# src/handlers/messages.py

import logging
import tempfile
from pathlib import Path
from uuid import UUID
from datetime import datetime

from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from beanie.operators import In

from src.bot import bot
from src.models.generation import Generation
from src.models.user import User
from src.models.app_config import AppConfig
from src.services.tapsage_storage import tapsage_upload
from src.services.tapsage_client import TapsageClient
from src.services.replicate_client import ReplicateClient
from src.texts import messages, buttons

logger = logging.getLogger("pp_bot.handlers.messages")


@bot.message_handler(content_types=["photo"])
async def handle_photo(message: Message):
    # ... (این تابع بدون تغییر است)
    chat_id = message.chat.id
    
    gen = Generation(
        chat_id=chat_id,
        photo_file_id=message.photo[-1].file_id,
        status="init",
        model_name="black-forest-labs/flux-kontext-pro"
    )
    await gen.insert()
    logger.info(f"[handle_photo] New generation created. uid={gen.uid}")

    markup = InlineKeyboardMarkup()
    callback_data = f"select_service_{gen.uid}_photoshoot"
    markup.add(InlineKeyboardButton(buttons.PRODUCT_PHOTOSHOOT, callback_data=callback_data))

    await bot.send_message(chat_id, messages.SELECT_SERVICE, reply_markup=markup)


@bot.message_handler(content_types=['text'])
async def handle_text_messages(message: Message):
    """
    Handles text messages based on the user's current conversation state.
    This function is now more robust and state-aware.
    """
    chat_id = message.chat.id
    
    # دکمه‌های منوی اصلی در commands.py زودتر پردازش می‌شوند
    # پس فقط متن‌های دیگر به اینجا می‌رسند.

    # Find the latest pending generation for the user across all waiting states
    gen = await Generation.find(
        Generation.chat_id == chat_id,
        In(Generation.status, [
            "awaiting_mode_selection",
            "awaiting_template_selection",
            "awaiting_description",
            "awaiting_product_name",
            "awaiting_confirmation"
        ])
    ).sort(-Generation.created_at).first_or_none()

    if not gen:
        # No active process, guide the user to start a new one
        await bot.send_message(chat_id, messages.UNEXPECTED_TEXT_PROMPT)
        return

    # --- State-aware logic ---
    if gen.status in ["awaiting_description", "awaiting_product_name"]:
        # These states expect text input, so we process it.
        logger.info(f"[handle_text] Received text for an active generation in state: {gen.status}")
        if gen.status == "awaiting_product_name":
            gen.product_name = message.text
            await show_confirmation_prompt(gen)
        elif gen.status == "awaiting_description":
            gen.description = message.text
            await show_confirmation_prompt(gen)
    else:
        # These states expect a button click, so we remind the user.
        # (awaiting_mode_selection, awaiting_template_selection, awaiting_confirmation)
        logger.warning(f"[handle_text] User sent text '{message.text}' while in state '{gen.status}', which expects a button click.")
        await bot.send_message(chat_id, messages.PROMPT_TO_USE_BUTTONS)


async def show_confirmation_prompt(gen: Generation):
    # ... (این تابع بدون تغییر است)
    gen.status = "awaiting_confirmation"
    gen.updated_at = datetime.utcnow()
    await gen.save()

    caption = ""
    if gen.generation_mode == "template":
        cfg = await AppConfig.find_one(AppConfig.type == "style_templates")
        template_name = "N/A"
        if cfg and cfg.style_templates:
            for t in cfg.style_templates:
                if t["id"] == gen.template_id:
                    template_name = t["name"]
                    break
        caption = messages.CONFIRMATION_PROMPT_TEMPLATE.format(template_name=template_name, product_name=gen.product_name)
    
    elif gen.generation_mode == "manual":
        caption = messages.CONFIRMATION_PROMPT_MANUAL.format(description=gen.description)

    elif gen.generation_mode == "automatic":
        caption = messages.CONFIRMATION_PROMPT_AUTOMATIC.format(description=gen.description)

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(buttons.ACCEPT, callback_data=f"confirm_{gen.uid}_accept"),
        InlineKeyboardButton(buttons.EDIT, callback_data=f"confirm_{gen.uid}_edit"),
        InlineKeyboardButton(buttons.CANCEL_NEW_REQUEST, callback_data=f"confirm_{gen.uid}_cancel")
    )

    await bot.send_photo(
        gen.chat_id,
        photo=gen.photo_file_id,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=markup
    )


async def process_generation_request(generation_id: UUID):
    # ... (این تابع بدون تغییر است)
    gen = await Generation.find_one(Generation.uid == generation_id)
    if not gen:
        return logger.error(f"[process_request] Could not find generation uid={generation_id}")

    chat_id = gen.chat_id
    gen.status = "inqueue"
    await gen.save()
    logger.info(f"[process_request] uid={gen.uid} status -> inqueue")

    user = await User.find_one(User.chat_id == chat_id)
    generation_cost = 1

    if not user or user.credits < generation_cost:
        gen.status = "error"
        gen.error = "Insufficient credits"
        await gen.save()
        return await bot.send_message(chat_id, messages.INSUFFICIENT_CREDITS.format(credits_balance=user.credits if user else 0))

    loading_message = None
    try:
        loading_message = await bot.send_message(chat_id, messages.PROCESSING_REQUEST)

        final_prompt = ""
        if gen.generation_mode == "template":
            cfg = await AppConfig.find_one(AppConfig.type == "style_templates")
            template_prompt = ""
            if cfg and cfg.style_templates:
                for t in cfg.style_templates:
                    if t["id"] == gen.template_id:
                        template_prompt = t["prompt"]
                        break
            final_prompt = template_prompt.format(product_name=gen.product_name)

        elif gen.generation_mode == "manual":
            final_prompt = gen.description

        elif gen.generation_mode == "automatic":
            file_info = await bot.get_file(gen.photo_file_id)
            file_bytes = await bot.download_file(file_info.file_path)
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)
                tmp_path.write_bytes(file_bytes)
            input_url = await tapsage_upload(tmp_path, file_name=tmp_path.name)
            gen.input_url = input_url
            tmp_path.unlink()
            
            tapsage = TapsageClient()
            session_id = await tapsage.create_session()
            if not session_id: raise Exception("Failed to create Tapsage session")
            
            final_prompt = await tapsage.generate_prompt(session_id=session_id, prompt=gen.description, image_url=input_url)
        
        gen.prompt = final_prompt
        logger.info(f"[process_request] Final prompt for uid={gen.uid}: {final_prompt}")
        
        if not gen.input_url:
            file_info = await bot.get_file(gen.photo_file_id)
            file_bytes = await bot.download_file(file_info.file_path)
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)
                tmp_path.write_bytes(file_bytes)
            input_url = await tapsage_upload(tmp_path, file_name=tmp_path.name)
            gen.input_url = input_url
            tmp_path.unlink()
        
        user.credits -= generation_cost
        await user.save()
        
        replicate = ReplicateClient()
        rep_id = await replicate.submit_generation(chat_id=chat_id, prompt=final_prompt, input_url=gen.input_url)
        
        gen.replicate_id = rep_id
        gen.status = "processing"
        gen.cost = generation_cost
        await gen.save()
        
        await bot.delete_message(chat_id, loading_message.message_id)
        await bot.send_message(chat_id, messages.REQUEST_IN_QUEUE.format(gen_uid=gen.uid), parse_mode="Markdown")

    except Exception as e:
        logger.exception(f"[process_request] Processing failed for uid={gen.uid}: {e}")
        if loading_message:
            await bot.delete_message(chat_id, loading_message.message_id)
        if user and gen.cost:
            user.credits += gen.cost
            await user.save()
            
        gen.status = "error"
        gen.error = str(e)
        await gen.save()
        await bot.send_message(chat_id, messages.IMAGE_GENERATION_SUBMISSION_ERROR)
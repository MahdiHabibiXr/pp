# src/handlers/messages.py

import logging
import tempfile
from pathlib import Path
from uuid import UUID
from datetime import datetime

from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from beanie.operators import In, And

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
    """
    Starts the generation flow by creating a Generation document.
    """
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
    UPDATED: Sanitizes user input for both quotes and newlines.
    """
    chat_id = message.chat.id
    
    # Handlers for main menu buttons in commands.py are checked first.
    if message.text.startswith('/'):
        return

    # Find the latest pending generation for the user
    gen = await Generation.find(
        Generation.chat_id == chat_id,
        In(Generation.status, [
            "awaiting_mode_selection", "awaiting_template_selection",
            "awaiting_description", "awaiting_product_name", "awaiting_confirmation"
        ])
    ).sort(-Generation.created_at).first_or_none()

    if not gen:
        await bot.send_message(chat_id, messages.UNEXPECTED_TEXT_PROMPT)
        return

    # Sanitize the input text by escaping double quotes and replacing newlines.
    sanitized_text = message.text.replace('"', '\\"').replace('\n', '\\n')

    # --- State-aware logic ---
    if gen.status in ["awaiting_description", "awaiting_product_name"]:
        logger.info(f"[handle_text] Received text for state: {gen.status}")
        if gen.status == "awaiting_product_name":
            gen.product_name = sanitized_text
            await show_confirmation_prompt(gen)
        elif gen.status == "awaiting_description":
            gen.description = sanitized_text
            await show_confirmation_prompt(gen)
    else:
        logger.warning(f"[handle_text] User sent text '{message.text}' while in state '{gen.status}', which expects a button click.")
        await bot.send_message(chat_id, messages.PROMPT_TO_USE_BUTTONS)


async def show_confirmation_prompt(gen: Generation):
    """
    UPDATED: Desanitizes text before showing it to the user for a clean display.
    """
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
        
        # Create a display-friendly version of the product name
        display_product_name = gen.product_name.replace('\\n', '\n').replace('\\"', '"')
        caption = messages.CONFIRMATION_PROMPT_TEMPLATE.format(
            template_name=template_name,
            product_name=display_product_name
        )
    
    elif gen.generation_mode in ["manual", "automatic"]:
        # Create a display-friendly version of the description
        display_description = gen.description.replace('\\n', '\n').replace('\\"', '"')
        caption = messages.CONFIRMATION_PROMPT_MANUAL.format(description=display_description)

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
    """
    Prepares all data (uploads image) and queues the request.
    """
    gen = await Generation.find_one(Generation.uid == generation_id)
    if not gen: return logger.error(f"Could not find generation uid={generation_id}")

    chat_id = gen.chat_id
    user = await User.find_one(User.chat_id == chat_id)

    # 1. Get cost
    costs_cfg = await AppConfig.find_one(AppConfig.type == "service_costs")
    cost = 1
    if costs_cfg and costs_cfg.service_costs:
        try: cost = costs_cfg.service_costs[gen.service][gen.generation_mode]
        except (TypeError, KeyError): logger.error(f"Could not determine cost for service={gen.service}, mode={gen.generation_mode}. Using fallback.")
    gen.cost = cost

    # 2. Check credits
    if not user or user.credits < gen.cost:
        gen.status = "error"; gen.error = "Insufficient credits"; await gen.save()
        return await bot.send_message(chat_id, messages.INSUFFICIENT_CREDITS.format(credits_balance=user.credits if user else 0))

    # 3. Check queue limit for unpaid users
    is_paid = user.paid
    if not is_paid:
        queued_item = await Generation.find_one(And(Generation.chat_id == chat_id, Generation.status == "inqueue"))
        if queued_item:
            gen.status = "cancelled"; gen.error = "Queue limit reached"; await gen.save()
            return await bot.send_message(chat_id, messages.QUEUE_LIMIT_REACHED)

    loading_message = None
    try:
        loading_message = await bot.send_message(chat_id, messages.PROCESSING_REQUEST)

        # 4. Upload the image to get the URL for the workflow
        file_info = await bot.get_file(gen.photo_file_id)
        file_bytes = await bot.download_file(file_info.file_path)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            tmp_path.write_bytes(file_bytes)
        input_url = await tapsage_upload(tmp_path, file_name=tmp_path.name)
        gen.input_url = str(input_url)
        tmp_path.unlink()
        
        # 5. Deduct credits and place the request in the queue
        user.credits -= gen.cost
        await user.save()

        gen.is_paid_user = is_paid
        gen.status = "inqueue"
        await gen.save()

        logger.info(f"uid={gen.uid} successfully placed in queue. is_paid={is_paid}, cost={gen.cost}")
        await bot.delete_message(chat_id, loading_message.message_id)
        await bot.send_message(chat_id, messages.REQUEST_QUEUED_SUCCESS)

    except Exception as e:
        logger.exception(f"Processing/Queueing failed for uid={gen.uid}: {e}")
        if loading_message: await bot.delete_message(chat_id, loading_message.message_id)
        
        if 'user' in locals() and user and gen.cost:
            user.credits += gen.cost
            await user.save()
            
        gen.status = "error"; gen.error = str(e); await gen.save()
        await bot.send_message(chat_id, messages.IMAGE_GENERATION_SUBMISSION_ERROR)
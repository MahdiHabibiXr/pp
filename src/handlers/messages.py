# src/handlers/messages.py

import logging
import tempfile
from pathlib import Path
from uuid import UUID
from datetime import datetime
import mimetypes 

from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from beanie.operators import In, And

from src.bot import bot
from src.models.generation import Generation
from src.models.user import User
from src.models.app_config import AppConfig
from src.services.tapsage_storage import tapsage_upload
from src.services.tapsage_client import TapsageClient
from src.services.replicate_client import ReplicateClient
from src.texts import messages, buttons, prompts
from src.services.openai_client import OpenAIClient

logger = logging.getLogger("pp_bot.handlers.messages")


@bot.message_handler(content_types=["photo"])
async def handle_photo(message: Message):
    """
    Starts the generation flow by creating a Generation document
    and asking the user to select a service.
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

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(buttons.PRODUCT_PHOTOSHOOT, callback_data=f"select_service_{gen.uid}_photoshoot"),
        # InlineKeyboardButton(buttons.MODELING_PHOTOSHOOT, callback_data=f"select_service_{gen.uid}_modeling")
    )

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

    # Sanitize the input text by escaping double quotes and replacing newlines for database storage.
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
    Shows the confirmation prompt.
    UPDATED: Truncates long descriptions in the caption to avoid Telegram API errors.
    """
    gen.status = "awaiting_confirmation"
    await gen.save()

    caption = ""
    if gen.service == "photoshoot":
        mode_text = ""
        if gen.generation_mode == "template": mode_text = "قالب آماده"
        elif gen.generation_mode == "manual": mode_text = "دستی"
        elif gen.generation_mode == "automatic": mode_text = "خودکار"

        description_text = ""
        if gen.generation_mode == "template":
            cfg = await AppConfig.find_one(AppConfig.type == "style_templates")
            template_name = "N/A"
            if cfg and cfg.style_templates:
                for t in cfg.style_templates:
                    if t["id"] == gen.template_id:
                        template_name = t["name"]; break

            display_product_name = gen.product_name.replace('\\n', '\n').replace('\\"', '"')
            description_text = f"قالب: {template_name}\nنام محصول: {display_product_name}"
        else:
            display_description = gen.description.replace('\\n', '\n').replace('\\"', '"')
            
            # --- START: NEW TRUNCATION LOGIC ---
            if len(display_description) > 200:
                description_text = display_description[:200] + "..."
            else:
                description_text = display_description
            # --- END: NEW TRUNCATION LOGIC ---

        caption = messages.CONFIRMATION_PROMPT_PHOTOSHOOT.format(mode=mode_text, description=description_text)
    
    elif gen.service == "modeling":
        # ... (this part remains unchanged)
        cfg = await AppConfig.find_one(AppConfig.type == "modeling_templates")
        template_name = "N/A"
        gender_text = "زن" if gen.model_gender == "female" else "مرد"
        templates_list = cfg.female_templates if gen.model_gender == "female" else cfg.male_templates
        
        if cfg and templates_list:
            for t in templates_list:
                if t["id"] == gen.template_id:
                    template_name = t["name"]; break
        
        caption = messages.CONFIRMATION_PROMPT_MODELING.format(
            gender=gender_text,
            template_name=template_name
        )

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
    OVERHAULED: Now generates prompts in-house using OpenAIClient before queueing.
    FIXED: Ensures image is uploaded and URL is obtained BEFORE calling OpenAI.
    """
    gen = await Generation.find_one(Generation.uid == generation_id)
    if not gen: return logger.error(f"Could not find generation uid={generation_id}")

    chat_id = gen.chat_id
    user = await User.find_one(User.chat_id == chat_id)

    # 1. Get cost
    costs_cfg = await AppConfig.find_one(AppConfig.type == "service_costs")
    cost = 1
    if costs_cfg and costs_cfg.service_costs:
        try:
            mode = gen.generation_mode or "template"
            cost = costs_cfg.service_costs[gen.service][mode]
        except (TypeError, KeyError):
            logger.error(f"Could not determine cost... Using fallback.")
    gen.cost = cost

    # 2. Check credits
    if not user or user.credits < gen.cost:
        gen.status = "error"; gen.error = "Insufficient credits"; await gen.save()
        return await bot.send_message(chat_id, messages.INSUFFICIENT_CREDITS.format(credits_balance=user.credits if user else 0))

    # 3. Check queue limit
    is_paid = user.paid
    if not is_paid:
        queued_item = await Generation.find_one(And(Generation.chat_id == chat_id, Generation.status == "inqueue"))
        if queued_item:
            gen.status = "cancelled"; gen.error = "Queue limit reached"; await gen.save()
            return await bot.send_message(chat_id, messages.QUEUE_LIMIT_REACHED)

    loading_message = None
    try:
        loading_message = await bot.send_message(chat_id, messages.PROCESSING_REQUEST)

        # 4. Download image bytes
        file_info = await bot.get_file(gen.photo_file_id)
        file_bytes = await bot.download_file(file_info.file_path)

        # --- CORRECTED LOGIC ---
        # 5. Upload image to storage FIRST to get the URL
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            tmp_path.write_bytes(file_bytes)
        input_url = await tapsage_upload(tmp_path, file_name=tmp_path.name)
        gen.input_url = str(input_url) # Save the URL to the generation object
        tmp_path.unlink()
        
        # 6. Now, generate the prompt using the obtained URL
        final_prompt = ""
        openai_client = OpenAIClient()
        
        if gen.service == "photoshoot":
            if gen.generation_mode == "template":
                cfg = await AppConfig.find_one(AppConfig.type == "style_templates")
                if cfg and cfg.style_templates:
                    for t in cfg.style_templates:
                        if t["id"] == gen.template_id:
                            final_prompt = t["prompt"].replace("{product_name}", "this product"); break
            
            elif gen.generation_mode == "manual":
                final_prompt = await openai_client.generate_prompt_from_text(gen.description)

            elif gen.generation_mode == "automatic":
                # Now we have a valid URL in gen.input_url
                final_prompt = await openai_client.generate_prompt_from_image_url(gen.description, str(gen.input_url))
        
        elif gen.service == "modeling":
            cfg = await AppConfig.find_one(AppConfig.type == "modeling_templates")
            templates = cfg.female_templates if gen.model_gender == "female" else cfg.male_templates
            if cfg and templates:
                for t in templates:
                    if t["id"] == gen.template_id:
                        final_prompt = t["prompt"]; break
        
        gen.prompt = final_prompt
        logger.info(f"Final prompt for uid={gen.uid}: {final_prompt}")
        # --- END OF CORRECTED LOGIC ---

        # 7. Deduct credits and queue
        user.credits -= gen.cost
        await user.save()
        gen.is_paid_user = is_paid
        gen.status = "inqueue"
        await gen.save()

        logger.info(f"uid={gen.uid} successfully placed in queue.")
        await bot.delete_message(chat_id, loading_message.message_id)
        await bot.send_message(chat_id, messages.REQUEST_QUEUED_SUCCESS)

    except Exception as e:
        logger.exception(f"Processing/Queueing failed for uid={gen.uid}: {e}")
        if loading_message: await bot.delete_message(chat_id, loading_message.message_id)
        if 'user' in locals() and user and gen.cost:
            user.credits += gen.cost; await user.save()
        gen.status = "error"; gen.error = str(e); await gen.save()
        await bot.send_message(chat_id, messages.IMAGE_GENERATION_SUBMISSION_ERROR)

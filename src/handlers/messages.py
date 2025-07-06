# src/handlers/messages.py

import logging
import tempfile
from pathlib import Path
from uuid import UUID
from datetime import datetime

from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from src.bot import bot
from src.models.generation import Generation
from src.models.user import User
from src.services.tapsage_storage import tapsage_upload
from src.services.tapsage_client import TapsageClient
from src.services.replicate_client import ReplicateClient
from src.texts import messages, buttons

logger = logging.getLogger("pp_bot.handlers.messages")


@bot.message_handler(content_types=["photo"])
async def handle_photo(message: Message):
    # ... (this function remains unchanged)
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
    # ... (this function remains unchanged)
    chat_id = message.chat.id
    
    if message.text.startswith('/'):
        return # Ignore commands

    gen = await Generation.find_one(
        Generation.chat_id == chat_id,
        Generation.status == "awaiting_description"
    )

    if gen:
        logger.info(f"[handle_text] Received description for uid={gen.uid}")
        gen.description = message.text
        gen.status = "awaiting_confirmation"
        gen.updated_at = datetime.utcnow()
        await gen.save()

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(buttons.ACCEPT, callback_data=f"confirm_{gen.uid}_accept"),
            InlineKeyboardButton(buttons.EDIT, callback_data=f"confirm_{gen.uid}_edit"),
            InlineKeyboardButton(buttons.CANCEL_NEW_REQUEST, callback_data=f"confirm_{gen.uid}_cancel")
        )

        await bot.send_photo(
            chat_id,
            photo=gen.photo_file_id,
            caption=messages.CONFIRMATION_PROMPT.format(description=gen.description),
            parse_mode="Markdown",
            reply_markup=markup
        )


async def process_generation_request(generation_id: UUID):
    """
    Processes the generation request after final user confirmation.
    UPDATED: Sends a temporary "processing" message.
    """
    gen = await Generation.find_one(Generation.uid == generation_id)
    if not gen:
        logger.error(f"[process_request] Could not find generation with uid={generation_id}")
        return

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
        await bot.send_message(chat_id, messages.INSUFFICIENT_CREDITS.format(credits_balance=user.credits if user else 0))
        return

    # --- UPDATED LOGIC: Send and manage a loading message ---
    loading_message = None
    try:
        # Send the "Processing..." message
        loading_message = await bot.send_message(chat_id, messages.PROCESSING_REQUEST)

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
            
        prompt_text = await tapsage.generate_prompt(session_id=session_id, prompt=gen.description, image_url=input_url)
        gen.prompt = prompt_text
        
        user.credits -= generation_cost
        await user.save()
        logger.info(f"[process_request] Deducted {generation_cost} credits from chat_id={chat_id}")
        
        replicate = ReplicateClient()
        rep_id = await replicate.submit_generation(chat_id=chat_id, prompt=prompt_text, input_url=input_url)
        gen.replicate_id = rep_id
        gen.status = "processing"
        gen.cost = generation_cost
        await gen.save()
        logger.info(f"[process_request] uid={gen.uid} status -> processing, replicate_id={rep_id}")

        # Delete the loading message and send the final confirmation
        await bot.delete_message(chat_id, loading_message.message_id)
        await bot.send_message(chat_id, messages.REQUEST_IN_QUEUE.format(gen_uid=gen.uid), parse_mode="Markdown")

    except Exception as e:
        logger.exception(f"[process_request] Processing failed for uid={gen.uid}: {e}")
        # Clean up loading message on error
        if loading_message:
            await bot.delete_message(chat_id, loading_message.message_id)

        # Refund credits if they were deducted
        if user and gen.cost:
            user.credits += gen.cost
            await user.save()
            
        gen.status = "error"
        gen.error = str(e)
        await gen.save()
        await bot.send_message(chat_id, messages.IMAGE_GENERATION_SUBMISSION_ERROR)
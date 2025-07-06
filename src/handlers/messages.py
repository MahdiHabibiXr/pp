# src/handlers/messages.py

import logging
from uuid import uuid4
from datetime import datetime
import tempfile
from pathlib import Path
from telebot.types import Message

from src.bot import bot
from src.models.generation import Generation
from src.models.user import User  # <-- Import the User model
from src.services.tapsage_storage import tapsage_upload
from src.services.tapsage_client import TapsageClient
from src.services.replicate_client import ReplicateClient

logger = logging.getLogger("pp_bot.handlers.messages")


@bot.message_handler(content_types=["photo"])
async def handle_photo(message: Message):
    """
    Handles the core image generation flow, including credit checks.
    """
    chat_id = message.chat.id
    caption = (message.caption or "").strip()
    if not caption:
        logger.warning(f"[handle_photo] Missing caption for chat_id={chat_id}")
        await bot.send_message(
            chat_id,
            "⚠️ Please send the image with a descriptive caption."
        )
        return

    # === ADDED: CREDIT CHECK LOGIC ===
    user = await User.find_one(User.chat_id == chat_id)
    generation_cost = 1  # Define your cost per generation. You could also load this from AppConfig.

    if not user or user.credits < generation_cost:
        credits_balance = user.credits if user else 0
        logger.warning(f"[handle_photo] Insufficient credits for chat_id={chat_id}. Balance: {credits_balance}")
        await bot.send_message(
            chat_id,
            f"⚠️ You do not have enough credits. Your balance is {credits_balance} credits.\nUse /buy to purchase more."
        )
        return
    # === END OF ADDED LOGIC ===

    # دانلود عکس
    try:
        file_info = await bot.get_file(message.photo[-1].file_id)
        logger.info(f"[handle_photo] Downloading file_id={file_info.file_id}")
        file_bytes = await bot.download_file(file_info.file_path)
        logger.info(f"[handle_photo] Downloaded {len(file_bytes)} bytes")
    except Exception:
        logger.exception(f"[handle_photo] Error downloading photo for chat_id={chat_id}")
        await bot.send_message(
            chat_id,
            "❌ Error downloading the image. Please try again."
        )
        return

    # ذخیره موقت و آپلود به Tapsage Storage
    tmp_path = Path(tempfile.gettempdir()) / f"{file_info.file_id}.jpg"
    tmp_path.write_bytes(file_bytes)
    logger.info(f"[handle_photo] Wrote temp file: {tmp_path}")

    try:
        input_url = await tapsage_upload(tmp_path, file_name=tmp_path.name)
        logger.info(f"[handle_photo] Uploaded to Tapsage: {input_url}")
    except Exception:
        logger.exception(f"[handle_photo] Tapsage upload failed for chat_id={chat_id}")
        await bot.send_message(
            chat_id,
            "❌ Error uploading the image. Please try again later."
        )
        tmp_path.unlink(missing_ok=True)
        return
    finally:
        tmp_path.unlink(missing_ok=True)
        logger.info(f"[handle_photo] Cleaned up temp file: {tmp_path}")

    # تولید prompt از Tapsage Chat
    tapsage = TapsageClient()
    session_id = await tapsage.create_session()
    logger.info(f"[handle_photo] Tapsage session_id={session_id!r}")
    if not session_id:
        await bot.send_message(
            chat_id,
            "❌ Error contacting the prompt generation service. Please try again later."
        )
        return

    try:
        prompt_text = await tapsage.generate_prompt(
            session_id=session_id,
            prompt=caption,
            image_url=input_url
        )
        logger.info(f"[handle_photo] Resolved prompt_text={prompt_text!r}")
    except Exception:
        logger.exception(f"[handle_photo] Prompt generation error for chat_id={chat_id}")
        await bot.send_message(
            chat_id,
            "❌ Error generating the image description. Please try again later."
        )
        return

    # === ADDED: DEDUCT CREDITS ===
    user.credits -= generation_cost
    await user.save()
    logger.info(f"[handle_photo] Deducted {generation_cost} credits from chat_id={chat_id}. New balance: {user.credits}")
    # === END OF ADDED LOGIC ===


    # درج رکورد Generation
    gen_uid = uuid4()
    gen = Generation(
        uid=gen_uid,
        chat_id=chat_id,
        description=caption,
        input_url=input_url,
        prompt=prompt_text,
        model_name="black-forest-labs/flux-kontext-pro",
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    await gen.insert()
    logger.info(f"[handle_photo] Saved Generation uid={gen_uid}")

    # ارسال به Replicate
    replicate = ReplicateClient()
    try:
        rep_id = await replicate.submit_generation(
            chat_id=chat_id,
            prompt=prompt_text,
            input_url=input_url
        )
        gen.replicate_id = rep_id
        gen.status = "processing"
        gen.updated_at = datetime.utcnow()
        await gen.save()
        logger.info(f"[handle_photo] Submitted to Replicate id={rep_id}")
    except Exception:
        logger.exception(f"[handle_photo] Replicate submission failed for uid={gen_uid}")
        # Note: Consider refunding the credit here if submission fails
        user.credits += generation_cost
        await user.save()
        await bot.send_message(
            chat_id,
            "❌ Error submitting the request to the image generation service. Your credits have been refunded."
        )
        return

    # اطلاع‌رسانی نهایی
    await bot.send_message(
        chat_id,
        f"✅ Your request has been received (ID: `{gen_uid}`). It is now being processed. You will receive the image as soon as it's ready.",
        parse_mode="Markdown"
    )
    logger.info(f"[handle_photo] Acknowledgement sent for uid={gen_uid}")
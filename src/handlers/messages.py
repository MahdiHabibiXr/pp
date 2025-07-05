# src/handlers/messages.py

import logging
from uuid import uuid4
from datetime import datetime
import tempfile
from pathlib import Path
from telebot.types import Message

from src.bot import bot
from src.models.generation import Generation
from src.services.tapsage_storage import tapsage_upload
from src.services.tapsage_client import TapsageClient
from src.services.replicate_client import ReplicateClient

logger = logging.getLogger("pp_bot.handlers.messages")


@bot.message_handler(content_types=["photo"])
async def handle_photo(message: Message):
    """
    یک‌جلوه ساده: عکس + کپشن.
    1) بررسی کپشن
    2) دانلود عکس
    3) آپلود به Tapsage Storage
    4) تولید prompt از Tapsage Chat
    5) درج Generation در MongoDB
    6) ارسال به Replicate
    7) اطلاع‌رسانی به کاربر
    """
    chat_id = message.chat.id
    caption = (message.caption or "").strip()
    if not caption:
        logger.warning(f"[handle_photo] Missing caption for chat_id={chat_id}")
        await bot.send_message(
            chat_id,
            "⚠️ لطفاً تصویر را همراه با توضیح (caption) ارسال کنید."
        )
        return

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
            "❌ خطا در دانلود تصویر. لطفاً دوباره تلاش کنید."
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
            "❌ خطا در بارگذاری تصویر. لطفاً بعداً امتحان کنید."
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
            "❌ خطا در برقراری ارتباط با سرویس تولید توضیح. لطفاً بعداً امتحان کنید."
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
            "❌ خطا در تولید توضیح تصویر. لطفاً بعداً امتحان کنید."
        )
        return

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
        await bot.send_message(
            chat_id,
            "❌ خطا در ارسال درخواست به سرویس تولید تصویر. لطفاً بعداً امتحان کنید."
        )
        return

    # اطلاع‌رسانی نهایی
    await bot.send_message(
        chat_id,
        f"✅ درخواست شما دریافت شد (ID: `{gen_uid}`). در حال پردازش است؛ به محض آماده شدن تصویر را دریافت خواهید کرد.",
        parse_mode="Markdown"
    )
    logger.info(f"[handle_photo] Acknowledgement sent for uid={gen_uid}")

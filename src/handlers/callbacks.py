# src/handlers/callbacks.py

import logging
from uuid import UUID
from datetime import datetime
from telebot.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from src.bot import bot
from src.models.app_config import AppConfig
from src.models.payment import Payment
from src.models.user import User
from src.models.generation import Generation
from src.services.zarinpal_client import ZarinpalClient
from src.texts import messages, buttons
# Import the processing function
from src.handlers.messages import process_generation_request


@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("select_service_"))
async def handle_service_selection(call: CallbackQuery):
    # ... (this function remains unchanged)
    chat_id = call.message.chat.id
    try:
        parts = call.data.split("_")
        generation_id = UUID(parts[2])
        service_name = parts[3]
    except (IndexError, ValueError):
        await bot.answer_callback_query(call.id, messages.GENERIC_ERROR)
        return

    logger = logging.getLogger("pp_bot.handlers.callbacks")
    logger.info(f"[handle_service_selection] User selected '{service_name}' for uid={generation_id}")

    gen = await Generation.find_one(Generation.uid == generation_id, Generation.chat_id == chat_id)
    if not gen or gen.status != "init":
        await bot.edit_message_text(messages.GENERATION_NOT_FOUND_FOR_USER, chat_id, call.message.message_id)
        return

    gen.service = service_name
    gen.status = "awaiting_description"
    gen.updated_at = datetime.utcnow()
    await gen.save()
    
    await bot.edit_message_text(messages.PROVIDE_DESCRIPTION, chat_id, call.message.message_id)


@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("confirm_"))
async def handle_confirmation(call: CallbackQuery):
    # ... (this function remains unchanged)
    chat_id = call.message.chat.id
    try:
        parts = call.data.split("_")
        generation_id = UUID(parts[1])
        action = parts[2]
    except (IndexError, ValueError):
        await bot.answer_callback_query(call.id, messages.GENERIC_ERROR)
        return

    logger = logging.getLogger("pp_bot.handlers.callbacks")
    logger.info(f"[handle_confirmation] User action '{action}' for uid={generation_id}")

    gen = await Generation.find_one(Generation.uid == generation_id, Generation.chat_id == chat_id)
    if not gen or gen.status != "awaiting_confirmation":
        await bot.edit_message_caption(caption=messages.GENERATION_NOT_FOUND_FOR_USER, chat_id=chat_id, message_id=call.message.message_id)
        return

    if action == "accept":
        await bot.edit_message_caption(caption=messages.REQUEST_ACCEPTED, chat_id=chat_id, message_id=call.message.message_id)
        await process_generation_request(generation_id)

    elif action == "edit":
        gen.status = "awaiting_description"
        await gen.save()
        await bot.edit_message_caption(caption=messages.EDIT_PROMPT, chat_id=chat_id, message_id=call.message.message_id)

    elif action == "cancel":
        gen.status = "cancelled"
        await gen.save()
        await bot.edit_message_caption(caption=messages.REQUEST_CANCELLED, chat_id=chat_id, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("buy_"))
async def process_purchase(call: CallbackQuery):
    """
    Handles package selection.
    UPDATED: Now deletes the /buy menu and sends a new message for payment.
    """
    chat_id = call.message.chat.id
    try:
        pkg_idx = int(call.data.split("_", 1)[1])
    except (ValueError, IndexError):
        await bot.answer_callback_query(call.id, messages.INVALID_CHOICE, show_alert=True)
        return

    # Delete the original message with the package list
    await bot.delete_message(chat_id, call.message.message_id)

    cfg = await AppConfig.find_one(AppConfig.type == "credit_packages")
    if not cfg or pkg_idx >= len(cfg.credit_packages):
        await bot.send_message(chat_id, messages.PACKAGE_NOT_FOUND)
        return

    label, price, coins, _ = cfg.credit_packages[pkg_idx]
    client = ZarinpalClient()
    result = await client.create_payment(
        chat_id=chat_id, amount=price, package_coins=coins, description=label
    )

    if not result.get("success"):
        err = result.get("error", "Unknown error")
        await bot.send_message(chat_id, messages.PAYMENT_CREATION_ERROR.format(err=err))
        return

    payment = Payment(
        uid=UUID(result["payment_uid"]),
        chat_id=chat_id, amount=price, status="initiated", package_coins=coins,
        payment_link=result["payment_link"], authority=result["authority"]
    )
    await payment.insert()

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(buttons.COMPLETE_PAYMENT, url=payment.payment_link))
    markup.add(InlineKeyboardButton(buttons.I_HAVE_PAID, callback_data=f"verify_{payment.uid}"))

    # Send a new message with the payment prompt
    await bot.send_message(
        chat_id,
        messages.PURCHASE_PROMPT.format(coins=coins, price=price),
        parse_mode="Markdown",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("verify_"))
async def verify_payment(call: CallbackQuery):
    """
    Handles payment verification.
    UPDATED: Now deletes the previous message and sends a new one with the result.
    """
    chat_id = call.message.chat.id
    try:
        pay_uid = UUID(call.data.split("_", 1)[1])
    except:
        await bot.delete_message(chat_id, call.message.message_id)
        await bot.send_message(chat_id, messages.INVALID_PAYMENT_ID)
        return

    # Delete the message with the "verify" button
    await bot.delete_message(chat_id, call.message.message_id)

    pay = await Payment.find_one(Payment.uid == pay_uid)
    if not pay:
        await bot.send_message(chat_id, messages.PAYMENT_RECORD_NOT_FOUND)
        return

    client = ZarinpalClient()
    verify_res = await client.verify_payment(pay.authority, pay.amount)
    status = verify_res.get("status")

    if verify_res.get("success") and status in (100, 101):
        is_newly_verified = pay.status != "completed" and status == 100
        pay.status = "completed"
        pay.transaction_id = verify_res.get("ref_id")
        pay.completed_at = datetime.utcnow()
        await pay.save()

        if is_newly_verified:
            user = await User.find_one(User.chat_id == chat_id)
            if user:
                user.credits += pay.package_coins
                user.paid = True
                await user.save()
            
            await bot.send_message(
                chat_id,
                messages.PAYMENT_VERIFIED_SUCCESS.format(package_coins=pay.package_coins),
                parse_mode="Markdown"
            )
        else: # Already verified
             await bot.send_message(
                chat_id,
                messages.PAYMENT_ALREADY_VERIFIED,
                parse_mode="Markdown"
            )
        return

    else:
        pay.status = "failed"
        await pay.save()
        error_message = messages.PAYMENT_VERIFICATION_GENERIC_ERROR.format(
            authority=pay.authority, chat_id=pay.chat_id
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(buttons.COMPLETE_PAYMENT, url=pay.payment_link))
        markup.add(InlineKeyboardButton(buttons.RETRY_VERIFICATION, callback_data=f"verify_{pay.uid}"))
        
        # Send a new message with the error and retry buttons
        await bot.send_message(
            chat_id,
            error_message,
            reply_markup=markup
        )
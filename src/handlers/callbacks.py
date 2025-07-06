# src/handlers/callbacks.py

from uuid import UUID
from datetime import datetime

from telebot.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from src.bot import bot
from src.models.app_config import AppConfig
from src.models.payment import Payment
from src.models.user import User
from src.services.zarinpal_client import ZarinpalClient
from src.texts import messages, buttons

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("buy_"))
async def process_purchase(call: CallbackQuery):
    chat_id = call.message.chat.id
    try:
        pkg_idx = int(call.data.split("_", 1)[1])
    except (ValueError, IndexError):
        return await bot.send_message(chat_id, messages.INVALID_CHOICE)

    cfg = await AppConfig.find_one(AppConfig.type == "credit_packages")
    if not cfg or pkg_idx >= len(cfg.credit_packages):
        return await bot.send_message(chat_id, messages.PACKAGE_NOT_FOUND)

    label, price, coins, _ = cfg.credit_packages[pkg_idx]
    client = ZarinpalClient()
    result = await client.create_payment(
        chat_id=chat_id,
        amount=price,
        package_coins=coins,
        description=label
    )

    if not result.get("success"):
        err = result.get("error", "Unknown error")
        status = result.get("status")
        if status is not None:
            err = f"{err} (code={status})"
        return await bot.send_message(chat_id, messages.PAYMENT_CREATION_ERROR.format(err=err))

    # Success
    payment_link = result["payment_link"]
    authority    = result["authority"]
    payment_uid  = result["payment_uid"]

    payment = Payment(
        uid=UUID(payment_uid),
        chat_id=chat_id,
        amount=price,
        status="initiated",
        package_coins=coins,
        payment_link=payment_link,
        authority=authority,
        transaction_id=None,
        created_at=datetime.utcnow()
    )
    await payment.insert()

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(buttons.COMPLETE_PAYMENT, url=payment_link))
    markup.add(InlineKeyboardButton(buttons.I_HAVE_PAID, callback_data=f"verify_{payment_uid}"))

    await bot.send_message(
        chat_id,
        messages.PURCHASE_PROMPT.format(coins=coins, price=price),
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("verify_"))
async def verify_payment(call: CallbackQuery):
    chat_id = call.message.chat.id
    try:
        pay_uid = UUID(call.data.split("_", 1)[1])
    except:
        return await bot.send_message(chat_id, messages.INVALID_PAYMENT_ID)

    pay = await Payment.find_one(Payment.uid == pay_uid)
    if not pay:
        return await bot.send_message(chat_id, messages.PAYMENT_RECORD_NOT_FOUND)

    client     = ZarinpalClient()
    verify_res = await client.verify_payment(pay.authority, pay.amount)
    status     = verify_res.get("status")

    if verify_res.get("success") and status == 100:
        pay.status       = "completed"
        pay.transaction_id = verify_res.get("ref_id")
        pay.completed_at = datetime.utcnow()
        await pay.save()

        user = await User.find_one(User.chat_id == chat_id)
        if user:
            user.credits    += pay.package_coins
            user.paid        = True
            user.updated_at  = datetime.utcnow()
            await user.save()

        return await bot.send_message(
            chat_id,
            messages.PAYMENT_VERIFIED_SUCCESS.format(pay=pay),
            parse_mode="Markdown"
        )

    if verify_res.get("success") and status == 101:
        return await bot.send_message(
            chat_id,
            messages.PAYMENT_ALREADY_VERIFIED,
            parse_mode="Markdown"
        )
    
    if status == -51:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(buttons.COMPLETE_PAYMENT, url=pay.payment_link))
        markup.add(InlineKeyboardButton(buttons.RETRY_VERIFICATION, callback_data=f"verify_{pay.uid}"))
        
        await bot.send_message(
            chat_id,
            messages.PAYMENT_NOT_CONFIRMED,
            reply_markup=markup
        )
        return

    err = verify_res.get("error", "Unknown error")
    if status is not None:
        err = f"{err} (code={status})"
    pay.status = "failed"
    await pay.save()
    return await bot.send_message(chat_id, messages.PAYMENT_VERIFICATION_FAILED.format(err=err))
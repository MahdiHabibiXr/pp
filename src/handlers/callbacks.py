from uuid import UUID
from datetime import datetime

from telebot.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from src.bot import bot
from src.models.app_config import AppConfig
from src.models.payment import Payment
from src.models.user import User
from src.services.zarinpal_client import ZarinpalClient

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("buy_"))
async def process_purchase(call: CallbackQuery):
    chat_id = call.message.chat.id
    try:
        pkg_idx = int(call.data.split("_", 1)[1])
    except (ValueError, IndexError):
        return await bot.send_message(chat_id, "Invalid selection.")

    cfg = await AppConfig.find_one(AppConfig.type == "credit_packages")
    if not cfg or pkg_idx >= len(cfg.credit_packages):
        return await bot.send_message(chat_id, "The selected package is not available.")

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
        return await bot.send_message(chat_id, f"❌ Error creating payment: {err}")

    # Success
    payment_link = result["payment_link"]
    authority    = result["authority"]
    payment_uid  = result["payment_uid"]

    payment = Payment(
        uid=UUID(payment_uid), # Ensure UID is UUID object for the DB
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
    markup.add(InlineKeyboardButton("🛒 Complete Payment", url=payment_link))
    markup.add(InlineKeyboardButton("✅ I have paid", callback_data=f"verify_{payment_uid}"))

    await bot.send_message(
        chat_id,
        f"To purchase **{coins}** credits for **{price:,}** Rial, please complete the payment:",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("verify_"))
async def verify_payment(call: CallbackQuery):
    chat_id = call.message.chat.id
    try:
        pay_uid = UUID(call.data.split("_", 1)[1])
    except:
        return await bot.send_message(chat_id, "Invalid payment ID.")

    pay = await Payment.find_one(Payment.uid == pay_uid)
    if not pay:
        return await bot.send_message(chat_id, "Payment record not found.")

    client     = ZarinpalClient()
    verify_res = await client.verify_payment(pay.authority, pay.amount)
    status     = verify_res.get("status")

    if verify_res.get("success") and status == 100:
        # Payment newly verified -> add credits
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
            f"🎉 Payment verified! **{pay.package_coins}** credits have been added.",
            parse_mode="Markdown"
        )

    if verify_res.get("success") and status == 101:
        # Payment already verified
        return await bot.send_message(
            chat_id,
            "ℹ️ This payment has already been verified.",
            parse_mode="Markdown"
        )
    
    # Handle the specific "session not active" error
    if status == -51:
        error_message = (
            "❌ Your payment has not been confirmed by the bank.\n\n"
            "If a deduction was made from your account, it will be returned within 72 hours.\n\n"
            "If you are sure about your payment, please try again in a few minutes or contact support."
        )
        markup = InlineKeyboardMarkup()
        # Add the "Complete Payment" button with the URL from the database
        markup.add(InlineKeyboardButton("🛒 Complete Payment", url=pay.payment_link))
        # Add the "Retry Verification" button
        markup.add(InlineKeyboardButton("🔄 Retry Verification", callback_data=f"verify_{pay.uid}"))
        
        await bot.send_message(
            chat_id,
            error_message,
            reply_markup=markup
        )
        return

    # Handle other errors
    err = verify_res.get("error", "Unknown error")
    if status is not None:
        err = f"{err} (code={status})"
    pay.status = "failed"
    await pay.save()
    return await bot.send_message(chat_id, f"❌ Payment verification failed: {err}")
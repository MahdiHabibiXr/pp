# src/handlers/callbacks.py

import logging
from uuid import UUID
from datetime import datetime
from telebot.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

from src.bot import bot
from src.models.app_config import AppConfig
from src.models.payment import Payment
from src.models.user import User
from src.models.generation import Generation
from src.services.zarinpal_client import ZarinpalClient
from src.texts import messages, buttons
from src.handlers.messages import process_generation_request, show_confirmation_prompt

logger = logging.getLogger("pp_bot.handlers.callbacks")

async def show_template_gallery(chat_id: int, gen_uid: UUID, page: int = 0, gender: str = None):
    """
    Displays a paginated gallery with a static caption.
    """
    PAGE_SIZE = 8
    
    if gender:
        cfg = await AppConfig.find_one(AppConfig.type == "modeling_templates")
        templates = cfg.female_templates if gender == 'female' else cfg.male_templates
    else:
        cfg = await AppConfig.find_one(AppConfig.type == "style_templates")
        templates = cfg.style_templates

    if not cfg or not templates:
        return await bot.send_message(chat_id, "متاسفانه در حال حاضر قالبی برای این بخش وجود ندارد.")

    start_index = page * PAGE_SIZE
    end_index = start_index + PAGE_SIZE
    paginated_templates = templates[start_index:end_index]

    if not paginated_templates:
        return await bot.send_message(chat_id, "قالب دیگری برای نمایش وجود ندارد.")

    media_group = []
    for template in paginated_templates:
        if template.get("sample_image_url"):
            media_group.append(InputMediaPhoto(
                media=template["sample_image_url"],
                # --- THIS LINE IS NOW UPDATED ---
                caption=messages.GALLERY_CAPTION if len(media_group) == 0 else ""
            ))
    
    markup = InlineKeyboardMarkup(row_width=2)
    template_buttons = [
        InlineKeyboardButton(f"«{t['name']}»", callback_data=f"select_template_{gen_uid}_{t['id']}")
        for t in paginated_templates
    ]
    markup.add(*template_buttons)

    pagination_buttons = []
    gender_payload = f"_{gender}" if gender else ""
    if page > 0:
        pagination_buttons.append(
            InlineKeyboardButton("⬅️ قبلی", callback_data=f"gallery_page_{gen_uid}_{page - 1}{gender_payload}")
        )
    if end_index < len(templates):
        pagination_buttons.append(
            InlineKeyboardButton("بعدی ➡️", callback_data=f"gallery_page_{gen_uid}_{page + 1}{gender_payload}")
        )
    if pagination_buttons:
        markup.add(*pagination_buttons)

    if media_group:
        await bot.send_media_group(chat_id, media=media_group)
    await bot.send_message(chat_id, messages.SELECT_TEMPLATE, reply_markup=markup)


@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("select_service_"))
async def handle_service_selection(call: CallbackQuery):
    """
    Handles the initial service selection (Product Photoshoot vs. Modeling).
    """
    chat_id = call.message.chat.id
    try:
        parts = call.data.split("_")
        gen_uid = UUID(parts[2])
        service = parts[3]
    except (IndexError, ValueError):
        return await bot.answer_callback_query(call.id, messages.GENERIC_ERROR, show_alert=True)

    gen = await Generation.find_one(Generation.uid == gen_uid, Generation.chat_id == chat_id)
    if not gen or gen.status != "init":
        return await bot.edit_message_text(messages.GENERATION_NOT_FOUND_FOR_USER, chat_id, call.message.message_id)

    gen.service = service
    await gen.save()

    if service == "photoshoot":
        gen.status = "awaiting_mode_selection"
        await gen.save()
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton(buttons.MODE_TEMPLATE, callback_data=f"select_mode_{gen_uid}_template"),
            InlineKeyboardButton(buttons.MODE_MANUAL, callback_data=f"select_mode_{gen_uid}_manual"),
            InlineKeyboardButton(buttons.MODE_AUTOMATIC, callback_data=f"select_mode_{gen_uid}_automatic")
        )
        await bot.edit_message_text(messages.SELECT_MODE, chat_id, call.message.message_id, reply_markup=markup)
    
    elif service == "modeling":
        gen.status = "awaiting_model_gender"
        await gen.save()
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton(buttons.MODEL_GENDER_FEMALE, callback_data=f"select_gender_{gen_uid}_female"),
            InlineKeyboardButton(buttons.MODEL_GENDER_MALE, callback_data=f"select_gender_{gen_uid}_male")
        )
        await bot.edit_message_text(messages.SELECT_MODEL_GENDER, chat_id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("select_gender_"))
async def handle_gender_selection(call: CallbackQuery):
    """
    Handles model gender selection and shows the modeling template gallery.
    """
    chat_id = call.message.chat.id
    try:
        parts = call.data.split("_")
        gen_uid = UUID(parts[2])
        gender = parts[3]
    except (IndexError, ValueError):
        return await bot.answer_callback_query(call.id, messages.GENERIC_ERROR, show_alert=True)

    gen = await Generation.find_one(Generation.uid == gen_uid, Generation.chat_id == chat_id)
    if not gen or gen.status != "awaiting_model_gender":
        return await bot.edit_message_text(messages.GENERATION_NOT_FOUND_FOR_USER, chat_id, call.message.message_id)
    
    gen.model_gender = gender
    gen.status = "awaiting_template_selection"
    await gen.save()
    
    await bot.delete_message(chat_id, call.message.message_id)
    await show_template_gallery(chat_id, gen_uid, page=0, gender=gender)

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("select_mode_"))
async def handle_mode_selection(call: CallbackQuery):
    """
    UPDATED: Deletes the mode selection message before showing the gallery.
    """
    chat_id = call.message.chat.id
    try:
        parts = call.data.split("_")
        gen_uid = UUID(parts[2])
        mode = parts[3]
    except (IndexError, ValueError):
        return await bot.answer_callback_query(call.id, messages.GENERIC_ERROR, show_alert=True)

    gen = await Generation.find_one(Generation.uid == gen_uid, Generation.chat_id == chat_id)
    if not gen or gen.status != "awaiting_mode_selection":
        return await bot.edit_message_text(messages.GENERATION_NOT_FOUND_FOR_USER, chat_id, call.message.message_id)
    
    gen.generation_mode = mode
    
    await bot.delete_message(chat_id, call.message.message_id)

    if mode == "template":
        gen.status = "awaiting_template_selection"
        await gen.save()
        await show_template_gallery(chat_id, gen_uid, page=0)

    elif mode == "manual":
        gen.status = "awaiting_description"
        await gen.save()
        await bot.send_message(chat_id, messages.PROVIDE_FULL_DESCRIPTION)

    elif mode == "automatic":
        gen.status = "awaiting_description"
        await gen.save()
        await bot.send_message(chat_id, messages.PROVIDE_SIMPLE_CAPTION)


@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("gallery_page_"))
async def handle_gallery_pagination(call: CallbackQuery):
    """
    Handles next/previous page buttons for both gallery types.
    """
    chat_id = call.message.chat.id
    try:
        parts = call.data.split("_")
        gen_uid = UUID(parts[2])
        page = int(parts[3])
        # Gender might be empty, so handle it carefully
        gender = parts[4] if len(parts) > 4 and parts[4] else None
    except (IndexError, ValueError):
        return await bot.answer_callback_query(call.id, messages.GENERIC_ERROR, show_alert=True)
    
    await bot.delete_message(chat_id, call.message.message_id)
    # await bot.delete_message(chat_id, call.message.message_id-1)
    await show_template_gallery(chat_id, gen_uid, page, gender=gender)


@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("select_template_"))
async def handle_template_selection(call: CallbackQuery):
    """
    Handles final template selection for both services.
    """
    chat_id = call.message.chat.id
    try:
        parts = call.data.split("_", 3)
        gen_uid = UUID(parts[2])
        template_id = parts[3]
    except (IndexError, ValueError):
        return await bot.answer_callback_query(call.id, messages.GENERIC_ERROR, show_alert=True)

    gen = await Generation.find_one(Generation.uid == gen_uid, Generation.chat_id == chat_id)
    if not gen or gen.status != "awaiting_template_selection":
        await bot.delete_message(chat_id, call.message.message_id)
        # await bot.delete_message(chat_id, call.message.message_id-1)

        return await bot.send_message(chat_id, messages.GENERATION_NOT_FOUND_FOR_USER)
        
    gen.template_id = template_id
    await gen.save()
    
    await bot.delete_message(chat_id, call.message.message_id)
    # await bot.delete_message(chat_id, call.message.message_id-1)

    
    # For modeling, go directly to confirmation. For photoshoot, ask for product name.
    if gen.service == "modeling":
        await show_confirmation_prompt(gen)
    else: # photoshoot
        gen.status = "awaiting_product_name"
        await gen.save()
        await bot.send_message(chat_id, messages.PROVIDE_PRODUCT_NAME)

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("confirm_"))
async def handle_confirmation(call: CallbackQuery):
    # ... (بدون تغییر)
    chat_id = call.message.chat.id
    try:
        parts = call.data.split("_")
        gen_uid = UUID(parts[1])
        action = parts[2]
    except (IndexError, ValueError):
        return await bot.answer_callback_query(call.id, messages.GENERIC_ERROR, show_alert=True)

    gen = await Generation.find_one(Generation.uid == gen_uid, Generation.chat_id == chat_id)
    if not gen or gen.status != "awaiting_confirmation":
        return await bot.edit_message_caption(caption=messages.GENERATION_NOT_FOUND_FOR_USER, chat_id=chat_id, message_id=call.message.message_id)

    if action == "accept":
        await bot.edit_message_caption(caption=messages.REQUEST_ACCEPTED, chat_id=chat_id, message_id=call.message.message_id)
        await process_generation_request(gen_uid)

    elif action == "edit":
        if gen.generation_mode == "template":
            gen.status = "awaiting_product_name"
            prompt_text = messages.EDIT_PROMPT_PRODUCT_NAME
        else:
            gen.status = "awaiting_description"
            prompt_text = messages.EDIT_PROMPT_DESCRIPTION
        
        await gen.save()
        await bot.edit_message_caption(caption=prompt_text, chat_id=chat_id, message_id=call.message.message_id)

    elif action == "cancel":
        gen.status = "cancelled"
        await gen.save()
        await bot.edit_message_caption(caption=messages.REQUEST_CANCELLED, chat_id=chat_id, message_id=call.message.message_id)


# --- Payment Handlers ---
@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("buy_"))
async def process_purchase(call: CallbackQuery):
    # ... (بدون تغییر)
    chat_id = call.message.chat.id
    try:
        pkg_idx = int(call.data.split("_", 1)[1])
    except (ValueError, IndexError):
        await bot.answer_callback_query(call.id, messages.INVALID_CHOICE, show_alert=True)
        return

    await bot.delete_message(chat_id, call.message.message_id)

    cfg = await AppConfig.find_one(AppConfig.type == "credit_packages")
    if not cfg or not cfg.credit_packages:
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

    await bot.send_message(
        chat_id,
        messages.PURCHASE_PROMPT.format(coins=f"{coins:,}", price=f"{price:,}"),
        parse_mode="Markdown",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("verify_"))
async def verify_payment(call: CallbackQuery):
    # ... (بدون تغییر)
    chat_id = call.message.chat.id
    try:
        pay_uid = UUID(call.data.split("_", 1)[1])
    except:
        await bot.delete_message(chat_id, call.message.message_id)
        await bot.send_message(chat_id, messages.INVALID_PAYMENT_ID)
        return

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
        pay.transaction_id = str(verify_res.get("ref_id"))
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
                messages.PAYMENT_VERIFIED_SUCCESS.format(package_coins=f"{pay.package_coins:,}"),
                parse_mode="Markdown"
            )
        else:
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
        
        await bot.send_message(
            chat_id,
            error_message,
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("resend_"))
async def handle_resend_image(call: CallbackQuery):
    """
    Handles the 'Resend' button from the project history, sending the final image again.
    """
    try:
        gen_uid = UUID(call.data.split("_")[1])
    except (IndexError, ValueError):
        return await bot.answer_callback_query(call.id, messages.GENERIC_ERROR, show_alert=True)

    gen = await Generation.find_one(Generation.uid == gen_uid)

    if gen and gen.status == "done" and gen.result_url:
        await bot.answer_callback_query(call.id, text="در حال ارسال مجدد تصویر...")
        await bot.send_photo(call.message.chat.id, photo=gen.result_url, caption=f"تصویر پروژه: {gen.description or gen.product_name}")
    else:
        await bot.answer_callback_query(call.id, text="متاسفانه تصویر این پروژه یافت نشد.", show_alert=True)


@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("cancel_"))
async def handle_cancel_request(call: CallbackQuery):
    """
    Handles the 'Cancel Request' button from the project history.
    """
    chat_id = call.message.chat.id
    try:
        gen_uid = UUID(call.data.split("_")[1])
    except (IndexError, ValueError):
        return await bot.answer_callback_query(call.id, messages.GENERIC_ERROR, show_alert=True)

    gen = await Generation.find_one(Generation.uid == gen_uid, Generation.chat_id == chat_id)

    if not gen:
        return await bot.answer_callback_query(call.id, "پروژه یافت نشد.", show_alert=True)

    if gen.status == "inqueue":
        gen.status = "cancelled"
        await gen.save()
        
        # Refund credits
        user = await User.find_one(User.chat_id == chat_id)
        if user and gen.cost:
            user.credits += gen.cost
            await user.save()
        
        await bot.edit_message_text(messages.REQUEST_CANCELLED_SUCCESS, chat_id, call.message.message_id)
    else:
        await bot.answer_callback_query(call.id, messages.REQUEST_ALREADY_PROCESSED, show_alert=True)
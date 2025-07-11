# src/handlers/commands.py

import logging
from datetime import datetime
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton

from src.bot import bot
from src.models.user import User
from src.models.generation import Generation
from src.models.app_config import AppConfig
from src.texts import messages, buttons
from src.config import settings

logger = logging.getLogger("pp_bot.handlers.commands")


def create_main_keyboard():
    """
    Creates the main reply keyboard with all primary options.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton(buttons.MAIN_KEYBOARD_NEW),
        KeyboardButton(buttons.MAIN_KEYBOARD_BALANCE),
        KeyboardButton(buttons.MAIN_KEYBOARD_PROJECTS),
        KeyboardButton(buttons.MAIN_KEYBOARD_INVITE),
        KeyboardButton(buttons.MAIN_KEYBOARD_BUY),
        KeyboardButton(buttons.MAIN_KEYBOARD_HELP)
    )
    return markup


@bot.message_handler(commands=["start"])
async def start_cmd(message: Message):
    """
    Handles /start, registers new users, processes referrals,
    and shows a personalized welcome message.
    """
    chat_id = message.chat.id
    referrer_id = None
    welcome_message = messages.START

    try:
        payload = message.text.split(" ")[1]
        if payload.isdigit():
            referrer_id = int(payload)
            if referrer_id == chat_id:
                referrer_id = None
    except IndexError:
        pass

    user = await User.find_one(User.chat_id == chat_id)
    if not user:
        new_user = User(
            chat_id=chat_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            referred_by=referrer_id
        )
        await new_user.insert()
        logger.info(f"[start_cmd] New user registered: chat_id={chat_id}, referred_by={referrer_id}")

        # Send welcome message and gift notification
        await bot.send_message(chat_id, welcome_message, reply_markup=create_main_keyboard())
        await bot.send_message(chat_id, messages.NEW_USER_GIFT)

        if referrer_id:
            referrer = await User.find_one(User.chat_id == referrer_id)
            if referrer:
                reward = settings.REFERRAL_REWARD_COINS
                referrer.credits += reward
                referrer.refs.append(chat_id)
                await referrer.save()
                logger.info(f"[start_cmd] Gave {reward} credits to referrer: chat_id={referrer_id}")
                try:
                    await bot.send_message(
                        referrer_id,
                        messages.REFERRAL_SUCCESS_NOTIFICATION.format(reward_amount=reward)
                    )
                except Exception as e:
                    logger.error(f"Could not notify referrer {referrer_id}: {e}")
    else:
        # It's a returning user
        user.updated_at = datetime.utcnow()
        await user.save()
        logger.info(f"[start_cmd] Returning user updated: chat_id={chat_id}")
        welcome_message = messages.START_RETURN_USER
        await bot.send_message(chat_id, welcome_message, reply_markup=create_main_keyboard())


@bot.message_handler(commands=["cancel"])
async def cancel_cmd(message: Message):
    """
    Handles the /cancel command, guiding the user to their project history.
    """
    await bot.send_message(message.chat.id, "برای لغو یک درخواست، لطفا به بخش «پروژه‌های من» رفته و از دکمه لغو در کنار پروژه مورد نظر استفاده کنید.")


@bot.message_handler(commands=["myprojects"])
async def my_projects_cmd(message: Message):
    """
    Handles the /myprojects command and shows the last 5 generations for the user.
    """
    chat_id = message.chat.id
    
    user_generations = await Generation.find(
        Generation.chat_id == chat_id
    ).sort(-Generation.created_at).limit(5).to_list()

    if not user_generations:
        await bot.send_message(chat_id, messages.NO_PROJECTS_FOUND)
        return

    await bot.send_message(chat_id, messages.MY_PROJECTS_HEADER)

    status_map = {
        "done": "✅ انجام شده",
        "processing": "⏳ در حال پردازش",
        "inqueue": "... در صف",
        "error": "❌ خطا",
        "cancelled": "⭕️ لغو شده"
    }

    for gen in user_generations:
        status_icon = status_map.get(gen.status, "❓ وضعیت نامشخص")
        description = gen.product_name or gen.description or "پروژه بدون عنوان"
        if len(description) > 30:
            description = description[:30] + "..."
        local_time = gen.created_at.strftime("%Y-%m-%d %H:%M")
        text = messages.PROJECT_STATUS_FORMAT.format(
            status_icon=status_icon,
            description=description,
            date=local_time
        )
        
        markup = InlineKeyboardMarkup()
        if gen.status == "done" and gen.result_url:
            markup.add(InlineKeyboardButton(buttons.RESEND_IMAGE, callback_data=f"resend_{gen.uid}"))
        if gen.status == "inqueue":
            markup.add(InlineKeyboardButton(buttons.CANCEL_REQUEST, callback_data=f"cancel_{gen.uid}"))

        await bot.send_message(chat_id, text, reply_markup=markup if markup.keyboard else None, parse_mode="Markdown")


@bot.message_handler(commands=["invite"])
async def invite_cmd(message: Message):
    """
    Handles the /invite command and shows the user's referral link.
    """
    chat_id = message.chat.id
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    
    invite_link = f"https://t.me/{bot_username}?start={chat_id}"
    reward = settings.REFERRAL_REWARD_COINS
    
    await bot.send_message(
        chat_id,
        messages.INVITE_FRIENDS.format(reward_amount=reward, invite_link=invite_link),
        parse_mode="Markdown"
    )


@bot.message_handler(commands=["generate"])
async def generate_cmd(message: Message):
    await bot.send_message(message.chat.id, messages.GENERATE_PROMPT)


@bot.message_handler(commands=["balance", "credits"])
async def balance_cmd(message: Message):
    chat_id = message.chat.id
    user = await User.find_one(User.chat_id == chat_id)
    credits = user.credits if user else 0
    await bot.send_message(chat_id, messages.BALANCE_CHECK.format(credits=credits))


@bot.message_handler(commands=["buy"])
async def buy_cmd(message: Message):
    chat_id = message.chat.id
    cfg_packages = await AppConfig.find_one(AppConfig.type == "credit_packages")
    markup = InlineKeyboardMarkup(row_width=1)
    text = messages.NO_PACKAGES

    if cfg_packages and cfg_packages.credit_packages:
        for label, price, coins, idx in cfg_packages.credit_packages:
            markup.add(InlineKeyboardButton(label, callback_data=f"buy_{idx}"))
        if markup.keyboard:
            cfg_shop = await AppConfig.find_one(AppConfig.type == "shop_messages")
            text = cfg_shop.shop_menu_message if cfg_shop and cfg_shop.shop_menu_message else "بسته‌های اعتبار موجود:"

    await bot.send_message(chat_id, text, reply_markup=markup)


@bot.message_handler(commands=["help"])
async def help_cmd(message: Message):
    await bot.send_message(message.chat.id, messages.HELP)


@bot.message_handler(commands=["menu"])
async def menu_cmd(message: Message):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(buttons.MENU_GENERATE, callback_data="menu_generate"),
        InlineKeyboardButton(buttons.MENU_BALANCE, callback_data="menu_balance"),
        InlineKeyboardButton(buttons.MENU_BUY, callback_data="menu_buy"),
        InlineKeyboardButton(buttons.MENU_INVITE, callback_data="menu_invite"),
        InlineKeyboardButton(buttons.MENU_HELP, callback_data="menu_help")
    )
    await bot.send_message(message.chat.id, messages.MENU_PROMPT, reply_markup=markup)


# --- Handlers for Main Keyboard Buttons ---

@bot.message_handler(func=lambda message: message.text == buttons.MAIN_KEYBOARD_NEW)
async def handle_new_project_button(message: Message):
    await generate_cmd(message)

@bot.message_handler(func=lambda message: message.text == buttons.MAIN_KEYBOARD_PROJECTS)
async def handle_my_projects_button(message: Message):
    await my_projects_cmd(message)

@bot.message_handler(func=lambda message: message.text == buttons.MAIN_KEYBOARD_INVITE)
async def handle_invite_button(message: Message):
    await invite_cmd(message)

@bot.message_handler(func=lambda message: message.text == buttons.MAIN_KEYBOARD_BALANCE)
async def handle_balance_button(message: Message):
    await balance_cmd(message)

@bot.message_handler(func=lambda message: message.text == buttons.MAIN_KEYBOARD_BUY)
async def handle_buy_button(message: Message):
    await buy_cmd(message)

@bot.message_handler(func=lambda message: message.text == buttons.MAIN_KEYBOARD_HELP)
async def handle_help_button(message: Message):
    await help_cmd(message)


# --- Callback handlers for the inline /menu buttons ---

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("menu_"))
async def handle_menu_callbacks(call: CallbackQuery):
    action = call.data.split("_")[1]
    await bot.answer_callback_query(call.id)
    
    message_for_action = call.message
    message_for_action.text = f"/{action}"

    if action == "generate": await generate_cmd(message_for_action)
    elif action == "balance": await balance_cmd(message_for_action)
    elif action == "buy": await buy_cmd(message_for_action)
    elif action == "help": await help_cmd(message_for_action)
    elif action == "invite": await invite_cmd(message_for_action)
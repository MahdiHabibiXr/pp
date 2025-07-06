# src/handlers/commands.py

import logging
from datetime import datetime
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from src.bot import bot
from src.models.user import User
from src.models.app_config import AppConfig
from src.texts import messages

logger = logging.getLogger("pp_bot.handlers.commands")


@bot.message_handler(commands=["start"])
async def start_cmd(message: Message):
    """
    Handler for /start – ثبت‌نام یا به‌روزرسانی کاربر و نمایش پیام خوش‌آمدگویی
    """
    chat_id = message.chat.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    user = await User.find_one(User.chat_id == chat_id)
    if not user:
        user = User(
            chat_id=chat_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        await user.insert()
        logger.info(f"[start_cmd] New user registered: chat_id={chat_id}")
    else:
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.updated_at = datetime.utcnow()
        await user.save()
        logger.info(f"[start_cmd] Existing user updated: chat_id={chat_id}")

    await bot.send_message(
        chat_id,
        messages.WELCOME
    )


@bot.message_handler(commands=["balance"])
async def balance_cmd(message: Message):
    """
    Handler for /balance – نمایش اعتبار فعلی کاربر
    """
    chat_id = message.chat.id
    user = await User.find_one(User.chat_id == chat_id)
    credits = user.credits if user else 0

    await bot.send_message(chat_id, messages.BALANCE_CHECK.format(credits=credits))
    logger.info(f"[balance_cmd] chat_id={chat_id} credits={credits}")


@bot.message_handler(commands=["buy"])
async def buy_cmd(message: Message):
    """
    Handler for /buy – نمایش منوی بسته‌های اعتباری
    """
    chat_id = message.chat.id

    cfg_shop = await AppConfig.find_one(AppConfig.type == "shop_messages")
    cfg_packages = await AppConfig.find_one(AppConfig.type == "credit_packages")

    text = (
        cfg_shop.shop_menu_message
        if cfg_shop and cfg_shop.shop_menu_message
        else messages.NO_PACKAGES
    )

    markup = InlineKeyboardMarkup()
    if cfg_packages and cfg_packages.credit_packages:
        for label, price, coins, idx in cfg_packages.credit_packages:
            markup.add(InlineKeyboardButton(label, callback_data=f"buy_{idx}"))

    await bot.send_message(chat_id, text, reply_markup=markup)
    logger.info(f"[buy_cmd] chat_id={chat_id} displayed shop menu")


@bot.message_handler(commands=["menu"])
async def menu_cmd(message: Message):
    """
    Handler for /menu – معادل /buy برای نمایش منوی بسته‌ها
    """
    logger.info(f"[menu_cmd] chat_id={message.chat.id}")
    await buy_cmd(message)
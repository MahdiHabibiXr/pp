from telebot.async_telebot import AsyncTeleBot
from src.config import settings

# Instantiate the asynchronous Telegram bot
bot = AsyncTeleBot(settings.BOT_TOKEN)

# Register handler modules to attach their callbacks to the bot instance
import src.handlers.commands  # noqa: F401
import src.handlers.messages  # noqa: F401
import src.handlers.callbacks  # noqa: F401

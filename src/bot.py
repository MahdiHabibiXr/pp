# src/bot.py

from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from src.config import settings

bot = AsyncTeleBot(settings.BOT_TOKEN, state_storage=StateMemoryStorage())

# Register handler modules
import src.handlers.commands
import src.handlers.messages
import src.handlers.callbacks
# import src.handlers.admin 
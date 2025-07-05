import asyncio
from src.config import settings
from src.database import init_db
from src.bot import bot

async def main():
    # Initialize MongoDB and Beanie
    await init_db()
    # Start Telegram polling
    await bot.infinity_polling()

if __name__ == "__main__":
    asyncio.run(main())

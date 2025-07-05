import motor.motor_asyncio
from beanie import init_beanie
from src.config import settings
from src.models.user import User
from src.models.generation import Generation
from src.models.payment import Payment
from src.models.app_config import AppConfig

async def init_db():
    """
    Establish MongoDB connection and initialize document models.
    """
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URI)
    db = client.get_default_database()
    await init_beanie(database=db, document_models=[User, Generation, Payment, AppConfig])

from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    BOT_TOKEN: str = Field(..., env="BOT_TOKEN")
    MONGO_URI: str = Field(..., env="MONGO_URI")
    TAPSAGE_API_KEY: str = Field(..., env="TAPSAGE_API_KEY")
    TAPSAGE_BOT_ID: str = Field(..., env="TAPSAGE_BOT_ID")
    REPLICATE_API_TOKEN: str = Field(..., env="REPLICATE_API_TOKEN")
    REPLICATE_CALLBACK_URL: str = Field(..., env="REPLICATE_CALLBACK_URL")
    ZARINPAL_MERCHANT_ID: str = Field(..., env="ZARINPAL_MERCHANT_ID")
    ZARINPAL_CALLBACK_URL: str = Field(..., env="ZARINPAL_CALLBACK_URL")
    ZARINPAL_REQUEST_URL: str = Field(..., env="ZARINPAL_REQUEST_URL")
    ZARINPAL_VERIFY_URL: str = Field(..., env="ZARINPAL_VERIFY_URL")
    ZARINPAL_PAYMENT_BASE: str = Field(..., env="ZARINPAL_PAYMENT_BASE")
    PIXY_API_KEY: str = Field(..., env="PIXY_API_KEY")
    LOGFIRE_TOKEN: str = Field(..., env="LOGFIRE_TOKEN")
    ZARINPAL_MERCHANT_MOBILE: str = Field(..., env="ZARINPAL_MERCHANT_MOBILE")
    ZARINPAL_MERCHANT_EMAIL: str = Field(..., env="ZARINPAL_MERCHANT_EMAIL")
    REFERRAL_REWARD_COINS: int = Field(default=1, env="REFERRAL_REWARD_COINS")
    NEW_USER_GIFT_COINS: int = Field(default=1, env="NEW_USER_GIFT_COINS")
    MANDATORY_CHANNEL_ID: str = Field(default="@PhotosazAI", env="MANDATORY_CHANNEL_ID")
    ADMIN_CHAT_IDS: list[int] = Field(default=[791927771], env="ADMIN_CHAT_IDS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = 'ignore'  

settings = Settings()
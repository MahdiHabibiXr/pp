# src/models/user.py

from beanie import Document
from pydantic import Field
from datetime import datetime
from uuid import UUID, uuid4  # <-- 'uuid4' is now imported here
from typing import List, Optional

class User(Document):
    """
    Represents a Telegram user with full profile and credit data.
    """
    uid: UUID = Field(default_factory=uuid4)
    chat_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str] = ""
    credits: int = 10
    paid: bool = False
    
    referred_by: Optional[int] = None
    refs: List[int] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
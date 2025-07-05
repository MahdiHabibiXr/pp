from beanie import Document
from pydantic import Field, HttpUrl
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional

class Generation(Document):
    """
    Represents an image generation request and its lifecycle.
    """
    uid: UUID = Field(default_factory=uuid4)
    chat_id: int
    description: Optional[str] = None
    input_url: Optional[HttpUrl] = None
    prompt: str
    model_name: str
    replicate_id: Optional[str] = None
    status: str             # pending, processing, completed, failed
    error: Optional[str] = None
    cost: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)  # ← new field
    completed_at: Optional[datetime] = None

    class Settings:
        name = "generations"

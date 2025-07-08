# src/models/generation.py

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
    photo_file_id: str
    
    # --- New fields for the new flow ---
    generation_mode: Optional[str] = None # template, manual, automatic
    template_id: Optional[str] = None
    product_name: Optional[str] = None
    # ---

    service: Optional[str] = None
    description: Optional[str] = None
    input_url: Optional[HttpUrl] = None
    prompt: Optional[str] = None
    model_name: str
    replicate_id: Optional[str] = None
    
    # --- Updated statuses ---
    status: str # init, awaiting_mode_selection, awaiting_template_selection, awaiting_product_name, awaiting_description, awaiting_confirmation, inqueue, processing, done, error, cancelled
    
    result_url: Optional[HttpUrl] = None
    error: Optional[str] = None
    cost: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Settings:
        name = "generations"
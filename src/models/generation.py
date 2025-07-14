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
    
    # --- Fields for Core Logic & Queueing ---
    is_paid_user: bool = False
    service: Optional[str] = None # 'photoshoot' or 'modeling'
    generation_mode: Optional[str] = None # template, manual, automatic
    
    # --- Fields for Modeling Service ---
    model_gender: Optional[str] = None # 'male' or 'female'
    
    # --- Fields for Template/Manual/Auto Modes ---
    template_id: Optional[str] = None
    product_name: Optional[str] = None
    description: Optional[str] = None
    
    # --- Fields for Advanced Settings ---
    lighting_style: Optional[str] = None
    color_theme: Optional[str] = None

    # --- Fields for Processing & Result ---
    input_url: Optional[HttpUrl] = None
    prompt: Optional[str] = None
    model_name: str
    replicate_id: Optional[str] = None
    
    status: str # init, awaiting_mode_selection, awaiting_template_selection, etc.
    
    result_url: Optional[HttpUrl] = None
    error: Optional[str] = None
    cost: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Settings:
        name = "generations"
# src/models/payment.py

from beanie import Document
from pydantic import Field
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional

class Payment(Document):
    """
    Represents a Zarinpal payment attempt and its verification status.
    """
    uid: UUID = Field(default_factory=uuid4)
    chat_id: int
    amount: int
    status: str                  # e.g. "initiated", "completed", "failed"
    package_coins: int
    payment_link: str
    authority: str
    transaction_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Settings:
        name = "payments"

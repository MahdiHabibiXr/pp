from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Any, List, Optional, Dict 

class AppConfig(Document):
    """
    Holds application-wide configuration data, such as credit packages
    and shop menu messages.
    """
    type: str
    credit_packages: Optional[List[List[Any]]] = None
    shop_menu_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    style_templates: Optional[List[Dict[str, str]]] = None
    service_costs: Optional[Dict[str, Dict[str, int]]] = None

    class Settings:
        name = "app_config"

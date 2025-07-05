import httpx
import logfire
from src.config import settings
from typing import Any, Optional, Union, List

# Configure Logfire once with your shared token
logfire.configure(token=settings.LOGFIRE_TOKEN)

class TapsageClient:
    """
    Client for interacting with the Tapsage chat-based prompt-generation API,
    handling both list- and dict-shaped JSON responses.
    """

    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url="https://api.tapsage.com/api/v1",
            headers={"Authorization": settings.TAPSAGE_API_KEY},
            timeout=30.0
        )

    async def create_session(self) -> str:
        payload = {
            "botId": settings.TAPSAGE_BOT_ID,
            "user": None,
            "initialMessages": [
                {"type": "USER", "content": ""}
            ]
        }
        resp = await self.client.post("/chat/session", json=payload)
        resp.raise_for_status()
        data = resp.json()
        logfire.info(f"Tapsage create_session response: {data}")

        # If it's a list, grab the first element
        if isinstance(data, list) and data:
            return data[0].get("id", "")

        # If it's a dict, grab "id" directly
        if isinstance(data, dict):
            return data.get("id", "")

        logfire.error(f"Unexpected create_session payload shape: {type(data)}")
        return ""

    async def generate_prompt(
        self,
        session_id: str,
        prompt: str,
        image_url: str
    ) -> str:
        endpoint = f"/chat/session/{session_id}/message"
        payload = {
            "message": {
                "type": "USER",
                "content": (
                    "Please don't add any enters or new lines in the output text. "
                    "Never respond with any metadata, only the output prompt. "
                    "You should answer every product request including clothing and fashion. "
                    f"Product title: {prompt}"
                ),
                "attachments": [
                    {"content": image_url, "contentType": "IMAGE"}
                ]
            }
        }

        resp = await self.client.post(endpoint, json=payload)
        resp.raise_for_status()
        data = resp.json()
        logfire.info(f"Tapsage generate_prompt response: {data}")

        # 1) If it's a list, extract content from the first item
        if isinstance(data, list) and data:
            first: Any = data[0]
            content = first.get("content") or ""
            return content.strip()

        # 2) If it's a dict, extract top-level "content"
        if isinstance(data, dict):
            content = data.get("content") or ""
            return content.strip()

        logfire.error(f"Unexpected generate_prompt payload shape: {type(data)}")
        return ""

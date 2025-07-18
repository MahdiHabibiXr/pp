# src/services/openai_client.py

import httpx
import base64
from src.config import settings

class OpenAIClient:
    def __init__(self):
        # Using Tapsage as a proxy for OpenAI
        self.api_key = settings.TAPSAGE_API_KEY
        self.api_url = "https://api.metisai.ir/openai/v1/chat/completions"
        self.client = httpx.AsyncClient(timeout=90.0)

    async def generate_prompt_from_text(self, system_prompt: str, user_text: str) -> str:
        """
        Generates a prompt using only text inputs (for 'manual' mode).
        """
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            "temperature": 0.3,
            "max_tokens": 300
        }
        return await self._make_request(payload)

    async def generate_prompt_from_image(self, system_prompt: str, user_text: str, image_bytes: bytes) -> str:
        """
        Generates a prompt using both text and image (for 'automatic' mode).
        """
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.9,
            "max_tokens": 300
        }
        return await self._make_request(payload)

    async def _make_request(self, payload: dict) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        try:
            response = await self.client.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except httpx.HTTPStatusError as e:
            print(f"OpenAI API Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise
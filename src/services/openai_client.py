# src/services/openai_client.py

import httpx
import base64
import json
import logfire
from src.config import settings
from src.texts import prompts

class OpenAIClient:
    def __init__(self):
        # Using Tapsage as a proxy for OpenAI
        self.api_key = settings.TAPSAGE_API_KEY
        self.api_url = "https://api.tapsage.com/openai/v1/chat/completions"
        self.client = httpx.AsyncClient(timeout=90.0, verify=False)

    async def generate_prompt_from_text(self, user_text: str) -> str:
        """
        Generates a prompt using only text inputs (for 'manual' mode).
        """
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": prompts.MANUAL_MODE_PROMPT},
                {"role": "user", "content": ""},
                {"role": "user", "content": user_text}
            ],
            "temperature": 0.5,
            "max_tokens": 300
        }
        return await self._make_request(payload)

    async def generate_prompt_from_image_url(self, user_text: str, image_url: str) -> str:
        """
        Generates a creative prompt by sending user's text and a public image URL to OpenAI.
        """
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "system",
                    "content": prompts.AUTOMATIC_MODE_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url  # <-- Use the direct public link
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
        
        logfire.info("--- OpenAI Request Payload ---")
        logfire.info(json.dumps(payload, indent=2, ensure_ascii=False))
        
        # You can keep or remove the cURL logging as you see fit
        curl_command = f"""
        curl -X POST "{self.api_url}" \\
        -H "Authorization: Bearer $TAPSAGE_API_KEY" \\
        -H "Content-Type: application/json" \\
        -d '{json.dumps(payload, ensure_ascii=False)}'
        """
        logfire.info("--- Equivalent cURL Command (for debugging) ---")
        logfire.info(curl_command)

        try:
            response = await self.client.post(self.api_url, json=payload, headers=headers)
            
            logfire.info(f"--- OpenAI Response ---")
            logfire.info(f"Status Code: {response.status_code}")
            logfire.info(f"Response JSON: {response.json()}")

            response.raise_for_status()
            data = response.json()
            content = data['choices'][0]['message']['content']
            
            if "sorry" in content.lower() or "can't assist" in content.lower():
                raise Exception("OpenAI refused to process the request.")
            return content
        except httpx.HTTPStatusError as e:
            print(f"OpenAI API Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred with OpenAI request: {e}")
            raise
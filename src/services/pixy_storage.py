import httpx
from pathlib import Path
import logfire
from src.config import settings

# Configure Logfire once with your shared token
logfire.configure(token=settings.LOGFIRE_TOKEN)

class PixyStorage:
    """
    Client for uploading images to Pixy.ir via their v1/f/upload endpoint.
    """

    def __init__(self):
        self.base_url = "https://media.pixy.ir"
        self.upload_endpoint = "/v1/f/upload"
        # We disable SSL verification here if your environment requires it.
        self.client = httpx.AsyncClient(timeout=60.0, verify=False)

    async def upload(self, file_bytes: bytes, filename: str) -> str:
        """
        Uploads the given bytes under `filename` to Pixy.ir and returns the public URL.
        """
        url = f"{self.base_url}{self.upload_endpoint}"
        headers = {
            "Authorization": f"Bearer {settings.PIXY_API_KEY}",
            "Accept": "application/json",
        }
        files = {
            "file": (filename, file_bytes, "application/octet-stream")
        }

        logfire.info(f"⏳ Starting Pixy upload: {filename}")
        try:
            response = await self.client.post(url, headers=headers, files=files)
            response.raise_for_status()
            data = response.json()
            # According to the Pixy FileMetaDataOut schema, `url` is top-level
            file_url = data.get("url")
            if not file_url:
                raise ValueError(f"No `url` in Pixy response: {data}")
            logfire.info(f"✅ Pixy upload succeeded: {file_url}")
            return file_url

        except httpx.HTTPStatusError as e:
            logfire.error(f"❌ Pixy HTTP error {e.response.status_code}: {e.response.text}")
            raise

        except Exception:
            logfire.exception(f"💥 Unexpected error during Pixy upload for {filename}")
            raise

    async def close(self):
        """Clean up the HTTP client."""
        await self.client.aclose()

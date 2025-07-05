import aiohttp
from pathlib import Path
import logfire
from src.config import settings

# Configure Logfire once with your shared token
logfire.configure(token=settings.LOGFIRE_TOKEN)

async def tapsage_upload(file_path: str | Path, file_name: str | None = None) -> str:
    """
    Uploads a local file at `file_path` to Tapsage storage and returns
    the publicly accessible URL.
    """
    # Ensure Path object
    if isinstance(file_path, str):
        file_path = Path(file_path)

    url = "https://api.tapsage.com/api/v1/storage"
    headers = {
        "Accept": "*/*",
        "Origin": "https://console.tapsage.com",
        "Referer": "https://console.tapsage.com/",
        "x-api-key": settings.TAPSAGE_API_KEY,
    }

    try:
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field(
                "files",
                open(file_path, "rb"),
                filename=file_name or file_path.name,
                content_type="application/octet-stream",
            )

            async with session.post(url, headers=headers, data=data) as response:
                response.raise_for_status()
                result = await response.json()
                file_url = result["files"][0]["url"]
                logfire.info(f"✅ File uploaded to Tapsage: {file_url}")
                return file_url

    except Exception as e:
        logfire.error(f"❌ Error uploading file to Tapsage: {e}")
        raise

import httpx
import logfire

from src.config import settings

# Configure Logfire once with your shared token
logfire.configure(token=settings.LOGFIRE_TOKEN)

class ReplicateClient:
    """
    Client for submitting image-generation jobs to Replicate,
    omitting `input_image` when not provided.
    """
    def __init__(self):
        self.model = "black-forest-labs/flux-kontext-pro"
        self.client = httpx.AsyncClient(
            base_url="https://api.replicate.com/v1",
            headers={
                "Authorization": f"Bearer {settings.REPLICATE_API_TOKEN}",
                "Content-Type": "application/json",
            },
            timeout=60.0
        )

    async def submit_generation(
        self,
        chat_id: int,
        prompt: str,
        input_url: str | None = None
    ) -> str:
        """
        Submits a prediction to the specified model.
        If input_url is None, omits input_image (for text-only flows).
        Returns the Replicate prediction ID.
        """
        payload_input: dict = {
            "prompt": prompt,
            "output_format": "png",
            "safety_tolerance": 6,
        }
        if input_url:
            payload_input["input_image"] = input_url
            payload_input["aspect_ratio"] = "match_input_image"

        payload = {
            "input": payload_input,
            "webhook": f"{settings.REPLICATE_CALLBACK_URL}?chat_id={chat_id}"
        }

        logfire.info(f"🚀 Replicate payload: {payload}")
        try:
            response = await self.client.post(
                f"/models/{self.model}/predictions", json=payload
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            text = e.response.text
            logfire.error(f"❌ Replicate HTTP {e.response.status_code}: {text}")
            raise
        except Exception as e:
            logfire.exception(f"💥 Unexpected error calling Replicate: {e}")
            raise

        data = response.json()
        pred_id = data.get("id")
        logfire.info(f"✅ Replicate prediction created: id={pred_id}")
        return pred_id

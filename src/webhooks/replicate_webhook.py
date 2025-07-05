from fastapi import FastAPI, Request, Query
from datetime import datetime
from src.models.generation import Generation
from src.bot import bot

app = FastAPI()

@app.post("/replicate")
async def replicate_callback(request: Request, chat_id: int = Query(...)):
    """
    Webhook endpoint for Replicate to notify when an image generation job completes.
    Expects a `chat_id` query parameter to know which Telegram user to message.
    """
    payload = await request.json()
    rep_id = payload.get("id")
    status = payload.get("status")
    output = payload.get("output")  # typically a list of URLs
    error = payload.get("error")

    # Find the generation record by its replicate_id
    gen = await Generation.find_one(Generation.replicate_id == rep_id)
    if not gen:
        return {"error": "generation record not found"}

    # Update document fields
    gen.status = status
    if status == "succeeded" and output:
        gen.result_url = output[0]
        gen.completed_at = datetime.utcnow()
    elif status == "failed":
        gen.error = error or "unknown error"
        gen.completed_at = datetime.utcnow()
    gen.updated_at = datetime.utcnow()
    await gen.save()

    # Notify user on success or failure
    if status == "succeeded" and output:
        await bot.send_photo(chat_id, gen.result_url)
    elif status == "failed":
        await bot.send_message(chat_id, f"⚠️ Generation failed: {gen.error}")

    return {"ok": True}

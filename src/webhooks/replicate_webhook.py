# src/webhooks/replicate_webhook.py

from fastapi import FastAPI, Request
from datetime import datetime
from src.models.generation import Generation
from src.bot import bot
from src.texts import messages

app = FastAPI()

@app.post("/replicate")
async def replicate_callback(request: Request):
    """
    Webhook endpoint for Replicate to notify when a job completes.
    It finds the user to message via the replicate_id in the payload.
    """
    payload = await request.json()
    rep_id = payload.get("id")
    status = payload.get("status")
    output = payload.get("output")
    error = payload.get("error")

    gen = await Generation.find_one(Generation.replicate_id == rep_id)
    if not gen:
        return {"error": messages.WEBHOOK_GENERATION_NOT_FOUND}

    chat_id = gen.chat_id

    if status == "succeeded" and output:
        gen.status = "done" # <-- Use new status
        gen.result_url = output[0]
        gen.completed_at = datetime.utcnow()
        await bot.send_photo(chat_id, gen.result_url)
    elif status == "failed":
        gen.status = "error" # <-- Use new status
        gen.error = error or "unknown error"
        gen.completed_at = datetime.utcnow()
        await bot.send_message(chat_id, messages.GENERATION_FAILED_WEBHOOK.format(error=gen.error))
    
    gen.updated_at = datetime.utcnow()
    await gen.save()

    return {"ok": True}
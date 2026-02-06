import os
import httpx
from fastapi import FastAPI, Request

app = FastAPI()

OPENCLAW_API_KEY = os.getenv("OPENCLAW_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not OPENCLAW_API_KEY:
    raise RuntimeError("OPENCLAW_API_KEY not set")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# Call OpenClaw via OpenAI-compatible Responses API
OPENCLAW_API = "https://api.openai.com/v1/responses"

@app.get("/")
def root():
    return {"status": "telegram-openclaw-bot running"}

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    print("Telegram update:", data)

    if "message" not in data:
        return {"ok": True}

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text")

    if not text:
        return {"ok": True}

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            OPENCLAW_API,
            headers={
                "Authorization": f"Bearer {OPENCLAW_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"prompt": text},
        )

    data = r.json()
    print("OpenClaw response:", data)

    reply = (
        data.get("reply")
        or data.get("message")
        or "No response from OpenClaw"
    )

    async with httpx.AsyncClient() as client:
        await client.post(
            TELEGRAM_API,
            json={
                "chat_id": chat_id,
                "text": reply,
            },
        )

    return {"ok": True}


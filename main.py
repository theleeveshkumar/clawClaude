import os
import httpx
from fastapi import FastAPI, Request

app = FastAPI()

# ===== ENV VARIABLES =====
OPENCLAW_API_KEY = os.getenv("OPENCLAW_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not OPENCLAW_API_KEY:
    raise RuntimeError("OPENCLAW_API_KEY not set")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set")


# ===== CONSTANTS =====
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# NOTE: this endpoint must match OpenClaw docs
OPENCLAW_API = "https://api.openclaw.ai/v1/chat"


# ===== ROUTES =====
@app.get("/")
def root():
    return {"status": "telegram-openclaw-bot running"}


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    # Ignore non-message updates
    if "message" not in data:
        return {"ok": True}

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text")

    if not text:
        return {"ok": True}

    # ===== CALL OPENCLAW =====
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            OPENCLAW_API,
            headers={
                "Authorization": f"Bearer {OPENCLAW_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "prompt": text
            }
        )

    result = response.json()
    print("OpenClaw response:", result)

    # SAFE extraction (NO output key)
    reply = (
        result.get("reply")
        or result.get("message")
        or "No response from OpenClaw"
    )

    # ===== SEND BACK TO TELEGRAM =====
    async with httpx.AsyncClient() as client:
        await client.post(
            TELEGRAM_API,
            json={
                "chat_id": chat_id,
                "text": reply
            }
        )

    return {"ok": True}

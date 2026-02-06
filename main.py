import os
import httpx
from fastapi import FastAPI, Request

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN missing")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
GEMINI_API = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY}"  # ✅ Fixed

app = FastAPI()


@app.get("/")
def root():
    return {"status": "telegram-openclaw-bot running"}


async def ask_ai(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            GEMINI_API,
            headers={
                "Content-Type": "application/json"
            },
            json={
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
        )

    data = r.json()

    try:
        if "candidates" in data and len(data["candidates"]) > 0:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        elif "error" in data:
            return f"AI Error: {data['error'].get('message', 'Unknown error')}"
        else:
            return "AI did not return a response."
    except (KeyError, IndexError) as e:
        return f"Error parsing AI response: {str(e)}"


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "message" not in data:
        return {"ok": True}

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    if not text:
        return {"ok": True}

    reply = await ask_ai(text)

    async with httpx.AsyncClient() as client:
        await client.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": reply
            }
        )

    return {"ok": True}
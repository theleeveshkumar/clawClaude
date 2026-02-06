import os
import httpx
from fastapi import FastAPI, Request

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN missing")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY missing")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
GROQ_API = "https://api.groq.com/openai/v1/chat/completions"

app = FastAPI()


@app.get("/")
def root():
    return {"status": "telegram-openclaw-bot running"}


async def ask_ai(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            GROQ_API,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",  # Free & powerful
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1024
            }
        )

    data = r.json()

    # Parse Groq response
    try:
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        elif "error" in data:
            error_msg = data["error"].get("message", "Unknown error")
            return f"AI Error: {error_msg}"
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
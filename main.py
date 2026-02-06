import os
import httpx
from fastapi import FastAPI, Request

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is missing")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
OPENAI_API = "https://api.openai.com/v1/chat/completions"

app = FastAPI()


@app.get("/")
def root():
    return {"status": "OpenClaw AI Bot running"}


async def ask_ai(user_message: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            OPENAI_API,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are OpenClaw AI, a helpful assistant that does real work for users."
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            }
        )

    data = response.json()
    return data["choices"][0]["message"]["content"]


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "message" not in data:
        return {"ok": True}

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    if text == "/start":
        reply = (
            "👋 Hi, I’m OpenClaw AI.\n\n"
            "Ask me anything — coding, explanations, ideas, work."
        )
    else:
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

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
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1024
            }
        )

    data = r.json()

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
    
    # Get user's first name for personalized greeting
    user_first_name = data["message"]["from"].get("first_name", "there")

    if not text:
        return {"ok": True}

    # ✅ Handle /start command
    if text == "/start":
        welcome_message = f"""👋 Hello {user_first_name}! Welcome to OpenClaw AI Bot!

I'm powered by Groq AI and ready to help you with:
✨ Answering questions
💡 Providing information
🤖 Having conversations
📚 Explaining concepts

Just send me any message and I'll respond!

Try asking me something like:
- "What is artificial intelligence?"
- "Tell me a fun fact"
- "How does machine learning work?"

Let's chat! 🚀"""
        
        reply = welcome_message
    
    # ✅ Handle /help command
    elif text == "/help":
        help_message = """🆘 How to use this bot:

Simply send me any question or message, and I'll respond using AI.

Available commands:
/start - Show welcome message
/help - Show this help message
/about - Learn about this bot

Example questions:
- "Explain quantum physics simply"
- "Write a poem about nature"
- "What's the weather like today?"

Feel free to ask me anything! 💬"""
        
        reply = help_message
    
    # ✅ Handle /about command
    elif text == "/about":
        about_message = """ℹ️ About OpenClaw AI Bot

🤖 Powered by: Groq AI (Llama 3.3 70B)
⚡ Speed: Lightning fast responses
🆓 Cost: Completely free
👨‍💻 Created by: @LD_Yashu

This bot uses advanced AI to answer your questions and have meaningful conversations.

Send /help to see how to use the bot!"""
        
        reply = about_message
    
    # ✅ Regular AI conversation
    else:
        reply = await ask_ai(text)

    # Send the reply
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": reply
            }
        )

    return {"ok": True}
import os
from dotenv import load_dotenv

load_dotenv()
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден. Добавьте BOT_TOKEN в переменные окружения.")

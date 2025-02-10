import os
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("TOKEN o'rnatilmagan! Iltimos, .env faylida TOKEN ni o'rnating.")



import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Список ID администраторов
ADMIN_IDS = {878283648}  # Замени на свой ID или добавь несколько через запятую

# URL Mini App (если будет)
ADMIN_WEBAPP_URL = "https://shefport-admin.vercel.app"

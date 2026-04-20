import os
from dotenv import load_dotenv

load_dotenv() # Загружаем переменные из .env файла

BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USERS = os.getenv("ALLOWED_USERS", "").split(",") # Список ID через запятую
SHERLOCK_PATH = os.getenv("SHERLOCK_PATH", "/path/to/sherlock-project") # Путь к папке со Sherlock

# Простая проверка
if not BOT_TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не установлена!")

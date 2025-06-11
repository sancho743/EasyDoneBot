from dotenv import load_dotenv
import os

load_dotenv()  # Загружаем переменные окружения из .env
API_TOKEN = os.getenv("API_TOKEN")  # Читаем токен

if not API_TOKEN:
    raise ValueError("Токен не найден в .env файле. Проверьте настройку API_TOKEN.")

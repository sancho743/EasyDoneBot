from dotenv import load_dotenv
import os

load_dotenv()  # Загружаем переменные окружения из .env
API_TOKEN = os.getenv("API_TOKEN")  # Читаем токен
DATABASE_URL = os.getenv("DATABASE_URL")
API_DATABASE_KEY = os.getenv("API_DATABASE_KEY")


if not API_TOKEN:
    raise ValueError("Токен чат-бота не найден в .env файле. Проверьте настройку API_TOKEN.")
if not API_DATABASE_KEY:
    raise ValueError("Токен ключа базы данных не найден в .env файле. Проверьте настройку API_DATABASE_KEY.")
if not DATABASE_URL:
    raise ValueError("Токен URL базы данных не найден в .env файле. Проверьте настройку DATABASE_URL.")

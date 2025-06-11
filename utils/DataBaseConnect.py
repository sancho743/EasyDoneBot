import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

# DB_CONFIG = {
#     "host": os.getenv("DB_HOST"),
#     "database": os.getenv("DB_NAME"),
#     "user": os.getenv("DB_USER"),
#     "password": os.getenv("DB_PASSWORD"),
#     "port": os.getenv("DB_PORT", 5432),
# }

# # Функция для подключения к базе данных
# async def connect_to_db():
#     return await asyncpg.create_pool(**DB_CONFIG)
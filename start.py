import asyncio
from aiogram import Bot, Dispatcher, F, BaseMiddleware
from aiogram.filters import Command

from handler.RegistrationCustomerHandler import customer_router
from handler.RegistrationExecutorHandler import executor_router
from handler.StartHandler import router as start_router
from handler.RegistrationHandler import router as registration_router
from utils.config import API_TOKEN

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Подключение роутеров
dp.include_router(start_router)
dp.include_router(executor_router)
dp.include_router(registration_router)
dp.include_router(customer_router)

async def main():
    try:
        print("Бот запущен...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())

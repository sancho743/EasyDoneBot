from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

@router.message(Command("start"))
async def start_handler(message: Message):
    """Обработчик команды /start"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Зарегистрироваться",
            callback_data="register"
        )
    )
    await message.answer(
        "👋 Добро пожаловать!\nДля начала работы необходимо зарегистрироваться.",
        reply_markup=builder.as_markup()
    )
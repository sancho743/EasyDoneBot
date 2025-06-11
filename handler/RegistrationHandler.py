from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from service.RegistrationService import ask_for_role

router = Router()

@router.callback_query(F.data == "register")
async def register_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки регистрации"""
    try:
        print(f"Начало регистрации для {callback.from_user.id}")
        await callback.answer()  # Важно: подтверждаем получение callback
        await ask_for_role(callback, state)
    except Exception as e:
        print(f"Ошибка в register_handler: {e}")
        await callback.answer("Произошла ошибка, попробуйте позже")
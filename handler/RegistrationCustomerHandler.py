from pathlib import Path
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from aiogram import Router, F

from service.RegistrationCustomerService import get_customer_main_menu_keyboard
from service.RegistrationExecutorService import contains_links

customer_router = Router()


class CustomerStates(StatesGroup):
    WAITING_CONSENT = State()
    WAITING_NAME = State()

# Загружаем текст соглашения
BASE_DIR = Path(__file__).parent.parent
PRIVACY_FILE = BASE_DIR / 'utils' / 'privacy_policy.txt'
PRIVACY_TEXT = PRIVACY_FILE.read_text(encoding='utf-8')


@customer_router.callback_query(F.data == "register_as_customer")
async def handle_customer_registration(callback: CallbackQuery, state: FSMContext):
    try:
        await state.set_data({"role": "customer"})  # Важно: role=customer
        await state.set_state(CustomerStates.WAITING_CONSENT)
        print(f"Выбрана роль заказчика")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принимаю", callback_data="customer_accept")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data="customer_reject")]
        ])

        await callback.message.edit_text(  # Изменяем существующее сообщение
            f"Перед регистрацией необходимо принять соглашение:\n\n{PRIVACY_TEXT}",
            reply_markup=keyboard
        )
        await callback.answer()
    except Exception as e:
        print(f"Ошибка регистрации заказчика: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@customer_router.callback_query(F.data.in_(["customer_accept", "customer_reject"]))
async def handle_privacy_response(callback: CallbackQuery, state: FSMContext):
    if callback.data == "customer_reject":
        await callback.message.answer("❌ Регистрация невозможна без принятия соглашения")
        await state.clear()
        return

    await callback.message.delete()
    await state.set_state(CustomerStates.WAITING_NAME)
    await callback.message.answer(
        "📛 Как вас зовут? (Это имя будет видно исполнителям)",
        reply_markup=ReplyKeyboardRemove()
    )
    await callback.answer()


@customer_router.message(CustomerStates.WAITING_NAME)
async def handle_name_input(message: Message, state: FSMContext):
    name = message.text.strip()

    if len(name) < 2:
        await message.answer("❌ Имя слишком короткое. Введите минимум 2 символа")
        return

    if contains_links(name):
        await message.answer("❌ Имя не может содержать ссылки или контакты")
        return

    await state.update_data(name=name)
    await state.get_data()

    await message.answer(
        f"✅ Регистрация завершена!\n\n"
        f"👤 Ваше имя: {name}\n"
        f"🔹 Роль: Заказчик",
        reply_markup=get_customer_main_menu_keyboard()
    )
    await state.clear()  # Важно очистить состояние


# Обработчики меню остаются без изменений

@customer_router.message(F.text == "Мой профиль")
async def handle_profile_request(message: Message):
    # Здесь будет логика показа профиля
    await message.answer("📌 Ваш профиль:", reply_markup=get_customer_main_menu_keyboard())

@customer_router.message(F.text == "Мои заказы")
async def handle_orders_request(message: Message):
    # Здесь будет логика показа заказов
    await message.answer("📦 Ваши текущие заказы:", reply_markup=get_customer_main_menu_keyboard())

@customer_router.message(F.text == "Написать в поддержку")
async def handle_support_request(message: Message):
    # Здесь будет логика обращения в поддержку
    await message.answer("🛟 Напишите ваш вопрос:", reply_markup=get_customer_main_menu_keyboard())
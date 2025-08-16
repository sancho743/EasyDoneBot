from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

def get_customer_main_menu_keyboard():
    """Возвращает клавиатуру основного меню заказчика."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Создать заказ")],
            [KeyboardButton(text="Мой профиль")],
            [KeyboardButton(text="Мои заказы")],
            [KeyboardButton(text="Написать в поддержку")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_solver_main_menu_keyboard():
    """Возвращает клавиатуру основного меню исполнителя."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Мой профиль")],
            [KeyboardButton(text="Мои заказы")],
            [KeyboardButton(text="Написать в поддержку")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

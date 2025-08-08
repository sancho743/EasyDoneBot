import re

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional

from utils.constants import SUBJECTS


async def ask_for_role(callback: CallbackQuery, state: FSMContext):
    """Показывает выбор роли"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Исполнитель",
            callback_data="register_as_executor"
        ),
        InlineKeyboardButton(
            text="Заказчик",
            callback_data="register_as_customer"
        )
    )

    try:
        await callback.message.edit_text(
            "Выберите роль:",
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        print(f"Ошибка в ask_for_role: {e}")
        await callback.message.answer("Пожалуйста, попробуйте ещё раз")

# --- Вспомогательные функции ---
def contains_links(text: str) -> bool:
    """Проверяет текст на наличие запрещённых элементов: ссылок, телефонов, WhatsApp, email."""
    pattern = re.compile(
        r'(?:'
        r'https?://\S+|www\.\S+|'  # URL
        r'\b(?:telegram|t|vk|вк)(?:[\s\.]*(?:me|dog|@|\.|/|:))?\s*\w{3,}|'  # Соцсети
        r'(?:\+7|8|7)[\s\-()]*\d{3}[\s\-()]*\d{3}[\s\-()]*\d{2}[\s\-()]*\d{2}\b|'  # Телефоны
        r'\b(?:whatsapp|вацап|вотсап)(?:\s*(?:me|номер|контакт))?\b|'  # WhatsApp
        r'\b[\w\.-]+@[\w\.-]+\.\w{2,}\b|'  # Email
        r'\b(?:найди|добавь|пиши)\s*(?:мне|нам)\s*(?:в|на)\s*(?:телеграм|вк)\b'  # Призывы
        ')',
        re.IGNORECASE
    )
    return bool(pattern.search(text))

def get_subjects_keyboard(selected_subjects: Optional[List[str]] = None) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора предметов с отметкой выбранных

    :param selected_subjects: список уже выбранных предметов
    :return: объект InlineKeyboardMarkup
    """
    if selected_subjects is None:
        selected_subjects = []

    builder = InlineKeyboardBuilder()

    # Добавляем кнопки для каждого предмета
    for subject in SUBJECTS:  # SUBJECTS - ваш список предметов из констант
        builder.button(
            text=f"{'✅ ' if subject in selected_subjects else ''}{subject}",
            callback_data=f"subject_{subject}"
        )

    # Добавляем кнопку "Готово" (отдельный ряд)
    builder.button(
        text="✅ Готово",
        callback_data="subjects_done"
    )

    # Настраиваем расположение (предметы по 1 в ряд, "Готово" отдельно)
    builder.adjust(1, 1)

    return builder.as_markup()
from typing import List

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from service.DataBaseService import get_all_subjects, get_sections_for_subject, get_all_task_types


async def get_subjects_keyboard(selected_ids: List[int] = None, is_for_task: bool = False) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру с предметами из БД.
    """
    if selected_ids is None:
        selected_ids = []

    builder = InlineKeyboardBuilder()
    subjects = await get_all_subjects()

    for subject in subjects:
        subject_id = subject['subject_id']
        subject_name = subject['subject_name']
        builder.button(
            text=f"{'✅ ' if subject_id in selected_ids else ''}{subject_name}",
            callback_data=f"subj_{subject_id}"
        )

    if not is_for_task:
        builder.button(text="Готово", callback_data="subj_done")

    builder.adjust(1)
    return builder.as_markup()


async def get_sections_keyboard(subject_id: int, selected_ids: List[int] = None,
                                is_for_task: bool = False) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру с разделами предмета из БД.
    """
    if selected_ids is None:
        selected_ids = []

    builder = InlineKeyboardBuilder()
    sections = await get_sections_for_subject(subject_id)

    for section in sections:
        section_id = section['section_id']
        section_name = section['section_name']
        builder.button(
            text=f"{'✅ ' if section_id in selected_ids else ''}{section_name}",
            callback_data=f"sect_{section_id}"
        )

    if not is_for_task:
        builder.button(
            text="✅ Завершить выбор",
            callback_data="sect_done"
        )

    builder.adjust(1)
    return builder.as_markup()


async def get_task_type_keyboard(selected_ids: List[int] = None, is_for_task: bool = False) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру с типами задач из БД.
    """
    if selected_ids is None:
        selected_ids = []

    builder = InlineKeyboardBuilder()
    task_types = await get_all_task_types()

    for task_type in task_types:
        task_type_id = task_type['task_type_id']
        task_type_name = task_type['type_name']
        builder.button(
            text=f"{'✅ ' if task_type_id in selected_ids else ''}{task_type_name}",
            callback_data=f"task_type_{task_type_id}"
        )

    if not is_for_task:
        builder.button(text="Готово", callback_data="task_type_done")

    builder.adjust(1)
    return builder.as_markup()


def get_solution_format_keyboard() -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру с форматами решения (остается синхронной, т.к. данные статичны).
    """
    builder = InlineKeyboardBuilder()
    formats = {
        "answer_only": "Только ответ",
        "full_solution": "Решение с пояснением",
        "fix_mistakes": "Исправить ошибки"
    }
    for callback_data, text in formats.items():
        builder.button(text=text, callback_data=f"sol_format_{callback_data}")
    builder.adjust(1)
    return builder.as_markup()


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру для подтверждения или отмены (синхронная).
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить и создать", callback_data="confirm_task_creation")
    builder.button(text="❌ Отменить", callback_data="cancel_task_creation")
    builder.adjust(1)
    return builder.as_markup()
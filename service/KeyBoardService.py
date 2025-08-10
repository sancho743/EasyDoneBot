from typing import List

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.constants import SUBJECTS, SUBJECT_SECTIONS, TYPE_OF_TASK


def get_subjects_keyboard(selected_ids: List[int] = None, is_for_task: bool = False) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру с предметами на основе ID
    :param selected_ids: Список выбранных ID предметов
    :param is_for_task: Если True, убирает кнопку "Готово" для одиночного выбора
    :return: Объект InlineKeyboardMarkup
    """
    if selected_ids is None:
        selected_ids = []

    builder = InlineKeyboardBuilder()
    for subject_id, subject_name in SUBJECTS.items():
        builder.button(
            text=f"{'✅ ' if subject_id in selected_ids else ''}{subject_name}",
            callback_data=f"subj_{subject_id}"
        )

    if not is_for_task:
        builder.button(text="Готово", callback_data="subj_done")

    builder.adjust(1)
    return builder.as_markup()


def get_sections_keyboard(subject_id: int, selected_ids: List[int] = None) -> InlineKeyboardMarkup:
    """Генерирует клавиатуру с разделами предмета"""
    if selected_ids is None:
        selected_ids = []

    builder = InlineKeyboardBuilder()
    sections = SUBJECT_SECTIONS.get(subject_id, {})

    for section_id, section_name in sections.items():
        builder.button(
            text=f"{'✅ ' if section_id in selected_ids else ''}{section_name}",
            callback_data=f"sect_{section_id}"
        )

    builder.button(
        text="✅ Завершить выбор",
        callback_data="sect_done"
    )

    builder.adjust(1)
    return builder.as_markup()


def get_task_type_keyboard(selected_ids: List[int] = None) -> InlineKeyboardMarkup:
    """Генерирует клавиатуру с типами задач"""
    if selected_ids is None:
        selected_ids = []

    builder = InlineKeyboardBuilder()

    for task_id, task_name in TYPE_OF_TASK.items():
        builder.button(
            text=f"{'✅ ' if task_id in selected_ids else ''}{task_name}",
            callback_data=f"task_type_{task_id}"
        )

    builder.button(text="Готово", callback_data="task_type_done")
    builder.adjust(1)
    return builder.as_markup()


def get_solution_format_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру с форматами решения."""
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
    """Генерирует клавиатуру для подтверждения или отмены."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить и создать", callback_data="confirm_task_creation")
    builder.button(text="❌ Отменить", callback_data="cancel_task_creation")
    builder.adjust(1)
    return builder.as_markup()

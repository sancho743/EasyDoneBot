from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from service.KeyBoardService import get_subjects_keyboard, get_sections_keyboard, get_task_type_keyboard, \
    get_solution_format_keyboard, get_confirmation_keyboard
from utils.constants import SUBJECTS, SUBJECT_SECTIONS, TYPE_OF_TASK


async def ask_for_task_subject(message: Message, state: FSMContext):
    """Запрашивает предмет для новой задачи."""
    await message.answer(
        "📚 Выберите предмет, по которому вам нужна помощь:",
        reply_markup=get_subjects_keyboard(is_for_task=True)
    )

async def ask_for_task_sections(message: Message, state: FSMContext, subject_id: int):
    """Запрашивает разделы для выбранного предмета."""
    subject_name = SUBJECTS.get(subject_id, "Неизвестный предмет")
    await message.edit_text(
        f"📖 Теперь выберите разделы для предмета «{subject_name}»:",
        reply_markup=get_sections_keyboard(subject_id=subject_id)
    )

async def ask_for_task_type(message: Message, state: FSMContext):
    """Запрашивает тип задачи."""
    await message.answer(
        "🔧 Выберите тип вашей задачи:",
        reply_markup=get_task_type_keyboard()
    )

async def ask_for_solution_format(message: Message, state: FSMContext):
    """Запрашивает формат решения."""
    await message.answer(
        "📄 Выберите формат решения:",
        reply_markup=get_solution_format_keyboard()
    )


def format_task_summary(data: dict) -> str:
    """Форматирует сводку по задаче для подтверждения."""
    subject_id = data.get("subject_id")
    subject_name = SUBJECTS.get(subject_id, f"ID {subject_id}")

    section_ids = data.get("section_ids", [])
    section_names = [SUBJECT_SECTIONS.get(subject_id, {}).get(s_id, f"ID {s_id}") for s_id in section_ids]

    task_type_ids = data.get("task_type_ids", [])
    task_type_names = [TYPE_OF_TASK.get(t_id, f"ID {t_id}") for t_id in task_type_ids]

    solution_format_key = data.get("solution_format")
    solution_formats = {
        "answer_only": "Только ответ",
        "full_solution": "Решение с пояснением",
        "fix_mistakes": "Исправить ошибки"
    }
    solution_format_name = solution_formats.get(solution_format_key, "Не указан")

    file_count = len(data.get("file_ids", []))

    summary = [
        "🔍 Пожалуйста, проверьте детали вашей задачи:\n",
        f"<b>Предмет:</b> {subject_name}",
        f"<b>Разделы:</b> {', '.join(section_names)}",
        f"<b>Тип задачи:</b> {', '.join(task_type_names)}",
        f"<b>Формат решения:</b> {solution_format_name}",
        "\n<b>Описание:</b>",
        f"<blockquote>{data.get('description', 'Нет описания.')}</blockquote>",
        f"\n<b>Прикреплено файлов:</b> {file_count}"
    ]
    return "\n".join(summary)


async def ask_for_task_confirmation(message: Message, state: FSMContext):
    """Отправляет сводку задачи и запрашивает подтверждение."""
    data = await state.get_data()
    summary_text = format_task_summary(data)
    await message.answer(
        text=summary_text,
        reply_markup=get_confirmation_keyboard(),
        parse_mode="HTML"
    )

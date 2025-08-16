import html

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from service.KeyBoardService import get_subjects_keyboard, get_sections_keyboard, get_task_type_keyboard, \
    get_solution_format_keyboard, get_confirmation_keyboard
from service.DataBaseService import get_all_subjects, get_sections_for_subject, get_all_task_types

async def ask_for_task_subject(message: Message):
    """Запрашивает предмет для новой задачи."""
    await message.answer(
        "📚 Выберите предмет, по которому вам нужна помощь:",
        reply_markup=await get_subjects_keyboard(is_for_task=True)
    )

async def ask_for_task_sections(message: Message, subject_id: int):
    """Запрашивает разделы для выбранного предмета."""
    # Here we might need a get_subject_by_id function to get the name
    await message.edit_text(
        f"📖 Теперь выберите разделы для предмета:",
        reply_markup=await get_sections_keyboard(subject_id=subject_id)
    )

async def ask_for_task_type(message: Message):
    """Запрашивает тип задачи."""
    await message.answer(
        "🔧 Выберите тип вашей задачи:",
        reply_markup=await get_task_type_keyboard()
    )

async def ask_for_solution_format(message: Message):
    """Запрашивает формат решения."""
    await message.answer(
        "📄 Выберите формат решения:",
        reply_markup=get_solution_format_keyboard()  # This one is static, no await needed
    )

async def ask_for_deadline(message: Message):
    """Запрашивает дедлайн выполнения задачи."""
    await message.answer(
        "📄 Введите дату и/или время к которому должна быть выполнена задача. Вы можете ввести условия в свободном виде:"
    )

async def format_task_summary(data: dict) -> str:
    """Форматирует сводку по задаче для подтверждения, получая имена из БД."""

    # Fetch all subjects and task types once to create a mapping
    all_subjects = await get_all_subjects()
    subjects_map = {s['subject_id']: s['subject_name'] for s in all_subjects}

    all_task_types = await get_all_task_types()
    task_types_map = {t['task_type_id']: t['type_name'] for t in all_task_types}

    subject_id = data.get("subject_id")
    subject_name = subjects_map.get(subject_id, f"ID {subject_id}")

    section_id = data.get("section_id")  # Получаем один ID
    sections_data = await get_sections_for_subject(subject_id)
    sections_map = {s['section_id']: s['section_name'] for s in sections_data}
    section_name = sections_map.get(section_id, f"ID {section_id}")  # Находим одно имя

    task_type_id = data.get("task_type_id")  # Получаем один ID
    task_type_name = task_types_map.get(task_type_id, f"ID {task_type_id}")  # Находим одно имя

    solution_format_key = data.get("solution_format")
    solution_formats = {
        "answer_only": "Только ответ",
        "full_solution": "Решение с пояснением",
        "fix_mistakes": "Исправить ошибки"
    }
    solution_format_name = solution_formats.get(solution_format_key, "Не указан")

    file_count = len(data.get("file_ids", []))
    '''Экранирование, чтобы избежать <> в текстах'''
    deadline_text = html.escape(data.get('deadline', 'Не указан'))
    description_text = html.escape(data.get('description', 'Нет описания.'))
    summary = [
        "🔍 Пожалуйста, проверьте детали вашей задачи:\n",
        f"<b>Предмет:</b> {subject_name}",
        f"<b>Разделы:</b> {section_name}",
        f"<b>Тип задачи:</b> {task_type_name}",
        f"<b>Формат решения:</b> {solution_format_name}",
        f"<b>Срок:</b> {deadline_text}",
        "\n<b>Описание:</b>",
        f"<blockquote>{description_text}</blockquote>",
        f"\n<b>Прикреплено файлов:</b> {file_count}"
    ]
    return "\n".join(summary)

async def ask_for_task_confirmation(message: Message, state: FSMContext):
    """Отправляет сводку задачи и запрашивает подтверждение."""
    data = await state.get_data()
    summary_text = await format_task_summary(data)  # Add await here
    await message.answer(
        text=summary_text,
        reply_markup=get_confirmation_keyboard(),
        parse_mode="HTML"
    )
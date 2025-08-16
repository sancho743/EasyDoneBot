from typing import Dict, Union, List
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from service.KeyBoardService import get_subjects_keyboard, get_sections_keyboard, get_task_type_keyboard
from service.RegistrationService import contains_links
from service.DataBaseService import get_all_subjects, get_sections_for_subject, get_all_task_types
# --- Функции для FSM регистрации исполнителя ---

async def ask_for_subjects(target: Union[Message, CallbackQuery], state: FSMContext):
    """Запрашивает у пользователя предметы, которые он хочет выбрать."""
    message = target.message if isinstance(target, CallbackQuery) else target
    current_selected = (await state.get_data()).get("subjects", [])
    keyboard = await get_subjects_keyboard(current_selected)

    text = "📚 Выберите предмет(ы), по которым решаете задачи:"
    try:
        if isinstance(target, CallbackQuery):
            await message.edit_text(text, reply_markup=keyboard)
        else:
            await message.answer(text, reply_markup=keyboard)
    except Exception as e:
        print(f"Ошибка в ask_for_subjects: {e}")
        await message.answer(text, reply_markup=keyboard)


async def ask_for_sections(message: Message, subject_id: int):
    """Запрашивает разделы для выбранного предмета."""
    # В идеале, здесь можно было бы из БД получить и имя предмета
    await message.answer(
        f"📖 Выберите разделы для предмета:",
        reply_markup=await get_sections_keyboard(subject_id)
    )


async def update_subjects_keyboard(callback: CallbackQuery, selected_ids: List[int]):
    """Обновляет клавиатуру с предметами."""
    await callback.message.edit_text(
        "📚 Выберите предмет(ы), по которым решаете задачи:",
        reply_markup=await get_subjects_keyboard(selected_ids)
    )


async def update_sections_keyboard(callback: CallbackQuery, subject_id: int, selected_ids: List[int]):
    """Обновляет клавиатуру с разделами."""
    await callback.message.edit_text(
        f"📖 Выберите разделы для предмета:",
        reply_markup=await get_sections_keyboard(subject_id, selected_ids)
    )


async def update_task_type_keyboard(callback: CallbackQuery, selected_ids: List[int]):
    """Обновляет клавиатуру с типами заказов."""
    await callback.message.edit_text(
        "Выберите типы задач:",
        reply_markup=await get_task_type_keyboard(selected_ids)
    )


async def ask_for_task_type(message: Message, state: FSMContext):
    """Запрашивает типы задач."""
    await message.answer(
        "Выберите типы задач, которые вы выполняете:",
        reply_markup=await get_task_type_keyboard()
    )


async def ask_for_description(message: Message, state: FSMContext):
    """Запрашивает описание деятельности."""
    await message.answer(
        "✏️ Напишите описание вашей деятельности (без ссылок!):\n"
        "Пример: «Решаю задачи по математике для студентов 1-2 курсов»"
    )


async def ask_for_experience(message: Message, state: FSMContext):
    """Запрашивает опыт работы."""
    await message.answer("📆 Укажите ваш опыт работы (в годах или «Нет опыта»):")


async def ask_for_photo(message: Message, state: FSMContext):
    """Запрашивает фото."""
    await message.answer("📷 Прикрепите ваше фото (это повысит доверие клиентов):")


async def ask_for_education(message: Message, state: FSMContext):
    """Запрашивает информацию об образовании."""
    await message.answer(
        "🎓 Укажите ваше образование(например: "
        "\"МГУ, факультет математики, бакалавр/неоконченное высшее\")"
    )


def get_years_form(experience: int) -> str:
    """Возвращает правильную форму слова 'год' для любого числа."""
    if experience % 100 in (11, 12, 13, 14): return "лет"
    last_digit = experience % 10
    if last_digit == 1: return "год"
    if 2 <= last_digit <= 4: return "года"
    return "лет"


async def format_profile_text(data: dict) -> str:
    """Асинхронно форматирует текст профиля исполнителя, получая данные из БД."""

    # 1. Получаем справочники из БД
    all_subjects_data = await get_all_subjects()
    subjects_map = {s['subject_id']: s['subject_name'] for s in all_subjects_data}

    all_task_types_data = await get_all_task_types()
    task_types_map = {t['task_type_id']: t['type_name'] for t in all_task_types_data}

    # 2. Форматируем профиль
    profile_lines = ["✅ Анкета заполнена!", f"👤 Имя: {data.get('name', 'не указано')}", "📚 Предметы:"]

    # 3. Форматируем предметы и разделы
    subject_details = data.get('subject_details', {})
    if subject_details:
        for subject_id_str, section_ids in subject_details.items():
            subject_id = int(subject_id_str)
            subject_name = subjects_map.get(subject_id, f"ID {subject_id}")

            # Получаем разделы для текущего предмета
            sections_data = await get_sections_for_subject(subject_id)
            sections_map = {s['section_id']: s['section_name'] for s in sections_data}
            section_names = [sections_map.get(s_id, f"ID {s_id}") for s_id in section_ids]

            profile_lines.append(f"  - {subject_name}: {', '.join(section_names) if section_names else 'все разделы'}")
    else:
        profile_lines.append("  - Предметы не выбраны")

    # 4. Форматируем типы задач
    task_type_ids = data.get('task_types', [])
    if task_type_ids:
        task_type_names = [task_types_map.get(t_id, f"ID {t_id}") for t_id in task_type_ids]
        profile_lines.append(f"🔧 Типы решаемых задач: {', '.join(task_type_names)}")

    # 5. Добавляем остальную информацию
    profile_lines.extend([
        f"📝 Описание: {data.get('description', 'не указано')}",
        f"🎓 Образование: {data.get('education', 'не указано')}",
        f"⏳ Опыт: {data.get('experience', 0)} {get_years_form(data.get('experience', 0))}"
    ])
    return "\n".join(profile_lines)
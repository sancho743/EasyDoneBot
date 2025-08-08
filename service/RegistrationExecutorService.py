from typing import Dict, Union, List

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from service.RegistrationService import contains_links, get_subjects_keyboard
from utils.constants import SUBJECT_SECTIONS, SUBJECTS, TYPE_OF_TASK

# Временное хранилище данных (позже заменим на БД)
executor_data: Dict[int, Dict] = {}

# --- Основные функции ---
async def ask_for_subjects(
        target: Union[Message, CallbackQuery],
        current_selected: List[str] = None
):
    """Универсальная функция для запроса предметов"""
    message = target.message if isinstance(target, CallbackQuery) else target

    # Получаем клавиатуру
    keyboard = get_subjects_keyboard(current_selected)

    try:
        if isinstance(target, CallbackQuery):
            await message.edit_text(
                "📚 Выберите предмет(ы), по которым решаете задачи:",
                reply_markup=keyboard
            )
        else:
            await message.answer(
                "📚 Выберите предмет(ы), по которым решаете задачи:",
                reply_markup=keyboard
            )
    except Exception as e:
        print(f"Ошибка в ask_for_subjects: {e}")
        await message.answer(
            "📚 Выберите предмет(ы), по которым решаете задачи:",
            reply_markup=keyboard
        )

async def ask_for_sections(
    message: Message,
    subject_id: int,  # Теперь принимаем ID вместо названия
    selected_section_ids: List[int] = None
):
    """Запрос разделов для предмета с использованием ID"""
    if selected_section_ids is None:
        selected_section_ids = []

    builder = InlineKeyboardBuilder()
    sections = SUBJECT_SECTIONS.get(subject_id, {})  # Получаем словарь {id: название}

    # Добавляем кнопки для каждого раздела
    for section_id, section_name in sections.items():
        builder.button(
            text=f"{'✅ ' if section_id in selected_section_ids else ''}{section_name}",
            callback_data=f"sect_{section_id}"  # Формат: sect_<ID_раздела>
        )

    # Кнопка завершения выбора
    builder.button(
        text="✅ Завершить выбор",
        callback_data="sect_done"
    )

    builder.adjust(1)  # По одной кнопке в строке

    try:
        subject_name = SUBJECTS.get(subject_id, "Неизвестный предмет")
        await message.answer(
            f"📖 Выберите разделы для предмета {subject_name}:",
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        print(f"Ошибка при запросе разделов: {e}")
        raise

def get_subjects_keyboard(selected_ids: List[int] = None) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру с предметами на основе ID

    :param selected_ids: Список выбранных ID предметов
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

    builder.button(text="Готово", callback_data="subj_done")
    builder.adjust(1)  # По одному предмету в строке

    return builder.as_markup()


async def update_subjects_keyboard(
        callback: CallbackQuery,
        selected_ids: List[int],
        message_text: str = "📚 Выберите предмет(ы), по которым решаете задачи:"
) -> None:
    """
    Обновляет клавиатуру с предметами (редактирует сообщение)

    :param callback: Объект CallbackQuery
    :param selected_ids: Список выбранных ID предметов
    :param message_text: Текст сообщения (по умолчанию)
    """
    try:
        keyboard = get_subjects_keyboard(selected_ids)
        await callback.message.edit_text(
            text=message_text,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Ошибка при обновлении клавиатуры: {e}")
        # Fallback: отправляем новое сообщение
        await callback.message.answer(
            text=message_text,
            reply_markup=get_subjects_keyboard(selected_ids)
        )

# Функция обновления клавиатуры разделов
async def update_sections_keyboard(
        callback: CallbackQuery,
        subject_id: int,
        selected_ids: List[int],
        message_text: str = None
) -> None:
    """Обновляет клавиатуру с разделами предмета"""
    if message_text is None:
        subject_name = SUBJECTS[subject_id]
        message_text = f"📖 Выберите разделы для предмета {subject_name}:"

    try:
        keyboard = get_sections_keyboard(subject_id, selected_ids)
        await callback.message.edit_text(
            text=message_text,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Ошибка при обновлении клавиатуры разделов: {e}")
        # Fallback: отправляем новое сообщение
        await callback.message.answer(
            text=message_text,
            reply_markup=get_sections_keyboard(subject_id, selected_ids)
        )


# Функция генерации клавиатуры разделов
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

    # Кнопка завершения
    builder.button(
        text="✅ Завершить выбор",
        callback_data="sect_done"
    )

    builder.adjust(1)  # По одному разделу в строке
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


async def update_task_type_keyboard(callback: CallbackQuery, selected_ids: List[int]):
    """Обновляет клавиатуру с типами задач"""
    try:
        keyboard = get_task_type_keyboard(selected_ids)
        await callback.message.edit_text(
            text="Выберите типы задач:",
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Ошибка при обновлении клавиатуры типов задач: {e}")
        await callback.message.answer(
            text="Выберите типы задач:",
            reply_markup=get_task_type_keyboard(selected_ids)
        )

async def ask_for_task_type(message: Message, state: FSMContext):
    """Запрос типов задач"""
    await message.answer(
        "Выберите типы задач, которые вы выполняете:",
        reply_markup=get_task_type_keyboard()
    )

async def ask_for_description(message: Message):
    """Запрос описания деятельности"""
    await message.answer(
        "✏️ Напишите описание вашей деятельности (без ссылок!):\n"
        "Пример: «Решаю задачи по математике для студентов 1-2 курсов»"
    )
async def ask_for_experience(message: Message):
    """Запрос опыта работы"""
    await message.answer(
        "📆 Укажите ваш опыт работы (в годах или «Нет опыта»):"
    )

async def ask_for_photo(message: Message):
    """Запрос фото"""
    await message.answer(
        "📷 Прикрепите ваше фото (это повысит доверие клиентов):"
    )

async def ask_for_education(message: Message):
    """Запрос информации об образовании"""
    await message.answer(
        "🎓 Укажите ваше образование(например: "
        "\"МГУ, факультет математики, бакалавр/неоконченное высшее\")"
    )

async def validate_and_save_data(data: Dict) -> bool:
    """Валидация данных перед сохранением"""
    if not data.get('subjects'):
        return False
    if contains_links(data.get('description', '')):
        return False
    if not data.get('photo'):
        return False
    return True


def get_years_form(experience: int) -> str:
    """Возвращает правильную форму слова 'год' для любого числа"""
    if experience % 100 in (11, 12, 13, 14):
        return "лет"

    last_digit = experience % 10
    if last_digit == 1:
        return "год"
    elif 2 <= last_digit <= 4:
        return "года"
    else:
        return "лет"

def get_solver_main_menu_keyboard():
    """Возвращает клавиатуру основного меню исполнителя"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Мой профиль")],
            [KeyboardButton(text="Мои заказы")],
            [KeyboardButton(text="Написать в поддержку")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )


def format_profile_text(data: dict) -> str:
    profile = [
        "✅ Анкета заполнена!",
        f"👤 Имя: {data.get('name', 'не указано')}",
        f"📝 Описание: {data.get('description', 'не указано')}",
        f"⏳ Опыт: {data.get('experience', 0)} {get_years_form(data.get('experience', 0))}",
        f"🎓 Образование: {data.get('education', 'не указано')}",
        "\n📚 Выбранные предметы и разделы:"
    ]

    # Добавляем типы задач
    task_types_ids = data.get('task_types', [])
    if task_types_ids:
        # Преобразуем ID в названия
        task_types_names = [TYPE_OF_TASK.get(int(tt_id), 'неизвестный тип') for tt_id in task_types_ids]
        profile.append(f"🔧 Типы задач: {', '.join(task_types_names)}")

    profile.append("\n📚 Выбранные предметы и разделы:")

    subject_details = data.get('subject_details', {})
    if not subject_details:
        profile.append("  Предметы не выбраны.")
    else:
        for subject_id_str, section_ids in subject_details.items():  # Assuming subject_id might be string from FSM data key
            try:
                subject_id = int(subject_id_str)  # Convert to int for lookup
            except ValueError:
                profile.append(f"  - Некорректный ID предмета: {subject_id_str}")
                continue

            subject_name = SUBJECTS.get(subject_id, f"Предмет ID {subject_id}")

            section_names = []
            if not section_ids:  # No specific sections selected for this subject
                section_names.append("все разделы")
            else:
                current_subject_sections_map = SUBJECT_SECTIONS.get(subject_id, {})
                for section_id_str in section_ids:  # Assuming section_id might be string
                    try:
                        section_id = int(section_id_str)  # Convert to int for lookup
                    except ValueError:
                        section_names.append(f"Некорректный ID раздела: {section_id_str}")
                        continue
                    section_name = current_subject_sections_map.get(section_id, f"Раздел ID {section_id}")
                    section_names.append(section_name)

            profile.append(f"  - {subject_name}: {', '.join(section_names)}")

    return "\n".join(profile)
import traceback
from pathlib import Path
from typing import List

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder

from service.RegistrationExecutorService import ask_for_subjects, ask_for_description, contains_links, \
    ask_for_experience, ask_for_photo, ask_for_education, get_years_form, get_solver_main_menu_keyboard, \
    format_profile_text, ask_for_sections, SUBJECT_SECTIONS, update_subjects_keyboard, update_sections_keyboard
from utils.constants import SUBJECTS


# Загружаем текст соглашения
BASE_DIR = Path(__file__).parent.parent
PRIVACY_FILE = BASE_DIR / 'utils' / 'privacy_policy.txt'
PRIVACY_TEXT = PRIVACY_FILE.read_text(encoding='utf-8')

# Для исполнителей
executor_router = Router()

class ExecutorStates(StatesGroup):
    WAITING_DESCRIPTION = State()
    WAITING_NAME = State()
    WAITING_EDUCATION = State()
    WAITING_CONSENT = State()
    WAITING_EXPERIENCE = State()
    SELECTING_SUBJECTS = State()
    SELECTING_SECTIONS = State()

@executor_router.callback_query(F.data == "register_as_executor")
async def handle_executor_registration(callback: CallbackQuery, state: FSMContext):
    try:
        await state.set_data({"role": "executor"})
        await state.set_state(ExecutorStates.WAITING_CONSENT)
        print(f"Выбрана роль исполнителя")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принимаю", callback_data="executor_accept")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data="executor_reject")]
        ])

        await callback.message.edit_text(  # Изменяем существующее сообщение
            f"Перед регистрацией необходимо принять соглашение:\n\n{PRIVACY_TEXT}",
            reply_markup=keyboard
        )
        await callback.answer()
    except Exception as e:
        print(f"Ошибка регистрации заказчика: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@executor_router.callback_query(F.data.in_(["executor_accept", "executor_reject"]))
async def handle_privacy_response(callback: CallbackQuery, state: FSMContext):
    if callback.data == "executor_reject":
        await callback.message.answer("❌ Регистрация невозможна без принятия соглашения")
        await state.clear()
        return

    await callback.message.delete()
    await state.set_state(ExecutorStates.WAITING_NAME)
    await callback.message.answer(
        "Как вас зовут?",
        reply_markup=ReplyKeyboardRemove()
    )
    await callback.answer()

# Обработчик выбора предметов
@executor_router.callback_query(F.data.startswith("subj_"))
async def handle_subject_selection(callback: CallbackQuery, state: FSMContext):
    try:
        action = callback.data.split("_")[1]

        if action == "done":
            await handle_subjects_done(callback, state)
            return

        subject_id = int(action)
        data = await state.get_data()
        selected_ids = data.get("subjects", [])

        # Обновляем список выбранных ID
        if subject_id in selected_ids:
            selected_ids.remove(subject_id)
        else:
            selected_ids.append(subject_id)

        await state.update_data(subjects=selected_ids)

        # Обновляем клавиатуру
        await update_subjects_keyboard(callback, selected_ids)
        await callback.answer()

    except Exception as e:
        print(f"Ошибка в handle_subject_selection: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


# Обработчик завершения выбора предметов
@executor_router.callback_query(F.data == "subj_done", ExecutorStates.SELECTING_SUBJECTS)
async def handle_subjects_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("subjects"):
        await callback.answer("Выберите хотя бы один предмет!", show_alert=True)
        return

    try:
        await callback.message.delete()
    except:
        pass

    # Начинаем выбор разделов для первого предмета
    await state.update_data(current_subject_index=0)
    await state.set_state(ExecutorStates.SELECTING_SECTIONS)
    first_subject_id = data["subjects"][0]
    await ask_for_sections(callback.message, first_subject_id)


# Обработчик выбора разделов
@executor_router.callback_query(F.data.regexp(r"^sect_(?!done\b)\d+$"), ExecutorStates.SELECTING_SECTIONS)
async def handle_section_selection(callback: CallbackQuery, state: FSMContext):
    print(f"DEBUG: handle_section_selection triggered with callback_data: {callback.data}")
    try:

        # 1. Логируем входящие данные для диагностики
        print(f"DEBUG: Received callback data: {callback.data}")

        # 2. Парсим callback_data
        parts = callback.data.split('_')
        if len(parts) < 2:
            raise ValueError("Неверный формат callback_data")

        # Обрабатываем обычный выбор раздела
        section_id = int(parts[1])  # Берем только section_id без дополнительных параметров

        # 3. Получаем текущее состояние
        data = await state.get_data()
        print(f"DEBUG: Current state data: {data}")

        # 4. Проверяем наличие необходимых данных
        if "subjects" not in data or not data["subjects"]:
            raise KeyError("Не найдены выбранные предметы")

        current_subject_id = data["subjects"][data["current_subject_index"]]

        # 5. Инициализируем структуру для хранения разделов
        if "subject_details" not in data:
            data["subject_details"] = {}
        if current_subject_id not in data["subject_details"]:
            data["subject_details"][current_subject_id] = []

        selected_ids = data["subject_details"][current_subject_id]

        # 6. Обновляем список выбранных разделов
        if section_id in selected_ids:
            selected_ids.remove(section_id)
            print(f"DEBUG: Раздел {section_id} удален из выбранных")
        else:
            selected_ids.append(section_id)
            print(f"DEBUG: Раздел {section_id} добавлен к выбранным")

        # 7. Сохраняем обновленные данные
        await state.update_data(data)

        # 8. Обновляем интерфейс
        await update_sections_keyboard(callback, current_subject_id, selected_ids)
        await callback.answer()

    except ValueError as ve:
        print(f"Ошибка формата данных: {ve}\nTraceback: {traceback.format_exc()}")
        await callback.answer("Ошибка: неверный формат данных раздела", show_alert=True)
    except KeyError as ke:
        print(f"Ошибка ключа состояния: {ke}\nTraceback: {traceback.format_exc()}")
        await callback.answer("Ошибка: потеряно состояние выбора", show_alert=True)
    except IndexError as ie:
        print(f"Ошибка индекса: {ie}\nTraceback: {traceback.format_exc()}")
        await callback.answer("Ошибка: не найден текущий предмет", show_alert=True)
    except Exception as e:
        print(f"Неожиданная ошибка: {e}\nTraceback: {traceback.format_exc()}")
        await callback.answer("Произошла непредвиденная ошибка", show_alert=True)

# Обработчик завершения выбора разделов
@executor_router.callback_query(F.data == "sect_done", ExecutorStates.SELECTING_SECTIONS)
async def handle_sections_done(callback: CallbackQuery, state: FSMContext):
    print(f"DEBUG: handle_sections_done triggered with callback_data: {callback.data}")
    data = await state.get_data()
    next_index = data["current_subject_index"] + 1

    try:
        await callback.message.delete()
    except:
        pass

    print(f"DEBUG: handle_sections_done: current_subject_index={data.get('current_subject_index')}, next_index={next_index}, num_subjects={len(data.get('subjects', []))}")
    if next_index < len(data["subjects"]):
        # Переходим к следующему предмету
        await state.update_data(current_subject_index=next_index)
        next_subject_id = data["subjects"][next_index]
        print(f"DEBUG: handle_sections_done: Advancing to next subject_id: {data['subjects'][next_index]}")
        await ask_for_sections(callback.message, next_subject_id)
    else:
        # Все разделы выбраны - переходим к описанию
        print("DEBUG: handle_sections_done: All sections selected, moving to WAITING_DESCRIPTION.")
        await state.set_state(ExecutorStates.WAITING_DESCRIPTION)
        await ask_for_description(callback.message,state)

    await callback.answer()

@executor_router.message(ExecutorStates.WAITING_DESCRIPTION)
async def handle_description_input(message: Message, state: FSMContext):
    description = message.text.strip()

    if contains_links(description):
        await message.answer("❌ Описание не может содержать ссылки или контакты")
        return

    await state.update_data(description=description)
    await state.set_state(ExecutorStates.WAITING_EXPERIENCE)

    print("DEBUG: handle_description_input: Description added, moving to WAITING_EXPERIENCE.")
    await ask_for_experience(message, state)
    await state.clear()

@executor_router.message(ExecutorStates.WAITING_NAME)
async def handle_name_input(message: Message, state: FSMContext):
    name = message.text.strip()

    if len(name) < 2:
        await message.answer("❌ Имя слишком короткое. Введите минимум 2 символа")
        return

    if contains_links(name):
        await message.answer("❌ Имя не может содержать ссылки или контакты")
        return

    await state.update_data(name=name)
    await state.set_state(ExecutorStates.SELECTING_SUBJECTS)

    # Вызываем выбор предметов после ввода имени
    await ask_for_subjects(message, state)
    await state.clear()  # Важно очистить состояние

@executor_router.message(ExecutorStates.WAITING_EXPERIENCE)
async def handle_experience_input(message: Message, state: FSMContext):
    experience = int(message.text)
    if experience > 50:
        await message.answer("⚠️ Укажите реальный опыт!")
        return

    years_word = get_years_form(experience)  # Используем универсальный обработчик
    print("DEBUG: handle_experience_input: experience added, moving to WAITING_EDUCATION")
    await state.update_data(experience=experience, years_word=years_word)
    await state.set_state(ExecutorStates.WAITING_EDUCATION)
    await ask_for_education(message, state)
    await state.clear()  # Важно очистить состояние

# Обработчик образования (только при состоянии WAITING_EDUCATION)
@executor_router.message(
    F.text & ~F.text.isdigit(),
    ExecutorStates.WAITING_EDUCATION
)
async def handle_education_input(message: Message, state: FSMContext):
    if contains_links(message.text):
        await message.answer("❌ Описание образования не должно содержать ссылок!")
        return

    await state.update_data(education=message.text)
    await ask_for_photo(message, state)

@executor_router.message(F.photo)
async def handle_photo_upload(message: Message, state: FSMContext):
    try:
        print("Начало обработки фото...")  # Отладочное сообщение
        photo_id = message.photo[-1].file_id
        data = await state.get_data()
        print(f"Данные состояния: {data}")  # Что действительно в состоянии

        # Отправка анкеты
        await message.answer_photo(
            photo=photo_id,
            caption=format_profile_text(data),
            parse_mode="HTML"
        )
        print("Анкета отправлена пользователю")

        # Показ главного меню
        await message.answer(
            "🎉 Регистрация успешно завершена!",
            reply_markup=get_solver_main_menu_keyboard()
        )
        print("Главное меню показано")

        # Здесь будет сохранение в БД
        # await save_executor_profile(data, photo_id)

    except Exception as e:
        print(f"ОШИБКА: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Техническая ошибка при сохранении анкеты. Попробуйте позже.",
        )
    finally:
        await state.clear()

@executor_router.message(F.text == "Мой профиль")
async def handle_profile_request(message: Message):
    # Здесь будет логика показа профиля
    await message.answer("📌 Ваш профиль:", reply_markup=get_solver_main_menu_keyboard())

@executor_router.message(F.text == "Мои заказы")
async def handle_orders_request(message: Message):
    # Здесь будет логика показа заказов
    await message.answer("📦 Ваши текущие заказы:", reply_markup=get_solver_main_menu_keyboard())

@executor_router.message(F.text == "Написать в поддержку")
async def handle_support_request(message: Message):
    # Здесь будет логика обращения в поддержку
    await message.answer("🛟 Напишите ваш вопрос:", reply_markup=get_solver_main_menu_keyboard())
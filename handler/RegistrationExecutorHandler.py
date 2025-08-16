import traceback
from pathlib import Path
from typing import List

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from utils.filters import RoleFilter
from service.MenuService import get_solver_main_menu_keyboard
from service.DataBaseService import update_user_role, save_executor_profile, \
    upload_file_to_storage
from service.RegistrationExecutorService import ask_for_subjects, ask_for_description, contains_links, \
    ask_for_experience, ask_for_photo, ask_for_education, \
    format_profile_text, ask_for_sections, update_subjects_keyboard, update_sections_keyboard, \
    ask_for_task_type, update_task_type_keyboard

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
    SELECTING_TASK_TYPE = State()


@executor_router.callback_query(F.data == "register_as_executor")
async def handle_executor_registration(callback: CallbackQuery, state: FSMContext):
    try:
        await state.set_data({"role": "executor"})
        await state.set_state(ExecutorStates.WAITING_CONSENT)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принимаю", callback_data="executor_accept")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data="executor_reject")]
        ])
        await callback.message.edit_text(
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
    await callback.message.answer("Как вас зовут?", reply_markup=ReplyKeyboardRemove())
    await callback.answer()


@executor_router.callback_query(F.data.startswith("subj_"), ExecutorStates.SELECTING_SUBJECTS)
async def handle_subject_selection(callback: CallbackQuery, state: FSMContext):
    try:
        action = callback.data.split("_")[1]
        if action == "done":
            await handle_subjects_done(callback, state)
            return
        subject_id = int(action)
        data = await state.get_data()
        selected_ids = data.get("subjects", [])
        if subject_id in selected_ids:
            selected_ids.remove(subject_id)
        else:
            selected_ids.append(subject_id)
        await state.update_data(subjects=selected_ids)
        await update_subjects_keyboard(callback, selected_ids)
        await callback.answer()
    except Exception as e:
        print(f"Ошибка в handle_subject_selection: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


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
    await state.update_data(current_subject_index=0)
    await state.set_state(ExecutorStates.SELECTING_SECTIONS)
    first_subject_id = data["subjects"][0]
    await ask_for_sections(callback.message, first_subject_id)


@executor_router.callback_query(F.data.regexp(r"^sect_(?!done\b)\d+$"), ExecutorStates.SELECTING_SECTIONS)
async def handle_section_selection(callback: CallbackQuery, state: FSMContext):
    try:
        section_id = int(callback.data.split("_")[1])
        data = await state.get_data()
        current_subject_id = data["subjects"][data["current_subject_index"]]

        subject_details = data.get("subject_details", {})
        if current_subject_id not in subject_details:
            subject_details[current_subject_id] = []

        selected_ids = subject_details[current_subject_id]
        if section_id in selected_ids:
            selected_ids.remove(section_id)
        else:
            selected_ids.append(section_id)

        await state.update_data(subject_details=subject_details)
        await update_sections_keyboard(callback, current_subject_id, selected_ids)
        await callback.answer()
    except Exception as e:
        print(f"Неожиданная ошибка в handle_section_selection: {e}\nTraceback: {traceback.format_exc()}")
        await callback.answer("Произошла непредвиденная ошибка", show_alert=True)


@executor_router.callback_query(F.data == "sect_done", ExecutorStates.SELECTING_SECTIONS)
async def handle_sections_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    next_index = data.get("current_subject_index", 0) + 1
    if next_index < len(data.get("subjects", [])):
        await state.update_data(current_subject_index=next_index)
        next_subject_id = data["subjects"][next_index]
        await callback.message.delete()
        await ask_for_sections(callback.message, next_subject_id)
    else:
        await callback.message.delete()
        await state.set_state(ExecutorStates.SELECTING_TASK_TYPE)
        await ask_for_task_type(callback.message, state)
    await callback.answer()


@executor_router.callback_query(F.data.startswith("task_type_"), ExecutorStates.SELECTING_TASK_TYPE)
async def handle_task_type_selection(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[2]
    if action == "done":
        await handle_task_type_done(callback, state)
        return
    task_type_id = int(action)
    data = await state.get_data()
    selected_ids = data.get("task_types", [])
    if task_type_id in selected_ids:
        selected_ids.remove(task_type_id)
    else:
        selected_ids.append(task_type_id)
    await state.update_data(task_types=selected_ids)
    await update_task_type_keyboard(callback, selected_ids)
    await callback.answer()


@executor_router.callback_query(F.data == "task_type_done", ExecutorStates.SELECTING_TASK_TYPE)
async def handle_task_type_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("task_types"):
        await callback.answer("Выберите хотя бы один тип задач!", show_alert=True)
        return
    await callback.message.delete()
    await state.set_state(ExecutorStates.WAITING_DESCRIPTION)
    await ask_for_description(callback.message, state)
    await callback.answer()


@executor_router.message(F.text, ExecutorStates.WAITING_DESCRIPTION)
async def handle_description_input(message: Message, state: FSMContext):
    if contains_links(message.text):
        await message.answer("❌ Описание не может содержать ссылки или контакты")
        return
    await state.update_data(description=message.text)
    await state.set_state(ExecutorStates.WAITING_EXPERIENCE)
    await ask_for_experience(message, state)


@executor_router.message(F.text, ExecutorStates.WAITING_NAME)
async def handle_name_input(message: Message, state: FSMContext):
    if contains_links(message.text):
        await message.answer("❌ Имя не может содержать ссылки или контакты")
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(ExecutorStates.SELECTING_SUBJECTS)
    await ask_for_subjects(message, state)


@executor_router.message(F.text, ExecutorStates.WAITING_EXPERIENCE)
async def handle_experience_input(message: Message, state: FSMContext):
    try:
        experience = int(message.text)
    except ValueError:
        await message.answer("⚠️ Пожалуйста, введите число.")
        return
    await state.update_data(experience=experience)
    await state.set_state(ExecutorStates.WAITING_EDUCATION)
    await ask_for_education(message, state)


@executor_router.message(F.text, ExecutorStates.WAITING_EDUCATION)
async def handle_education_input(message: Message, state: FSMContext):
    if contains_links(message.text):
        await message.answer("❌ Описание образования не должно содержать ссылок!")
        return
    await state.update_data(education=message.text)
    await ask_for_photo(message, state)


@executor_router.message(F.photo, ExecutorStates.WAITING_EDUCATION)
async def handle_photo_upload(message: Message, state: FSMContext, bot: Bot):
    try:

        file_id = message.photo[-1].file_id
        user_id = message.from_user.id

        # Upload file and get public URL
        public_photo_url = await upload_file_to_storage(bot=bot, file_id=file_id, user_id=user_id, folder='executor_profile_avatars')

        if not public_photo_url:
            await message.answer("❌ Не удалось загрузить фото. Попробуйте еще раз.")
            return

        data = await state.get_data()
        data['photo_url'] = public_photo_url  # Save URL instead of file_id

        # Save user role and profile to DB
        await update_user_role(user_id=user_id, username=message.from_user.username, role='executor')
        await save_executor_profile(user_id=user_id, data=data)

        # Display profile to user
        profile_caption = await format_profile_text(data)
        await message.answer_photo(
            photo=file_id,  # Show the original photo back to the user
            caption=profile_caption,
            parse_mode="HTML"
        )
        await message.answer("🎉 Регистрация успешно завершена!", reply_markup=get_solver_main_menu_keyboard())
    except Exception as e:
        print(f"ОШИБКА в handle_photo_upload: {str(e)}", exc_info=True)
        await message.answer("❌ Техническая ошибка при сохранении анкеты. Попробуйте позже.")
    finally:
        await state.clear()

@executor_router.message(F.text == "Мой профиль", RoleFilter("executor"))
async def handle_profile_request(message: Message):
    await message.answer("📌 Ваш профиль:", reply_markup=get_solver_main_menu_keyboard())


@executor_router.message(F.text == "Мои заказы", RoleFilter("executor"))
async def handle_orders_request(message: Message):
    await message.answer("📦 Ваши текущие заказы:", reply_markup=get_solver_main_menu_keyboard())


@executor_router.message(F.text == "Написать в поддержку", RoleFilter("executor"))
async def handle_support_request(message: Message):
    await message.answer("🛟 Напишите ваш вопрос:", reply_markup=get_solver_main_menu_keyboard())
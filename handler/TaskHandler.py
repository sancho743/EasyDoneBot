from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from service.RegistrationExecutorService import update_sections_keyboard, update_task_type_keyboard
from service.TaskService import ask_for_task_subject, ask_for_task_sections, ask_for_task_type, \
    ask_for_solution_format

task_router = Router()

class TaskCreationStates(StatesGroup):
    SELECTING_SUBJECT = State()
    SELECTING_SECTIONS = State()
    ENTERING_DESCRIPTION = State()
    SELECTING_TASK_TYPE = State()
    SELECTING_SOLUTION_FORMAT = State()
    UPLOADING_FILES = State()
    CONFIRMING_CREATION = State()


@task_router.message(F.text == "Создать задачу")
async def handle_create_task(message: Message, state: FSMContext):
    await state.set_state(TaskCreationStates.SELECTING_SUBJECT)
    await state.set_data({})
    await ask_for_task_subject(message, state)


@task_router.callback_query(F.data.startswith("subj_"), TaskCreationStates.SELECTING_SUBJECT)
async def handle_subject_selection_for_task(callback: CallbackQuery, state: FSMContext):
    subject_id = int(callback.data.split("_")[1])
    await state.update_data(subject_id=subject_id)
    await state.set_state(TaskCreationStates.SELECTING_SECTIONS)
    await ask_for_task_sections(callback.message, state, subject_id)
    await callback.answer()


@task_router.callback_query(F.data.startswith("sect_"), TaskCreationStates.SELECTING_SECTIONS)
async def handle_section_selection_for_task(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    if action == "done":
        await handle_sections_done_for_task(callback, state)
        return
    section_id = int(action)
    data = await state.get_data()
    selected_ids = data.get("section_ids", [])
    if section_id in selected_ids:
        selected_ids.remove(section_id)
    else:
        selected_ids.append(section_id)
    await state.update_data(section_ids=selected_ids)
    subject_id = data.get("subject_id")
    await update_sections_keyboard(callback, subject_id, selected_ids)
    await callback.answer()

@task_router.callback_query(F.data == "sect_done", TaskCreationStates.SELECTING_SECTIONS)
async def handle_sections_done_for_task(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("section_ids"):
        await callback.answer("Пожалуйста, выберите хотя бы один раздел.", show_alert=True)
        return
    await state.set_state(TaskCreationStates.ENTERING_DESCRIPTION)
    await callback.message.delete()
    await callback.message.answer("📝 Теперь введите подробное описание вашей задачи.")
    await callback.answer()

@task_router.message(TaskCreationStates.ENTERING_DESCRIPTION)
async def handle_description_for_task(message: Message, state: FSMContext):
    print(f"DEBUG: TaskHandler state is {await state.get_state()}")
    await state.update_data(description=message.text)
    await state.set_state(TaskCreationStates.SELECTING_TASK_TYPE)
    await ask_for_task_type(message, state)


@task_router.callback_query(F.data.startswith("task_type_"), TaskCreationStates.SELECTING_TASK_TYPE)
async def handle_task_type_selection_for_task(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[2]
    if action == "done":
        await handle_task_type_done_for_task(callback, state)
        return
    task_type_id = int(action)
    data = await state.get_data()
    selected_ids = data.get("task_type_ids", [])
    if task_type_id in selected_ids:
        selected_ids.remove(task_type_id)
    else:
        selected_ids.append(task_type_id)
    await state.update_data(task_type_ids=selected_ids)
    await update_task_type_keyboard(callback, selected_ids)
    await callback.answer()

@task_router.callback_query(F.data == "task_type_done", TaskCreationStates.SELECTING_TASK_TYPE)
async def handle_task_type_done_for_task(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("task_type_ids"):
        await callback.answer("Пожалуйста, выберите хотя бы один тип.", show_alert=True)
        return
    await state.set_state(TaskCreationStates.SELECTING_SOLUTION_FORMAT)
    await callback.message.delete()
    await ask_for_solution_format(callback.message, state)
    await callback.answer()

@task_router.callback_query(F.data.startswith("sol_format_"), TaskCreationStates.SELECTING_SOLUTION_FORMAT)
async def handle_solution_format_selection(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор формата решения и переходит к загрузке файлов."""
    solution_format = callback.data.split("sol_format_")[1]
    await state.update_data(solution_format=solution_format)
    await state.set_state(TaskCreationStates.UPLOADING_FILES)

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ Готово", callback_data="files_done"))

    await callback.message.edit_text(
        "📎 Теперь прикрепите файлы с заданием (фото или документы). "
        "Отправьте все файлы, а затем нажмите 'Готово'.",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@task_router.message(F.content_type.in_({'photo', 'document'}), TaskCreationStates.UPLOADING_FILES)
async def handle_file_upload(message: Message, state: FSMContext):
    """Ловит фото и документы, сохраняет их file_id."""
    file_id = ""
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        file_id = message.document.file_id

    data = await state.get_data()
    file_ids = data.get("file_ids", [])
    file_ids.append(file_id)
    await state.update_data(file_ids=file_ids)

    await message.reply("✅ Файл добавлен. Можете добавить еще или нажать 'Готово'.")


@task_router.callback_query(F.data == "files_done", TaskCreationStates.UPLOADING_FILES)
async def handle_files_done(callback: CallbackQuery, state: FSMContext):
    """Завершает загрузку файлов и переходит к подтверждению."""
    data = await state.get_data()
    if not data.get("file_ids"):
        await callback.answer("Пожалуйста, прикрепите хотя бы один файл.", show_alert=True)
        return

    await state.set_state(TaskCreationStates.CONFIRMING_CREATION)
    await callback.message.delete()
    # Placeholder for the next step
    await callback.message.answer("Файлы загружены. Теперь шаг подтверждения.")
    await callback.answer()

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from service.MenuService import get_customer_main_menu_keyboard
from service.TaskService import ask_for_task_subject, ask_for_task_sections, ask_for_task_type, ask_for_solution_format, \
    ask_for_task_confirmation, ask_for_deadline
from service.DataBaseService import save_task, update_task_attachments, upload_file_to_storage

task_router = Router()


class TaskCreationStates(StatesGroup):
    SELECTING_SUBJECT = State()
    SELECTING_SECTION = State()
    ENTERING_DESCRIPTION = State()
    SELECTING_TASK_TYPE = State()
    SELECTING_SOLUTION_FORMAT = State()
    UPLOADING_FILES = State()
    CONFIRMING_CREATION = State()
    ENTERING_DEADLINE = State()

@task_router.message(F.text == "Создать задачу")
async def handle_create_task(message: Message, state: FSMContext):
    """Starts the task creation flow."""
    await state.set_state(TaskCreationStates.SELECTING_SUBJECT)
    await state.set_data({})
    await ask_for_task_subject(message)


@task_router.callback_query(F.data.startswith("subj_"), TaskCreationStates.SELECTING_SUBJECT)
async def handle_subject_selection_for_task(callback: CallbackQuery, state: FSMContext):
    """Handles subject selection and asks for section."""
    subject_id = int(callback.data.split("_")[1])
    await state.update_data(subject_id=subject_id)
    await state.set_state(TaskCreationStates.SELECTING_SECTION)
    await ask_for_task_sections(callback.message, subject_id)
    await callback.answer()


@task_router.callback_query(F.data.startswith("sect_"), TaskCreationStates.SELECTING_SECTION)
async def handle_section_selection_for_task(callback: CallbackQuery, state: FSMContext):
    """Handles single section selection and moves to description."""
    section_id = int(callback.data.split("_")[1])
    await state.update_data(section_id=section_id)
    await state.set_state(TaskCreationStates.ENTERING_DESCRIPTION)
    await callback.message.delete()
    await callback.message.answer("📝 Теперь введите подробное описание вашей задачи.")
    await callback.answer()


@task_router.message(F.text, TaskCreationStates.ENTERING_DESCRIPTION)
async def handle_description_for_task(message: Message, state: FSMContext):
    """Handles description input and asks for task type."""
    await state.update_data(description=message.text)
    await state.set_state(TaskCreationStates.SELECTING_TASK_TYPE)
    await ask_for_task_type(message)


@task_router.callback_query(F.data.startswith("task_type_"), TaskCreationStates.SELECTING_TASK_TYPE)
async def handle_task_type_selection_for_task(callback: CallbackQuery, state: FSMContext):
    """Handles single task type selection and moves to solution format."""
    task_type_id = int(callback.data.split("_")[2])
    await state.update_data(task_type_id=task_type_id)
    await state.set_state(TaskCreationStates.SELECTING_SOLUTION_FORMAT)
    await callback.message.delete()
    await ask_for_solution_format(callback.message)
    await callback.answer()


@task_router.callback_query(F.data.startswith("sol_format_"), TaskCreationStates.SELECTING_SOLUTION_FORMAT)
async def handle_solution_format_selection(callback: CallbackQuery, state: FSMContext):
    """Handles solution format selection and asks for files."""
    solution_format = callback.data.split("sol_format_")[1]
    await state.update_data(solution_format=solution_format)
    await state.set_state(TaskCreationStates.ENTERING_DEADLINE)
    await callback.message.delete()
    await ask_for_deadline(callback.message)
    await callback.answer()

@task_router.message(F.text, TaskCreationStates.ENTERING_DEADLINE)
async def handle_deadline_input(message: Message, state: FSMContext):
    await state.update_data(deadline=message.text)
    await state.set_state(TaskCreationStates.UPLOADING_FILES)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ Готово", callback_data="files_done"))
    await message.answer(
        "📎 Теперь прикрепите файлы с заданием (фото или документы). "
        "Отправьте все файлы, а затем нажмите 'Готово'.",
        reply_markup=builder.as_markup()
    )


@task_router.message(F.content_type.in_({'photo', 'document'}), TaskCreationStates.UPLOADING_FILES)
async def handle_file_upload(message: Message, state: FSMContext):
    """Catches photos/documents and saves their file_id."""
    file_id = message.photo[-1].file_id if message.photo else message.document.file_id
    data = await state.get_data()
    file_ids = data.get("file_ids", [])
    file_ids.append(file_id)
    await state.update_data(file_ids=file_ids)

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ Готово", callback_data="files_done"))
    await message.reply(
        "✅ Файл добавлен. Можете добавить еще или нажать 'Готово'.",
        reply_markup=builder.as_markup()
    )


@task_router.callback_query(F.data == "files_done", TaskCreationStates.UPLOADING_FILES)
async def handle_files_done(callback: CallbackQuery, state: FSMContext):
    """Moves to the confirmation step after files are selected."""
    await state.set_state(TaskCreationStates.CONFIRMING_CREATION)
    await callback.message.delete()
    await ask_for_task_confirmation(callback.message, state)
    await callback.answer()


@task_router.callback_query(F.data == "confirm_task_creation", TaskCreationStates.CONFIRMING_CREATION)
async def handle_task_confirmation_positive(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Saves task, uploads files with the new task_id, and updates the task with file URLs."""
    try:
        await callback.message.edit_text("⏳ Сохраняю вашу задачу...")
        data = await state.get_data()
        user_id = callback.from_user.id

        # 1. Save task without attachments to get a task_id
        new_task = await save_task(user_id=user_id, data=data)
        if not new_task or 'task_id' not in new_task:
            raise Exception("Failed to create task entry in database.")

        task_id = new_task['task_id']

        # 2. Upload files using the task_id for the path
        file_ids = data.get("file_ids", [])
        if file_ids:
            await callback.message.edit_text(f"⏳ Загружаю файлы для задачи #{task_id}...")
            attachment_urls = []
            for file_id in file_ids:
                url = await upload_file_to_storage(
                    bot=bot,
                    file_id=file_id,
                    user_id=user_id,
                    folder=f"tasks/{task_id}"  # Unique path
                )
                if url:
                    attachment_urls.append(url)

            # 3. Update the task with the attachment URLs
            if attachment_urls:
                await update_task_attachments(task_id, attachment_urls)

        await state.clear()
        await callback.message.edit_text(f"✅ Ваша задача #{task_id} успешно создана! Исполнители скоро откликнутся.")
        await callback.message.answer("Главное меню:", reply_markup=get_customer_main_menu_keyboard())

    except Exception as e:
        await callback.message.edit_text("❌ Произошла ошибка при сохранении задачи. Попробуйте снова.")
        print(f"Error on task confirmation: {e}")
    finally:
        await callback.answer()


@task_router.callback_query(F.data == "cancel_task_creation", TaskCreationStates.CONFIRMING_CREATION)
async def handle_task_confirmation_negative(callback: CallbackQuery, state: FSMContext):
    """Cancels task creation."""
    await state.clear()
    await callback.message.edit_text("❌ Создание задачи отменено.")
    await callback.answer()
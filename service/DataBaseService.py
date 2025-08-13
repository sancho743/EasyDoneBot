from aiogram import Bot
from aiogram.client.session import aiohttp
from supabase import create_client, Client
from utils.config import DATABASE_URL, API_DATABASE_KEY

# Инициализация клиента Supabase
supabase: Client = create_client(DATABASE_URL, API_DATABASE_KEY)

# --- Функции для работы с пользователями ---
# Важно: предполагается, что у вас есть таблица `users`
# со столбцами `user_id` (тип int8, Primary Key) и `role` (тип text).

async def update_user_role(user_id: int, username: str, role: str):
    """Добавляет/обновляет роль пользователя."""
    try:
        supabase.table('users').upsert({
            'user_id': user_id,
            'username': username,
            'role': role
        }).execute()
    except Exception as e:
        print(f"Error updating user role for {user_id}: {e}")

async def get_user_role(user_id: int) -> str | None:
    """Получает роль пользователя из базы данных."""
    try:
        response = supabase.table('users').select('role').eq('user_id', user_id).execute()
        if response.data:
            return response.data[0].get('role')
        return None
    except Exception as e:
        print(f"Error getting user role for {user_id}: {e}")
        return None
# --- Функции для получения справочных данных ---

async def get_all_subjects():
    """Получает все предметы из БД."""
    try:
        response = supabase.table('subject').select('subject_id, subject_name').execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error getting all subjects: {e}")
        return []

async def get_all_task_types():
    """Получает все типы задач из БД."""
    try:
        response = supabase.table('task_type').select('task_type_id, type_name').execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error getting all task types: {e}")
        return []

async def get_sections_for_subject(subject_id: int):
    """Получает все разделы для конкретного предмета."""
    try:
        response = supabase.table('section').select('section_id, section_name').eq('subject_id', subject_id).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error getting sections for subject {subject_id}: {e}")
        return []


async def save_executor_profile(user_id: int, data: dict):
    """Сохраняет полный профиль исполнителя в базу данных."""
    try:
        profile_data = {
            'user_id': user_id,
            'executor_name': data.get('name'),
            'description': data.get('description'),
            'experience': data.get('experience'),
            'education': data.get('education'),
            'photo_url': data.get('photo_id'),
            'personal_data_access': True
        }
        profile_response = supabase.table('executor').upsert(profile_data, on_conflict='user_id').execute()
        if not profile_response.data:
            raise Exception("Failed to create or update executor profile.")
        executor_id = profile_response.data[0]['executor_id']

        subject_ids = data.get('subjects', [])
        if subject_ids:
            subject_rows = [{'executor_id': executor_id, 'subject_id': sub_id} for sub_id in subject_ids]
            supabase.table('executor_subject').delete().eq('executor_id', executor_id).execute()
            supabase.table('executor_subject').insert(subject_rows).execute()

        task_type_ids = data.get('task_types', [])
        if task_type_ids:
            task_type_rows = [{'executor_id': executor_id, 'task_type_id': tt_id} for tt_id in task_type_ids]
            supabase.table('executor_task_type').delete().eq('executor_id', executor_id).execute()
            supabase.table('executor_task_type').insert(task_type_rows).execute()
    except Exception as e:
        print(f"Error saving full executor profile for {user_id}: {e}")

async def save_customer_profile(user_id: int, data: dict):
    """Сохраняет профиль заказчика в базу данных."""
    try:
        profile_data = {
            'user_id': user_id,
            'customer_name': data.get('name'),
            'personal_data_access': True
        }
        supabase.table('customer').upsert(profile_data, on_conflict='user_id').execute()
    except Exception as e:
        print(f"Error saving customer profile for {user_id}: {e}")

async def upload_file_to_storage(bot: Bot, file_id: str, user_id: int) -> str|None:
    try:
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.telegram.org/file/bot{bot.token}/{file_path}") as response:
                if response.status != 200:
                    print(f"Error downloading file: {response.status}")
                    return None
                file_content = await response.read()
        bucket_name = "storage"  # Как вы и указали
        upload_path = f"executor_profile_avatars/{user_id}/{file_id}.jpg"

        supabase.storage.from_(bucket_name).upload(upload_path, file_content)

        public_url_response = supabase.storage.from_(bucket_name).get_public_url(upload_path)
        return public_url_response

    except Exception as e:
        print(f"Error uploading file to storage for user {user_id}: {e}")
        return None


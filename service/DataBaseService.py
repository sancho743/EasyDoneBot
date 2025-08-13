from supabase import create_client, Client
from utils.config import DATABASE_URL, API_DATABASE_KEY

# Инициализация клиента Supabase
supabase: Client = create_client(DATABASE_URL, API_DATABASE_KEY)

# --- Функции для работы с пользователями ---
# Важно: предполагается, что у вас есть таблица `users`
# со столбцами `user_id` (тип int8, Primary Key) и `role` (тип text).

async def update_user_role(user_id: int, role: str):
    """Добавляет/обновляет роль пользователя."""
    try:
        supabase.table('users').upsert({
            'user_id': user_id,
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

async def update_username(user_id: int, username: str):
    """Добавляет/обновляет никнейм пользователя в ТГ."""
    try:
        supabase.table('users').upsert({
            'user_id': user_id,
            'username': username
        }).execute()
    except Exception as e:
        print(f"Error updating username role for {user_id}: {e}")
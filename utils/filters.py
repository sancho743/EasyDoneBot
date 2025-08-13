from aiogram.filters import Filter
from aiogram.types import Message
from service.DataBaseService import get_user_role

class RoleFilter(Filter):
    def __init__(self, role: str):
        self.role = role

    async def __call__(self, message: Message) -> bool:
        user_role_from_db = await get_user_role(message.from_user.id) # <--- Получаем роль из БД
        return user_role_from_db == self.role # <--- Сравниваем
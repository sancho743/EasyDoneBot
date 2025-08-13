from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from service.MenuService import get_customer_main_menu_keyboard, get_solver_main_menu_keyboard
from service.DataBaseService import get_user_role

class RoleCheckMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        # We only care about text messages that are commands
        if not isinstance(event, Message) or not event.text or not event.text.startswith('/'):
            return await handler(event, data)
        # Check if the command is /start
        if event.text.split()[0] == '/start':
            user_id = event.from_user.id
            role = await get_user_role(user_id)
            if role:
                if role == 'customer':
                    await event.answer(f"👋 С возвращением, заказчик!", reply_markup=get_customer_main_menu_keyboard())
                elif role == 'executor':
                    await event.answer(f"👋 С возвращением, исполнитель!", reply_markup=get_solver_main_menu_keyboard())
                # If we handled the /start command, we don't want it to be processed further.
                # So we just return and don't call the handler.
                return None
        # For any other command or for new users, continue to the original handlers
        return await handler(event, data)
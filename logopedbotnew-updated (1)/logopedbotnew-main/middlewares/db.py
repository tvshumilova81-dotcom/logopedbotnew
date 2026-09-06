from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from database.engine import async_session_maker


class DbSessionMiddleware(BaseMiddleware):
    """Открывает асинхронную сессию SQLAlchemy на каждое обновление."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with async_session_maker() as session:
            data["session"] = session
            return await handler(event, data)

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

logger = logging.getLogger("bot.errors")


class ErrorLoggingMiddleware(BaseMiddleware):
    """Ловит необработанные исключения в хендлерах и пишет их в лог,
    не давая боту упасть целиком."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception:  # noqa: BLE001
            logger.exception("Необработанная ошибка при обработке события: %r", event)
            return None

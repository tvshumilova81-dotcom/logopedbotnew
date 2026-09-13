from aiogram import Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from config.settings import settings

router = Router(name="admin_webapp")


@router.message(Command("panel"))
async def open_admin_panel(message: Message) -> None:
    """Открывает админ-панель мини-приложения (календарь, записи, доход).

    Важно: web_app-кнопка внутри InlineKeyboardMarkup открывается только если
    сообщение отправлено самому боту в личном чате (это ограничение Telegram).
    """
    if not settings.use_webhook:
        await message.answer(
            "Мини-приложение недоступно: не задан публичный адрес (WEBHOOK_URL) в настройках бота."
        )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="🗓 Открыть панель администратора",
                web_app=WebAppInfo(url=settings.webapp_admin_url),
            )
        ]]
    )
    await message.answer(
        "Панель администратора: календарь, записи и доход.",
        reply_markup=keyboard,
    )

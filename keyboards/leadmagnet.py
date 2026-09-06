from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def diagnostic_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Записаться на диагностику", callback_data="diagnostic:book")
    builder.adjust(1)
    return builder.as_markup()

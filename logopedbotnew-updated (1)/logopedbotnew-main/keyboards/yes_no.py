from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

YES = "✅ Да"
NO = "❌ Нет"
PARTIALLY = "🤔 Частично"


def yes_no_partially_keyboard(prefix: str = "ans") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=YES, callback_data=f"{prefix}:yes")
    builder.button(text=NO, callback_data=f"{prefix}:no")
    builder.button(text=PARTIALLY, callback_data=f"{prefix}:partially")
    builder.adjust(3)
    return builder.as_markup()


def yes_no_keyboard(prefix: str = "ans") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=YES, callback_data=f"{prefix}:yes")
    builder.button(text=NO, callback_data=f"{prefix}:no")
    builder.adjust(2)
    return builder.as_markup()


ANSWER_LABELS = {
    "yes": "✅ Да",
    "no": "❌ Нет",
    "partially": "🤔 Частично",
}

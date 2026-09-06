from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def booking_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить запись", callback_data="booking_confirm:yes")
    builder.button(text="✏️ Начать заново", callback_data="booking_confirm:restart")
    builder.adjust(1)
    return builder.as_markup()


def gender_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👦 Мальчик", callback_data="gender:boy")
    builder.button(text="👧 Девочка", callback_data="gender:girl")
    builder.adjust(2)
    return builder.as_markup()

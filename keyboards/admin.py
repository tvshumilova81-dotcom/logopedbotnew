from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def booking_notification_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Принято", callback_data=f"booking_accept:{booking_id}")
    builder.button(text="📋 Открыть анкету", callback_data=f"booking_open_q:{booking_id}")
    builder.button(text="👤 Профиль пользователя", callback_data=f"booking_profile:{booking_id}")
    builder.button(text="🗑 Удалить заявку", callback_data=f"booking_delete:{booking_id}")
    builder.adjust(1)
    return builder.as_markup()


def questionnaire_notification_keyboard(questionnaire_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📄 Посмотреть анкету", callback_data=f"q_view:{questionnaire_id}")
    builder.adjust(1)
    return builder.as_markup()


def admin_materials_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить материал", callback_data="admatl:add")
    builder.button(text="✏️ Изменить материал", callback_data="admatl:edit")
    builder.button(text="🗑 Удалить материал", callback_data="admatl:delete")
    builder.button(text="📊 Статистика продаж", callback_data="admatl:stats")
    builder.adjust(1)
    return builder.as_markup()


def broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Отправить всем", callback_data="broadcast:confirm")
    builder.button(text="❌ Отменить", callback_data="broadcast:cancel")
    builder.adjust(1)
    return builder.as_markup()

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from config.settings import settings

MENU_BOOKING = "📝 Записаться на занятие"
MENU_ONLINE_BOOKING = "🗓 Онлайн-запись"
MENU_QUESTIONNAIRE = "📋 Анкета ребёнка"
MENU_ABOUT = "👩‍🏫 Обо мне"
MENU_MATERIALS = "📚 Полезные материалы"
MENU_FAQ = "❓ Частые вопросы"
MENU_PURCHASES = "💎 Мои покупки"
MENU_PROFILE = "👤 Мой профиль"
MENU_CONTACTS = "📩 Контакты"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    booking_row = [KeyboardButton(text=MENU_BOOKING)]
    # Кнопка мини-приложения (календарь со свободными слотами) появляется,
    # только когда задан публичный HTTPS-адрес (settings.WEBHOOK_URL) —
    # Telegram не разрешает web_app-кнопки без https-домена.
    if settings.use_webhook:
        booking_row.append(
            KeyboardButton(
                text=MENU_ONLINE_BOOKING,
                web_app=WebAppInfo(url=settings.webapp_client_url),
            )
        )

    keyboard = [
        booking_row,
        [KeyboardButton(text=MENU_QUESTIONNAIRE)],
        [KeyboardButton(text=MENU_ABOUT), KeyboardButton(text=MENU_MATERIALS)],
        [KeyboardButton(text=MENU_FAQ), KeyboardButton(text=MENU_PURCHASES)],
        [KeyboardButton(text=MENU_PROFILE), KeyboardButton(text=MENU_CONTACTS)],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from config.settings import settings

MENU_BOOKING = "📝 Записаться на занятие"
MENU_MINIAPP = "🗓 Мини-приложение (запись)"
MENU_QUESTIONNAIRE = "📋 Анкета ребёнка"
MENU_ABOUT = "👩‍🏫 Обо мне"
MENU_MATERIALS = "📚 Полезные материалы"
MENU_FAQ = "❓ Частые вопросы"
MENU_PURCHASES = "💎 Мои покупки"
MENU_PROFILE = "👤 Мой профиль"
MENU_CONTACTS = "📩 Контакты"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = []

    if settings.WEBAPP_URL:
        keyboard.append(
            [KeyboardButton(text=MENU_MINIAPP, web_app=WebAppInfo(url=settings.WEBAPP_URL))]
        )

    keyboard += [
        [KeyboardButton(text=MENU_BOOKING)],
        [KeyboardButton(text=MENU_QUESTIONNAIRE)],
        [KeyboardButton(text=MENU_ABOUT), KeyboardButton(text=MENU_MATERIALS)],
        [KeyboardButton(text=MENU_FAQ), KeyboardButton(text=MENU_PURCHASES)],
        [KeyboardButton(text=MENU_PROFILE), KeyboardButton(text=MENU_CONTACTS)],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

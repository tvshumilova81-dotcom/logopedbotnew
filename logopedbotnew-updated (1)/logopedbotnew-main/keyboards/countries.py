from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

COUNTRIES = [
    "🇩🇪 Германия", "🇫🇷 Франция", "🇮🇹 Италия", "🇪🇸 Испания",
    "🇵🇱 Польша", "🇨🇿 Чехия", "🇳🇱 Нидерланды", "🇧🇪 Бельгия",
    "🇨🇭 Швейцария", "🇬🇧 Великобритания", "🇸🇪 Швеция", "🇫🇮 Финляндия",
    "🇳🇴 Норвегия", "🇩🇰 Дания", "🇺🇸 США", "🇨🇦 Канада",
    "🇦🇪 ОАЭ", "🇶🇦 Катар", "🇮🇱 Израиль", "🇷🇺 Россия",
    "🇰🇿 Казахстан", "🇧🇾 Беларусь", "🇦🇲 Армения", "🇦🇿 Азербайджан",
    "🇰🇬 Кыргызстан", "🇺🇿 Узбекистан", "🇹🇯 Таджикистан", "🇲🇩 Молдова",
    "🇱🇻 Латвия", "🇱🇹 Литва", "🇪🇪 Эстония",
]
OTHER_COUNTRY = "🌍 Другая страна"


def countries_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, country in enumerate(COUNTRIES):
        builder.button(text=country, callback_data=f"country:{i}")
    builder.button(text=OTHER_COUNTRY, callback_data="country:other")
    builder.adjust(2)
    return builder.as_markup()


def country_by_index(index: int) -> str | None:
    if 0 <= index < len(COUNTRIES):
        return COUNTRIES[index]
    return None

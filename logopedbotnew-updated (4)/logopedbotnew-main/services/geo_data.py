from __future__ import annotations

# Список стран для мини-приложения: код, эмодзи-флаг, название, подпись часового пояса.
# Порядок совпадает с порядком показа в UI (популярные страны — сверху).
COUNTRIES: list[dict[str, str]] = [
    {"code": "RU", "flag": "🇷🇺", "name": "Россия", "tz_label": "UTC+3 (Москва)"},
    {"code": "KZ", "flag": "🇰🇿", "name": "Казахстан", "tz_label": "UTC+5 (Астана)"},
    {"code": "BY", "flag": "🇧🇾", "name": "Беларусь", "tz_label": "UTC+3 (Минск)"},
    {"code": "US", "flag": "🇺🇸", "name": "США", "tz_label": "UTC-5 (Нью-Йорк)"},
    {"code": "DE", "flag": "🇩🇪", "name": "Германия", "tz_label": "UTC+1 (Берлин)"},
    {"code": "TR", "flag": "🇹🇷", "name": "Турция", "tz_label": "UTC+3 (Стамбул)"},
    {"code": "AE", "flag": "🇦🇪", "name": "ОАЭ", "tz_label": "UTC+4 (Дубай)"},
    {"code": "GB", "flag": "🇬🇧", "name": "Великобритания", "tz_label": "UTC+1 (Лондон)"},
    {"code": "FR", "flag": "🇫🇷", "name": "Франция", "tz_label": "UTC+1 (Париж)"},
    {"code": "ES", "flag": "🇪🇸", "name": "Испания", "tz_label": "UTC+2 (Мадрид)"},
    {"code": "IT", "flag": "🇮🇹", "name": "Италия", "tz_label": "UTC+1 (Рим)"},
    {"code": "PL", "flag": "🇵🇱", "name": "Польша", "tz_label": "UTC+1 (Варшава)"},
    {"code": "CZ", "flag": "🇨🇿", "name": "Чехия", "tz_label": "UTC+1 (Прага)"},
    {"code": "SE", "flag": "🇸🇪", "name": "Швеция", "tz_label": "UTC+1 (Стокгольм)"},
    {"code": "NL", "flag": "🇳🇱", "name": "Нидерланды", "tz_label": "UTC+1 (Амстердам)"},
    {"code": "CH", "flag": "🇨🇭", "name": "Швейцария", "tz_label": "UTC+1 (Цюрих)"},
    {"code": "CA", "flag": "🇨🇦", "name": "Канада", "tz_label": "UTC-5 (Торонто)"},
    {"code": "QA", "flag": "🇶🇦", "name": "Катар", "tz_label": "UTC+3 (Доха)"},
    {"code": "IL", "flag": "🇮🇱", "name": "Израиль", "tz_label": "UTC+2 (Тель-Авив)"},
    {"code": "AM", "flag": "🇦🇲", "name": "Армения", "tz_label": "UTC+4 (Ереван)"},
    {"code": "AZ", "flag": "🇦🇿", "name": "Азербайджан", "tz_label": "UTC+4 (Баку)"},
    {"code": "UZ", "flag": "🇺🇿", "name": "Узбекистан", "tz_label": "UTC+5 (Ташкент)"},
    {"code": "MD", "flag": "🇲🇩", "name": "Молдова", "tz_label": "UTC+2 (Кишинёв)"},
    {"code": "LV", "flag": "🇱🇻", "name": "Латвия", "tz_label": "UTC+2 (Рига)"},
    {"code": "LT", "flag": "🇱🇹", "name": "Литва", "tz_label": "UTC+2 (Вильнюс)"},
    {"code": "EE", "flag": "🇪🇪", "name": "Эстония", "tz_label": "UTC+2 (Таллин)"},
]

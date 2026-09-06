from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models.material import Material


def materials_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📖 Бесплатные материалы", callback_data="materials:free")
    builder.button(text="⭐️ Платные материалы", callback_data="materials:paid")
    builder.adjust(1)
    return builder.as_markup()


def free_articles_keyboard(articles: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    """articles: list of (slug, title)"""
    builder = InlineKeyboardBuilder()
    for slug, title in articles:
        builder.button(text=title, callback_data=f"article:{slug}")
    builder.button(text="⬅️ Назад", callback_data="materials:back")
    builder.adjust(1)
    return builder.as_markup()


def paid_materials_keyboard(materials: list[Material], purchased_ids: set[int]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for m in materials:
        mark = "✅ " if m.id in purchased_ids else ""
        builder.button(text=f"{mark}{m.title}", callback_data=f"material:{m.id}")
    builder.button(text="⬅️ Назад", callback_data="materials:back")
    builder.adjust(1)
    return builder.as_markup()


def material_card_keyboard(material: Material, already_purchased: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if already_purchased:
        builder.button(text="📂 Открыть материал", callback_data=f"material_open:{material.id}")
    else:
        builder.button(
            text=f"⭐️ Купить за {material.price_stars} Stars",
            callback_data=f"material_buy:{material.id}",
        )
    builder.button(text="⬅️ Назад", callback_data="materials:paid")
    builder.adjust(1)
    return builder.as_markup()


def purchases_keyboard(materials: list[Material]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for m in materials:
        builder.button(text=f"📂 {m.title}", callback_data=f"material_open:{m.id}")
    builder.adjust(1)
    return builder.as_markup()

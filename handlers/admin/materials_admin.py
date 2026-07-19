from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import MATERIALS_DIR
from filters.admin import IsAdmin
from keyboards.admin import admin_materials_menu_keyboard
from services.material_service import (
    create_material,
    delete_material,
    list_active_materials,
    sales_stats,
)
from states.admin import MaterialAdminForm

router = Router(name="admin_materials")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.message(Command("materials_admin"))
async def materials_admin_menu(message: Message) -> None:
    await message.answer(
        "📚 <b>Управление материалами</b>\n\nВыберите действие:",
        reply_markup=admin_materials_menu_keyboard(),
    )


@router.callback_query(F.data == "admatl:add")
async def add_material_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(MaterialAdminForm.title)
    await callback.message.answer("Введите название нового материала:")
    await callback.answer()


@router.message(MaterialAdminForm.title)
async def add_material_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text)
    await state.set_state(MaterialAdminForm.description)
    await message.answer("Введите описание материала:")


@router.message(MaterialAdminForm.description)
async def add_material_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text)
    await state.set_state(MaterialAdminForm.price)
    await message.answer("Введите стоимость в Telegram Stars (только число):")


@router.message(MaterialAdminForm.price)
async def add_material_price(message: Message, state: FSMContext) -> None:
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите число, например: 50")
        return
    await state.update_data(price=int(message.text))
    await state.set_state(MaterialAdminForm.file)
    await message.answer("Пришлите файл материала (документ: PDF, DOCX и т.п.):")


@router.message(MaterialAdminForm.file, F.document)
async def add_material_file(message: Message, state: FSMContext) -> None:
    document = message.document
    dest_path = MATERIALS_DIR / document.file_name
    await message.bot.download(document, destination=dest_path)
    await state.update_data(file_path=str(dest_path))
    await state.set_state(MaterialAdminForm.cover)
    await message.answer(
        "Пришлите обложку материала (фото) или отправьте /skip, чтобы пропустить."
    )


@router.message(MaterialAdminForm.file)
async def add_material_file_invalid(message: Message) -> None:
    await message.answer("Пожалуйста, пришлите файл как документ.")


@router.message(MaterialAdminForm.cover, F.photo)
async def add_material_cover(message: Message, state: FSMContext) -> None:
    photo = message.photo[-1]
    dest_path = MATERIALS_DIR.parent / "covers" / f"{photo.file_id}.jpg"
    await message.bot.download(photo, destination=dest_path)
    await state.update_data(cover_path=str(dest_path))
    await _confirm_new_material(message, state)


@router.message(MaterialAdminForm.cover, F.text == "/skip")
async def add_material_cover_skip(message: Message, state: FSMContext) -> None:
    await _confirm_new_material(message, state)


async def _confirm_new_material(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    text = (
        "Проверьте данные нового материала:\n\n"
        f"Название: {data['title']}\n"
        f"Описание: {data['description']}\n"
        f"Цена: {data['price']} ⭐️\n\n"
        "Отправьте /confirm чтобы сохранить или /cancel чтобы отменить."
    )
    await state.set_state(MaterialAdminForm.confirm)
    await message.answer(text)


@router.message(MaterialAdminForm.confirm, F.text == "/confirm")
async def save_new_material(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    slug = data["title"].lower().replace(" ", "_")[:64]
    await create_material(
        session,
        slug=slug,
        title=data["title"],
        description=data["description"],
        price_stars=data["price"],
        file_path=data["file_path"],
        cover_path=data.get("cover_path"),
        is_active=True,
    )
    await message.answer("✅ Материал добавлен и уже доступен в каталоге.")
    await state.clear()


@router.message(MaterialAdminForm.confirm, F.text == "/cancel")
async def cancel_new_material(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Добавление материала отменено.")


@router.callback_query(F.data == "admatl:delete")
async def delete_material_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    materials = await list_active_materials(session)
    if not materials:
        await callback.message.answer("Нет активных материалов.")
        await callback.answer()
        return

    builder = InlineKeyboardBuilder()
    for m in materials:
        builder.button(text=f"🗑 {m.title}", callback_data=f"admatl_del:{m.id}")
    builder.adjust(1)
    await callback.message.answer("Выберите материал для удаления:", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admatl_del:"))
async def confirm_delete_material(callback: CallbackQuery, session: AsyncSession) -> None:
    material_id = int(callback.data.split(":", 1)[1])
    await delete_material(session, material_id)
    await callback.message.answer("🗑 Материал удалён (скрыт из каталога).")
    await callback.answer()


@router.callback_query(F.data == "admatl:stats")
async def show_sales_stats(callback: CallbackQuery, session: AsyncSession) -> None:
    stats = await sales_stats(session)
    if not stats:
        await callback.message.answer("Продаж пока не было.")
    else:
        lines = [f"• {title}: {count} шт., {stars} ⭐️" for title, count, stars in stats]
        await callback.message.answer("📊 <b>Статистика продаж</b>\n\n" + "\n".join(lines))
    await callback.answer()


@router.callback_query(F.data == "admatl:edit")
async def edit_material_notice(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "Для редактирования материала — удалите его через «🗑 Удалить материал» "
        "и добавьте заново через «➕ Добавить материал» с обновлёнными данными."
    )
    await callback.answer()

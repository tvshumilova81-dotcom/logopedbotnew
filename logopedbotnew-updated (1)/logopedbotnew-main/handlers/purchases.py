from pathlib import Path

from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.main_menu import MENU_PURCHASES
from keyboards.materials import purchases_keyboard
from services.material_service import get_material, user_purchases
from services.user_service import get_user_by_telegram_id

router = Router(name="purchases")


@router.message(F.text == MENU_PURCHASES)
async def show_purchases(message: Message, session: AsyncSession) -> None:
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Сначала отправьте /start")
        return
    materials = await user_purchases(session, user.id)
    if not materials:
        await message.answer(
            "У вас пока нет купленных материалов.\n\n"
            "Загляните в раздел «📚 Полезные материалы» — там есть полезные "
            "бесплатные статьи и материалы за Telegram Stars."
        )
        return
    await message.answer(
        "💎 <b>Мои покупки</b>\n\nНажмите на материал, чтобы открыть его снова:",
        reply_markup=purchases_keyboard(materials),
    )


@router.callback_query(F.data.startswith("material_open:"))
async def open_purchased_material(callback: CallbackQuery, session: AsyncSession) -> None:
    material_id = int(callback.data.split(":", 1)[1])
    material = await get_material(session, material_id)
    if not material:
        await callback.answer("Материал не найден", show_alert=True)
        return

    path = Path(material.file_path)
    if not path.exists():
        await callback.message.answer(
            "⚠️ Не удалось найти файл. Напишите мне в Instagram или Telegram-канал — "
            "пришлю материал вручную."
        )
    else:
        await callback.message.answer_document(
            FSInputFile(path), caption=f"📚 {material.title}"
        )
    await callback.answer()

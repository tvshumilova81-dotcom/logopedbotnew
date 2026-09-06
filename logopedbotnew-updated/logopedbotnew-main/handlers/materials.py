from pathlib import Path

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import MATERIALS_DIR
from keyboards.main_menu import MENU_MATERIALS
from keyboards.materials import (
    free_articles_keyboard,
    material_card_keyboard,
    materials_menu_keyboard,
    paid_materials_keyboard,
)
from services.article_service import get_article, list_articles
from services.material_service import (
    create_purchase,
    get_material,
    has_purchased,
    list_active_materials,
    user_purchased_material_ids,
)
from services.notify_admin import notify_new_purchase
from services.user_service import get_user_by_telegram_id

router = Router(name="materials")

NAIDI_PARU_FREE_PATH = MATERIALS_DIR / "naidi_paru_free.pdf"


@router.message(F.text == MENU_MATERIALS)
async def show_materials_menu(message: Message) -> None:
    await message.answer(
        "📚 <b>Полезные материалы</b>\n\n"
        "Выберите раздел:",
        reply_markup=materials_menu_keyboard(),
    )


@router.callback_query(F.data == "materials:back")
async def back_to_materials(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "📚 <b>Полезные материалы</b>\n\nВыберите раздел:",
        reply_markup=materials_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "materials:free")
async def show_free_materials(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "📖 <b>Бесплатные материалы</b>\n\nВыберите статью:",
        reply_markup=free_articles_keyboard(list_articles()),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("article:"))
async def open_article(callback: CallbackQuery) -> None:
    slug = callback.data.split(":", 1)[1]

    if slug == "naidi_paru":
        await callback.answer()
        if NAIDI_PARU_FREE_PATH.exists():
            await callback.message.answer_document(
                FSInputFile(NAIDI_PARU_FREE_PATH),
                caption="🎲 Бонус-игра «Найди пару» — бесплатный материал от Татьяны Шумиловой.",
            )
        else:
            await callback.message.answer("Материал временно недоступен, попробуйте позже.")
        return

    article = get_article(slug)
    if not article:
        await callback.answer("Статья не найдена", show_alert=True)
        return
    await callback.message.answer(f"📖 <b>{article.title.split(' ', 1)[-1]}</b>\n\n{article.content}")
    await callback.answer()


@router.callback_query(F.data == "materials:paid")
async def show_paid_materials(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    materials = await list_active_materials(session)
    purchased = await user_purchased_material_ids(session, user.id) if user else set()
    await callback.message.edit_text(
        "⭐️ <b>Платные материалы</b>\n\nОплата через Telegram Stars.",
        reply_markup=paid_materials_keyboard(materials, purchased),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("material:"))
async def open_material_card(callback: CallbackQuery, session: AsyncSession) -> None:
    material_id = int(callback.data.split(":", 1)[1])
    material = await get_material(session, material_id)
    if not material:
        await callback.answer("Материал не найден", show_alert=True)
        return
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    already = await has_purchased(session, user.id, material.id) if user else False

    text = f"⭐️ <b>{material.title}</b>\n\n{material.description}"
    if not already:
        text += f"\n\nСтоимость: ⭐️ {material.price_stars} Telegram Stars"
    await callback.message.edit_text(text, reply_markup=material_card_keyboard(material, already))
    await callback.answer()


@router.callback_query(F.data.startswith("material_buy:"))
async def buy_material(callback: CallbackQuery, session: AsyncSession) -> None:
    material_id = int(callback.data.split(":", 1)[1])
    material = await get_material(session, material_id)
    if not material:
        await callback.answer("Материал не найден", show_alert=True)
        return

    await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title=material.title,
        description=material.description[:255],
        payload=f"material:{material.id}",
        currency="XTR",
        prices=[LabeledPrice(label=material.title, amount=material.price_stars)],
    )
    await callback.answer()


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery) -> None:
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message, session: AsyncSession) -> None:
    payload = message.successful_payment.invoice_payload
    if not payload.startswith("material:"):
        return
    material_id = int(payload.split(":", 1)[1])
    material = await get_material(session, material_id)
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not material or not user:
        await message.answer(
            "Оплата прошла, но материал не найден. Пожалуйста, напишите мне в "
            "Instagram или Telegram-канал — я решу вопрос вручную."
        )
        return

    await create_purchase(
        session,
        user_id=user.id,
        material_id=material.id,
        price_stars=material.price_stars,
        charge_id=message.successful_payment.telegram_payment_charge_id,
    )

    await message.answer(f"✅ Оплата прошла успешно! Материал «{material.title}» теперь ваш.")
    await send_material_file(message, material)
    await notify_new_purchase(message.bot, user, material)


async def send_material_file(message: Message, material) -> None:
    path = Path(material.file_path)
    if not path.exists():
        await message.answer(
            "⚠️ Не удалось отправить файл автоматически. Пожалуйста, напишите мне в "
            "Instagram или Telegram-канал — я отправлю материал вручную."
        )
        return
    try:
        await message.answer_document(
            FSInputFile(path),
            caption=f"📚 {material.title}\n\nМатериал сохранён в разделе «💎 Мои покупки».",
        )
    except Exception:
        await message.answer(
            "⚠️ Не удалось отправить файл. Попробуйте открыть его позже в разделе "
            "«💎 Мои покупки» или напишите в Instagram / Telegram-канал."
        )

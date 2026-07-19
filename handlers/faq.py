from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.main_menu import MENU_FAQ
from services.faq_service import load_faq

router = Router(name="faq")


def faq_keyboard():
    builder = InlineKeyboardBuilder()
    for i, item in enumerate(load_faq()):
        builder.button(text=item["question"], callback_data=f"faq:{i}")
    builder.adjust(1)
    return builder.as_markup()


@router.message(F.text == MENU_FAQ)
async def show_faq(message: Message) -> None:
    await message.answer(
        "❓ <b>Частые вопросы</b>\n\nВыберите вопрос:", reply_markup=faq_keyboard()
    )


@router.callback_query(F.data.startswith("faq:"))
async def answer_faq(callback: CallbackQuery) -> None:
    index = int(callback.data.split(":", 1)[1])
    faq = load_faq()
    if index >= len(faq):
        await callback.answer("Вопрос не найден", show_alert=True)
        return
    item = faq[index]
    await callback.message.answer(f"❓ <b>{item['question']}</b>\n\n{item['answer']}")
    await callback.answer()

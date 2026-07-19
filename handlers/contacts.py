from aiogram import F, Router
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config.settings import settings
from keyboards.main_menu import MENU_CONTACTS

router = Router(name="contacts")


@router.message(F.text == MENU_CONTACTS)
async def show_contacts(message: Message) -> None:
    builder = InlineKeyboardBuilder()
    builder.button(text="📷 Instagram", url="https://www.instagram.com/tatyana.logopedworld?igsh=b2tqMDJoZXZnZzZw&utm_source=qr")
    builder.button(text="📢 Telegram-канал", url="https://t.me/logopedonlinetatiyana")
    builder.adjust(1)
    await message.answer(
        "📩 <b>Контакты</b>\n\n"
        "Буду рада видеть вас в моих соцсетях — там я делюсь полезными "
        "материалами и отвечаю на вопросы:",
        reply_markup=builder.as_markup(),
    )

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import MATERIALS_DIR
from handlers.booking import start_booking
from keyboards.leadmagnet import diagnostic_keyboard
from services.notify_admin import notify_diagnostic_click, notify_lead_magnet_download
from services.user_service import get_or_create_user

router = Router(name="leadmagnet")

# === Лид-магнит: чек-лист "Проверьте речь ребёнка за 7 минут" ===
LEAD_MAGNET_PATH = MATERIALS_DIR / "rech_za_7_minut.pdf"

# Кодовые слова (регистр не важен, лишние пробелы по краям допустимы)
HOCHU_WORDS = {"хочу"}
DIAGNOSTIC_WORDS = {"диагностика"}


def _is_exact_word(message: Message, words: set[str]) -> bool:
    if not message.text:
        return False
    return message.text.strip().lower() in words


@router.message(lambda message: _is_exact_word(message, HOCHU_WORDS))
async def send_lead_magnet(message: Message, session: AsyncSession) -> None:
    user = await get_or_create_user(session, message.from_user)

    if not LEAD_MAGNET_PATH.exists():
        await message.answer(
            "Материал временно недоступен, попробуйте немного позже 🙏"
        )
        return

    await message.answer_document(
        FSInputFile(LEAD_MAGNET_PATH),
        caption=(
            "📄 <b>Проверьте речь ребёнка за 7 минут</b>\n\n"
            "Бесплатный чек-лист для родителей — держите!\n\n"
            "Если хотите разобраться, что делать дальше, напишите слово "
            "«<b>Диагностика</b>» — расскажу про первое занятие."
        ),
    )
    await notify_lead_magnet_download(message.bot, user)


# === Кодовое слово "Диагностика" — запись на первое занятие ===

DIAGNOSTIC_TEXT = (
    "🩺 <b>Диагностика речи — первое занятие</b>\n\n"
    "Познакомимся с ребёнком, посмотрим его речевые навыки, определим "
    "основные трудности и обсудим дальнейшие шаги.\n\n"
    "💰 <b>Стоимость:</b>\n"
    "🇷🇺 Россия и СНГ — 1200 ₽\n"
    "🌍 США, ОАЭ, Европа и другие страны — от 45 $\n\n"
    "Точная стоимость для вашей страны будет названа при записи.\n\n"
    "Нажмите кнопку ниже, чтобы записаться 👇"
)


@router.message(lambda message: _is_exact_word(message, DIAGNOSTIC_WORDS))
async def diagnostic_info(message: Message, session: AsyncSession) -> None:
    user = await get_or_create_user(session, message.from_user)
    await message.answer(DIAGNOSTIC_TEXT, reply_markup=diagnostic_keyboard())
    await notify_diagnostic_click(message.bot, user)


@router.callback_query(F.data == "diagnostic:book")
async def diagnostic_book(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_reply_markup()
    await start_booking(callback.message, state)
    await callback.answer()

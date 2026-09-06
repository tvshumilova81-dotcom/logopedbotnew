from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.main_menu import main_menu_keyboard
from services.user_service import get_or_create_user

router = Router(name="start")

WELCOME_TEXT = (
    "Здравствуйте! 👋\n\n"
    "Меня зовут <b>Татьяна Шумилова</b>.\n"
    "Я детский логопед и педагог.\n\n"
    "Добро пожаловать!\n\n"
    "В этом боте вы сможете:\n"
    "📝 записаться на онлайн-занятия;\n"
    "📋 заполнить анкету ребёнка;\n"
    "📚 получить полезные материалы;\n"
    "⭐️ приобрести обучающие статьи и чек-листы;\n"
    "❓ узнать ответы на популярные вопросы;\n"
    "👩‍🏫 познакомиться со мной и моим опытом.\n\n"
    "Выберите нужный раздел в меню."
)


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    await get_or_create_user(session, message.from_user)
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard())

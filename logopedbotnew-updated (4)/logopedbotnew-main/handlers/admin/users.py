from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from filters.admin import IsAdmin
from services.booking_service import latest_booking_for_user
from services.user_service import all_users, search_users
from states.admin import UserSearchForm

router = Router(name="admin_users")
router.message.filter(IsAdmin())

PAGE_SIZE = 15


def _format_user_line(user, booking) -> str:
    status = booking.status.value if booking else "—"
    return (
        f"👤 {user.parent_name or user.username or '—'} "
        f"(👶 {user.child_name or '—'}, 🌍 {user.country or '—'}, "
        f"📅 {user.created_at.strftime('%d.%m.%Y')}, статус: {status}) — ID {user.telegram_id}"
    )


@router.message(Command("users"))
async def list_users(message: Message, session: AsyncSession) -> None:
    users = await all_users(session)
    if not users:
        await message.answer("Пользователей пока нет.")
        return
    lines = []
    for u in users[:PAGE_SIZE]:
        booking = await latest_booking_for_user(session, u.id)
        lines.append(_format_user_line(u, booking))
    text = f"👥 <b>Пользователи</b> (показано {len(lines)} из {len(users)})\n\n" + "\n\n".join(lines)
    text += "\n\nДля поиска используйте команду /find <имя или ID>"
    await message.answer(text)


@router.message(Command("find"))
async def find_user(message: Message, session: AsyncSession) -> None:
    query = message.text.partition(" ")[2].strip()
    if not query:
        await message.answer("Использование: /find <имя, username или Telegram ID>")
        return
    users = await search_users(session, query)
    if not users:
        await message.answer("Никого не найдено.")
        return
    lines = []
    for u in users:
        booking = await latest_booking_for_user(session, u.id)
        lines.append(_format_user_line(u, booking))
    await message.answer("🔎 <b>Результаты поиска</b>\n\n" + "\n\n".join(lines))

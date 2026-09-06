from collections import Counter
from datetime import datetime, timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from filters.admin import IsAdmin
from services.booking_service import count_bookings
from services.material_service import sales_stats, total_revenue, total_sold
from services.questionnaire_service import count_completed
from services.user_service import all_users

router = Router(name="admin_stats")
router.message.filter(IsAdmin())


@router.message(Command("stats"))
async def show_stats(message: Message, session: AsyncSession) -> None:
    users = await all_users(session)
    total_users = len(users)
    bookings_count = await count_bookings(session)
    questionnaires_count = await count_completed(session)
    sold = await total_sold(session)
    revenue = await total_revenue(session)

    today = datetime.utcnow().date()
    month_ago = today - timedelta(days=30)
    new_today = sum(1 for u in users if u.created_at.date() == today)
    new_month = sum(1 for u in users if u.created_at.date() >= month_ago)

    countries = Counter(u.country for u in users if u.country)
    countries_text = "\n".join(f"  • {c}: {n}" for c, n in countries.most_common(10)) or "  —"

    text = (
        "📊 <b>Статистика</b>\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"📝 Всего заявок: {bookings_count}\n"
        f"📋 Заполнено анкет: {questionnaires_count}\n"
        f"⭐️ Продано материалов: {sold}\n"
        f"💰 Доход в Telegram Stars: {revenue}\n"
        f"📅 Новых пользователей за сегодня: {new_today}\n"
        f"📈 Новых пользователей за месяц: {new_month}\n\n"
        f"🌍 <b>По странам (топ-10):</b>\n{countries_text}"
    )
    await message.answer(text)


@router.message(Command("sales"))
async def show_sales(message: Message, session: AsyncSession) -> None:
    stats = await sales_stats(session)
    if not stats:
        await message.answer("Продаж пока не было.")
        return
    lines = [f"• {title}: {count} шт., {stars} ⭐️" for title, count, stars in stats]
    await message.answer("📊 <b>Статистика продаж</b>\n\n" + "\n".join(lines))

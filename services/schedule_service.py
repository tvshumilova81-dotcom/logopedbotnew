from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.schedule import (
    IncomeEntry,
    IncomeSource,
    LessonBooking,
    LessonStatus,
    ScheduleBlock,
)
from database.models.user import User

# Рабочие часы логопеда. Поменяйте здесь, если график другой.
WORK_HOURS = ["09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00", "18:00"]

DEFAULT_SESSION_PRICE = 2500


async def get_month_slots(session: AsyncSession, year: int, month: int) -> dict:
    """Возвращает статус каждого часа каждого дня месяца:
    'free' | 'booked' | 'blocked'. Без имён клиентов — это для клиентского календаря.
    """
    start = date(year, month, 1)
    end = date(year + (1 if month == 12 else 0), 1 if month == 12 else month + 1, 1)

    blocks = (await session.execute(
        select(ScheduleBlock).where(ScheduleBlock.date >= start, ScheduleBlock.date < end)
    )).scalars().all()
    bookings = (await session.execute(
        select(LessonBooking).where(
            LessonBooking.date >= start,
            LessonBooking.date < end,
            LessonBooking.status != LessonStatus.CANCELLED,
        )
    )).scalars().all()

    blocked_set = {(b.date.isoformat(), b.time) for b in blocks}
    booked_set = {(b.date.isoformat(), b.time) for b in bookings}

    result: dict[str, dict[str, str]] = {}
    d = start
    while d < end:
        day_key = d.isoformat()
        result[day_key] = {}
        for h in WORK_HOURS:
            if (day_key, h) in blocked_set:
                result[day_key][h] = "blocked"
            elif (day_key, h) in booked_set:
                result[day_key][h] = "booked"
            else:
                result[day_key][h] = "free"
        d += timedelta(days=1)
    return result


async def is_slot_free(session: AsyncSession, lesson_date: date, time_str: str) -> bool:
    blocked = (await session.execute(
        select(ScheduleBlock).where(ScheduleBlock.date == lesson_date, ScheduleBlock.time == time_str)
    )).scalar_one_or_none()
    if blocked:
        return False
    booked = (await session.execute(
        select(LessonBooking).where(
            LessonBooking.date == lesson_date,
            LessonBooking.time == time_str,
            LessonBooking.status != LessonStatus.CANCELLED,
        )
    )).scalar_one_or_none()
    return booked is None


async def create_booking(
    session: AsyncSession,
    user: User,
    lesson_date: date,
    time_str: str,
    topic: Optional[str],
    country: Optional[str],
    timezone: Optional[str],
    price_rub: int = DEFAULT_SESSION_PRICE,
) -> LessonBooking:
    if not await is_slot_free(session, lesson_date, time_str):
        raise ValueError("slot_taken")

    booking = LessonBooking(
        user_id=user.id,
        date=lesson_date,
        time=time_str,
        topic=topic,
        country=country,
        timezone=timezone,
        price_rub=price_rub,
        status=LessonStatus.CONFIRMED,
    )
    session.add(booking)
    await session.commit()
    await session.refresh(booking)
    return booking


async def user_bookings(session: AsyncSession, user: User) -> list[LessonBooking]:
    result = await session.execute(
        select(LessonBooking).where(LessonBooking.user_id == user.id).order_by(LessonBooking.date.desc())
    )
    return list(result.scalars().all())


async def cancel_booking(session: AsyncSession, booking_id: int) -> Optional[LessonBooking]:
    booking = await session.get(LessonBooking, booking_id)
    if booking is None:
        return None
    booking.status = LessonStatus.CANCELLED
    await session.execute(delete(IncomeEntry).where(IncomeEntry.lesson_booking_id == booking.id))
    await session.commit()
    return booking


async def block_slot(session: AsyncSession, d: date, time_str: str, reason: Optional[str] = None) -> None:
    exists = (await session.execute(
        select(ScheduleBlock).where(ScheduleBlock.date == d, ScheduleBlock.time == time_str)
    )).scalar_one_or_none()
    if exists:
        return
    session.add(ScheduleBlock(date=d, time=time_str, reason=reason))
    await session.commit()


async def unblock_slot(session: AsyncSession, d: date, time_str: str) -> None:
    await session.execute(
        delete(ScheduleBlock).where(ScheduleBlock.date == d, ScheduleBlock.time == time_str)
    )
    await session.commit()


async def all_bookings(session: AsyncSession, upcoming_only: bool = False) -> list[LessonBooking]:
    stmt = select(LessonBooking).options(selectinload(LessonBooking.user)).order_by(LessonBooking.date.desc())
    if upcoming_only:
        stmt = select(LessonBooking).options(selectinload(LessonBooking.user)).where(
            LessonBooking.date >= date.today(), LessonBooking.status == LessonStatus.CONFIRMED
        ).order_by(LessonBooking.date.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


# ---------------------- Доход ----------------------

async def add_income_for_booking(session: AsyncSession, booking: LessonBooking) -> IncomeEntry:
    entry = IncomeEntry(
        date=booking.date,
        amount=booking.price_rub,
        note=f"Занятие: {booking.topic or ''}".strip(),
        source=IncomeSource.BOOKING,
        lesson_booking_id=booking.id,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


async def add_manual_income(session: AsyncSession, d: date, amount: int, note: str) -> IncomeEntry:
    entry = IncomeEntry(date=d, amount=amount, note=note, source=IncomeSource.MANUAL)
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


async def update_income(session: AsyncSession, entry_id: int, amount: int) -> Optional[IncomeEntry]:
    entry = await session.get(IncomeEntry, entry_id)
    if entry is None:
        return None
    entry.amount = amount
    await session.commit()
    return entry


async def delete_income(session: AsyncSession, entry_id: int) -> None:
    await session.execute(delete(IncomeEntry).where(IncomeEntry.id == entry_id))
    await session.commit()


async def list_income(session: AsyncSession) -> list[IncomeEntry]:
    result = await session.execute(select(IncomeEntry).order_by(IncomeEntry.date.desc()))
    return list(result.scalars().all())

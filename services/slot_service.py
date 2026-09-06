from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.slot import BookingStatus, MiniAppBooking, SlotStatus, TimeSlot

# Шаблон рабочей недели: понедельник(0) ... воскресенье(6).
# По умолчанию — Пн-Сб с перерывом на обед в 13:00, воскресенье выходной.
WEEKLY_TEMPLATE: dict[int, list[str]] = {
    0: ["10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00", "18:00"],
    1: ["10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00", "18:00"],
    2: ["10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00", "18:00"],
    3: ["10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00", "18:00"],
    4: ["10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00", "18:00"],
    5: ["10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00", "18:00"],
    6: [],
}

GENERATE_DAYS_AHEAD = 60


async def ensure_slots_generated(session: AsyncSession, days_ahead: int = GENERATE_DAYS_AHEAD) -> None:
    """Создаёт недостающие тайм-слоты на ближайшие days_ahead дней по шаблону недели."""
    today = date.today()
    existing = await session.execute(
        select(TimeSlot.date, TimeSlot.time).where(
            TimeSlot.date >= today.isoformat(),
            TimeSlot.date <= (today + timedelta(days=days_ahead)).isoformat(),
        )
    )
    existing_pairs = {(row.date, row.time) for row in existing}

    to_create: list[TimeSlot] = []
    for offset in range(days_ahead + 1):
        d = today + timedelta(days=offset)
        times = WEEKLY_TEMPLATE.get(d.weekday(), [])
        for t in times:
            if (d.isoformat(), t) not in existing_pairs:
                to_create.append(TimeSlot(date=d.isoformat(), time=t, status=SlotStatus.FREE))

    if to_create:
        session.add_all(to_create)
        await session.commit()


async def get_slots_for_month(session: AsyncSession, year: int, month: int) -> list[TimeSlot]:
    prefix = f"{year:04d}-{month:02d}"
    result = await session.execute(
        select(TimeSlot).where(TimeSlot.date.like(f"{prefix}%")).order_by(TimeSlot.date, TimeSlot.time)
    )
    return list(result.scalars().all())


async def get_slots_for_date(session: AsyncSession, date_str: str) -> list[TimeSlot]:
    result = await session.execute(
        select(TimeSlot).where(TimeSlot.date == date_str).order_by(TimeSlot.time)
    )
    return list(result.scalars().all())


async def get_slot(session: AsyncSession, date_str: str, time_str: str) -> TimeSlot | None:
    result = await session.execute(
        select(TimeSlot).where(TimeSlot.date == date_str, TimeSlot.time == time_str)
    )
    return result.scalar_one_or_none()


async def toggle_block(session: AsyncSession, date_str: str, time_str: str) -> TimeSlot | None:
    """Переключает слот между 'свободен' и 'закрыт админом'. Занятые клиентом слоты не трогает."""
    slot = await get_slot(session, date_str, time_str)
    if slot is None:
        slot = TimeSlot(date=date_str, time=time_str, status=SlotStatus.BLOCKED)
        session.add(slot)
        await session.commit()
        await session.refresh(slot)
        return slot

    if slot.status == SlotStatus.BOOKED:
        return slot  # нельзя просто заблокировать занятый слот — сначала нужно отменить запись

    slot.status = SlotStatus.FREE if slot.status == SlotStatus.BLOCKED else SlotStatus.BLOCKED
    await session.commit()
    return slot


async def book_slot(
    session: AsyncSession,
    *,
    user_id: int,
    date_str: str,
    time_str: str,
    country: str | None,
    timezone: str | None,
    topic: str | None,
    price: int = 0,
) -> MiniAppBooking | None:
    """Бронирует слот, если он свободен. Возвращает None, если слот уже занят/закрыт."""
    slot = await get_slot(session, date_str, time_str)
    if slot is None:
        slot = TimeSlot(date=date_str, time=time_str, status=SlotStatus.FREE)
        session.add(slot)
        await session.flush()

    if slot.status != SlotStatus.FREE:
        return None

    booking = MiniAppBooking(
        user_id=user_id,
        date=date_str,
        time=time_str,
        country=country,
        timezone=timezone,
        topic=topic,
        price=price,
        status=BookingStatus.CONFIRMED,
    )
    session.add(booking)
    await session.flush()

    slot.status = SlotStatus.BOOKED
    slot.booking_id = booking.id
    await session.commit()
    await session.refresh(booking)
    return booking


async def cancel_booking(session: AsyncSession, booking_id: int) -> bool:
    booking = await session.get(MiniAppBooking, booking_id)
    if booking is None:
        return False
    booking.status = BookingStatus.CANCELLED
    result = await session.execute(select(TimeSlot).where(TimeSlot.booking_id == booking_id))
    slot = result.scalar_one_or_none()
    if slot is not None:
        slot.status = SlotStatus.FREE
        slot.booking_id = None
    await session.commit()
    return True


async def get_user_bookings(session: AsyncSession, user_id: int) -> list[MiniAppBooking]:
    result = await session.execute(
        select(MiniAppBooking)
        .where(MiniAppBooking.user_id == user_id)
        .order_by(MiniAppBooking.date.desc(), MiniAppBooking.time.desc())
    )
    return list(result.scalars().all())


async def get_bookings_for_date(session: AsyncSession, date_str: str) -> list[MiniAppBooking]:
    result = await session.execute(
        select(MiniAppBooking)
        .where(MiniAppBooking.date == date_str, MiniAppBooking.status != BookingStatus.CANCELLED)
        .order_by(MiniAppBooking.time)
    )
    return list(result.scalars().all())


def split_upcoming_past(bookings: list[MiniAppBooking]) -> tuple[list[MiniAppBooking], list[MiniAppBooking]]:
    now = datetime.now()
    upcoming, past = [], []
    for b in bookings:
        try:
            dt = datetime.strptime(f"{b.date} {b.time}", "%Y-%m-%d %H:%M")
        except ValueError:
            dt = now
        if dt >= now and b.status == BookingStatus.CONFIRMED:
            upcoming.append(b)
        else:
            past.append(b)
    return upcoming, past

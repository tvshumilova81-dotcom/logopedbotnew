from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.booking import Booking, BookingStatus


async def create_booking(session: AsyncSession, user_id: int, data: dict) -> Booking:
    booking = Booking(user_id=user_id, **data)
    session.add(booking)
    await session.commit()
    await session.refresh(booking)
    return booking


async def get_booking(session: AsyncSession, booking_id: int) -> Booking | None:
    return await session.get(Booking, booking_id)


async def set_booking_status(session: AsyncSession, booking_id: int, status: BookingStatus) -> None:
    booking = await session.get(Booking, booking_id)
    if booking:
        booking.status = status
        await session.commit()


async def delete_booking(session: AsyncSession, booking_id: int) -> None:
    booking = await session.get(Booking, booking_id)
    if booking:
        await session.delete(booking)
        await session.commit()


async def latest_booking_for_user(session: AsyncSession, user_id: int) -> Booking | None:
    result = await session.execute(
        select(Booking).where(Booking.user_id == user_id).order_by(Booking.id.desc())
    )
    return result.scalars().first()


async def count_bookings(session: AsyncSession) -> int:
    result = await session.execute(select(Booking))
    return len(result.scalars().all())

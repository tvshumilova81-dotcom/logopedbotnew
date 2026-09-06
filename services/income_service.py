from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.income import IncomeAdjustment
from database.models.slot import BookingStatus, MiniAppBooking


async def get_bookings_income(session: AsyncSession) -> int:
    result = await session.execute(
        select(func.coalesce(func.sum(MiniAppBooking.price), 0)).where(
            MiniAppBooking.status != BookingStatus.CANCELLED
        )
    )
    return int(result.scalar_one())


async def get_adjustments_total(session: AsyncSession) -> int:
    result = await session.execute(select(func.coalesce(func.sum(IncomeAdjustment.amount), 0)))
    return int(result.scalar_one())


async def get_total_income(session: AsyncSession) -> int:
    return await get_bookings_income(session) + await get_adjustments_total(session)


async def list_adjustments(session: AsyncSession, limit: int = 50) -> list[IncomeAdjustment]:
    result = await session.execute(
        select(IncomeAdjustment).order_by(IncomeAdjustment.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def add_adjustment(session: AsyncSession, amount: int, comment: str | None) -> IncomeAdjustment:
    adj = IncomeAdjustment(amount=amount, comment=comment)
    session.add(adj)
    await session.commit()
    await session.refresh(adj)
    return adj

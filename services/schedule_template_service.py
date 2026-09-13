from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.schedule_template import WeeklyTemplateSlot

# Значения по умолчанию, которыми заполняется таблица при самом первом запуске:
# Пн-Пт 18:00-20:00 (каждые 30 минут), Сб-Вс 10:00-12:00 (каждые 30 минут).
DEFAULT_TEMPLATE: dict[int, list[str]] = {
    0: ["18:00", "18:30", "19:00", "19:30"],
    1: ["18:00", "18:30", "19:00", "19:30"],
    2: ["18:00", "18:30", "19:00", "19:30"],
    3: ["18:00", "18:30", "19:00", "19:30"],
    4: ["18:00", "18:30", "19:00", "19:30"],
    5: ["10:00", "10:30", "11:00", "11:30"],
    6: ["10:00", "10:30", "11:00", "11:30"],
}


async def _seed_if_empty(session: AsyncSession) -> None:
    result = await session.execute(select(WeeklyTemplateSlot.id).limit(1))
    if result.scalar_one_or_none() is not None:
        return
    rows = [
        WeeklyTemplateSlot(weekday=weekday, time=t)
        for weekday, times in DEFAULT_TEMPLATE.items()
        for t in times
    ]
    session.add_all(rows)
    await session.commit()


async def get_template(session: AsyncSession) -> dict[int, list[str]]:
    """Возвращает текущий шаблон {weekday: [times]}. При первом обращении засеивает БД значениями по умолчанию."""
    await _seed_if_empty(session)
    result = await session.execute(
        select(WeeklyTemplateSlot).order_by(WeeklyTemplateSlot.weekday, WeeklyTemplateSlot.time)
    )
    template: dict[int, list[str]] = {i: [] for i in range(7)}
    for row in result.scalars().all():
        template.setdefault(row.weekday, []).append(row.time)
    return template


async def add_template_slot(session: AsyncSession, weekday: int, time_str: str) -> bool:
    existing = await session.execute(
        select(WeeklyTemplateSlot).where(
            WeeklyTemplateSlot.weekday == weekday, WeeklyTemplateSlot.time == time_str
        )
    )
    if existing.scalar_one_or_none() is not None:
        return False
    session.add(WeeklyTemplateSlot(weekday=weekday, time=time_str))
    await session.commit()
    return True


async def delete_template_slot(session: AsyncSession, weekday: int, time_str: str) -> bool:
    result = await session.execute(
        select(WeeklyTemplateSlot).where(
            WeeklyTemplateSlot.weekday == weekday, WeeklyTemplateSlot.time == time_str
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        return False
    await session.delete(row)
    await session.commit()
    return True

from __future__ import annotations

from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, TimestampMixin


class WeeklyTemplateSlot(TimestampMixin, Base):
    """Один пункт стандартного недельного расписания (шаблон), который можно
    редактировать из админ-панели. weekday: 0=Пн ... 6=Вс."""

    __tablename__ = "weekly_template_slots"
    __table_args__ = (UniqueConstraint("weekday", "time", name="uq_template_weekday_time"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    weekday: Mapped[int] = mapped_column(Integer, index=True)
    time: Mapped[str] = mapped_column(String(5))

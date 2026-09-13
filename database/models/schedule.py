from __future__ import annotations

import enum
from datetime import date as date_type
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from database.models.user import User


class LessonStatus(str, enum.Enum):
    CONFIRMED = "confirmed"   # предстоящее занятие
    DONE = "done"             # прошло
    CANCELLED = "cancelled"   # отменено (клиентом или админом)


class IncomeSource(str, enum.Enum):
    BOOKING = "booking"   # начислено автоматически за занятие
    MANUAL = "manual"     # добавлено/скорректировано вручную логопедом


class ScheduleBlock(TimestampMixin, Base):
    """Слот, который логопед вручную закрыла (личное время, недоступно для записи)."""

    __tablename__ = "schedule_blocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date_type] = mapped_column(Date, index=True)
    time: Mapped[str] = mapped_column(String(5))  # "10:00"
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class LessonBooking(TimestampMixin, Base):
    """Запись на конкретную дату/время через Mini App."""

    __tablename__ = "lesson_bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    date: Mapped[date_type] = mapped_column(Date, index=True)
    time: Mapped[str] = mapped_column(String(5))
    topic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    price_rub: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[LessonStatus] = mapped_column(Enum(LessonStatus), default=LessonStatus.CONFIRMED)

    user: Mapped["User"] = relationship()


class IncomeEntry(TimestampMixin, Base):
    """Запись о доходе. Может быть привязана к занятию либо добавлена вручную."""

    __tablename__ = "income_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date_type] = mapped_column(Date, index=True)
    amount: Mapped[int] = mapped_column(Integer)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[IncomeSource] = mapped_column(Enum(IncomeSource), default=IncomeSource.MANUAL)
    lesson_booking_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("lesson_bookings.id"), nullable=True
    )

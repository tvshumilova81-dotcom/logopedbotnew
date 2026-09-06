from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from database.models.user import User


class SlotStatus(str, enum.Enum):
    FREE = "free"
    BOOKED = "booked"
    BLOCKED = "blocked"  # закрыто вручную администратором (личные дела и т.п.)


class BookingStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MiniAppBooking(TimestampMixin, Base):
    """Запись на занятие, сделанная через мини-приложение."""

    __tablename__ = "miniapp_bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    date: Mapped[str] = mapped_column(String(10))  # "2025-06-07"
    time: Mapped[str] = mapped_column(String(5))  # "11:00"

    country: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    topic: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    price: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus), default=BookingStatus.CONFIRMED
    )

    user: Mapped["User"] = relationship()


class TimeSlot(TimestampMixin, Base):
    """Один тайм-слот в расписании — свободен / занят / закрыт админом."""

    __tablename__ = "time_slots"
    __table_args__ = (UniqueConstraint("date", "time", name="uq_time_slot_date_time"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[str] = mapped_column(String(10), index=True)
    time: Mapped[str] = mapped_column(String(5))
    status: Mapped[SlotStatus] = mapped_column(Enum(SlotStatus), default=SlotStatus.FREE)

    booking_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("miniapp_bookings.id"), nullable=True
    )
    booking: Mapped[Optional["MiniAppBooking"]] = relationship()

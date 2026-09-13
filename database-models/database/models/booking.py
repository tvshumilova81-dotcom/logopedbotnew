from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from database.models.user import User


class BookingStatus(str, enum.Enum):
    NEW = "new"
    ACCEPTED = "accepted"
    CANCELLED = "cancelled"


class Booking(TimestampMixin, Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    parent_name: Mapped[str] = mapped_column(String(128))
    child_name: Mapped[str] = mapped_column(String(128))
    child_age: Mapped[str] = mapped_column(String(32))
    child_gender: Mapped[str] = mapped_column(String(16))
    country: Mapped[str] = mapped_column(String(64))
    timezone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    problem: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    concern: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    noticed_since: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    saw_speech_therapist: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    specialists_reports: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    convenient_days: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    convenient_time: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus), default=BookingStatus.NEW
    )

    admin_message_id: Mapped[Optional[int]] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship(back_populates="bookings")

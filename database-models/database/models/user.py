from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from database.models.booking import Booking
    from database.models.purchase import Purchase
    from database.models.questionnaire import Questionnaire


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    parent_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    child_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    child_age: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    child_gender: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned_spam: Mapped[bool] = mapped_column(Boolean, default=False)

    bookings: Mapped[List["Booking"]] = relationship(back_populates="user")
    questionnaires: Mapped[List["Questionnaire"]] = relationship(back_populates="user")
    purchases: Mapped[List["Purchase"]] = relationship(back_populates="user")

    def display_name(self) -> str:
        return self.parent_name or self.username or f"ID {self.telegram_id}"

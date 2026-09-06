from __future__ import annotations

from typing import Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, TimestampMixin


class IncomeAdjustment(TimestampMixin, Base):
    """Ручная корректировка дохода (плюс или минус), которую вносит админ."""

    __tablename__ = "income_adjustments"

    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[int] = mapped_column(Integer)  # в рублях, может быть отрицательным
    comment: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

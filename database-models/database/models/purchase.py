from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from database.models.user import User


class Purchase(TimestampMixin, Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    price_stars: Mapped[int] = mapped_column(Integer)
    telegram_payment_charge_id: Mapped[str] = mapped_column(String(256))

    user: Mapped["User"] = relationship(back_populates="purchases")

from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, TimestampMixin


class ProgressNote(TimestampMixin, Base):
    """Запись о прогрессе ребёнка: было -> стало, которую добавляет логопед."""

    __tablename__ = "progress_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    title: Mapped[str] = mapped_column(String(256))
    before_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    after_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Homework(TimestampMixin, Base):
    """Домашнее задание для ребёнка, которое добавляет логопед."""

    __tablename__ = "homework"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    text: Mapped[str] = mapped_column(Text)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)

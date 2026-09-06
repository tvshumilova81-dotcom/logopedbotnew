from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from database.models.user import User


class Questionnaire(TimestampMixin, Base):
    __tablename__ = "questionnaires"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    child_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    child_age: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    attends_kindergarten: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    attends_school: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    native_language: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    second_language: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    says_single_words: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    says_short_sentences: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    says_long_sentences: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    tells_about_day: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    likes_talking: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    answers_questions: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    understands_speech: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    follows_instructions: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    is_understood_by_others: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    pronunciation_difficulties: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    pronunciation_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    focuses_20_min: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    gets_distracted: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    likes_books: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    likes_board_games: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    likes_drawing: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    likes_modelling: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    behavior_difficulties: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    peer_communication_difficulties: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    dresses_independently: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    puts_away_toys: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    follows_instructions_skill: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    repeats_movements: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    repeats_words: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    repeats_sentences: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    remembers_poems: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    neurologist_consult: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    ent_consult: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    psychologist_consult: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    had_speech_therapist: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    specialist_reports: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    hearing_problems: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    pregnancy_birth_features: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    additional_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    admin_message_id: Mapped[Optional[int]] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship(back_populates="questionnaires")

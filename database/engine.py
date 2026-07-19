from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.settings import settings
from database.base import Base

engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Создаёт таблицы, если их ещё нет (используется как fallback к Alembic)."""
    async with engine.begin() as conn:
        # Импортируем модели, чтобы они были зарегистрированы в metadata
        from database.models import (  # noqa: F401
            booking,
            material,
            purchase,
            questionnaire,
            user,
        )

        await conn.run_sync(Base.metadata.create_all)

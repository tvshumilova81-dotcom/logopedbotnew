from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.questionnaire import Questionnaire


async def create_questionnaire(session: AsyncSession, user_id: int, data: dict) -> Questionnaire:
    questionnaire = Questionnaire(user_id=user_id, is_completed=True, **data)
    session.add(questionnaire)
    await session.commit()
    await session.refresh(questionnaire)
    return questionnaire


async def get_questionnaire(session: AsyncSession, questionnaire_id: int) -> Questionnaire | None:
    return await session.get(Questionnaire, questionnaire_id)


async def latest_questionnaire_for_user(session: AsyncSession, user_id: int) -> Questionnaire | None:
    result = await session.execute(
        select(Questionnaire)
        .where(Questionnaire.user_id == user_id, Questionnaire.is_completed.is_(True))
        .order_by(Questionnaire.id.desc())
    )
    return result.scalars().first()


async def count_completed(session: AsyncSession) -> int:
    result = await session.execute(
        select(Questionnaire).where(Questionnaire.is_completed.is_(True))
    )
    return len(result.scalars().all())

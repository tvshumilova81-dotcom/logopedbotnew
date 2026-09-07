from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.progress import Homework, ProgressNote


async def get_progress_notes(session: AsyncSession, user_id: int) -> list[ProgressNote]:
    result = await session.execute(
        select(ProgressNote)
        .where(ProgressNote.user_id == user_id)
        .order_by(ProgressNote.created_at.desc())
    )
    return list(result.scalars().all())


async def get_homework(session: AsyncSession, user_id: int) -> list[Homework]:
    result = await session.execute(
        select(Homework).where(Homework.user_id == user_id).order_by(Homework.created_at.desc())
    )
    return list(result.scalars().all())


async def add_progress_note(
    session: AsyncSession,
    *,
    user_id: int,
    title: str,
    before_text: str | None,
    after_text: str | None,
    note: str | None,
) -> ProgressNote:
    entry = ProgressNote(
        user_id=user_id, title=title, before_text=before_text, after_text=after_text, note=note
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


async def add_homework(session: AsyncSession, *, user_id: int, text: str) -> Homework:
    hw = Homework(user_id=user_id, text=text)
    session.add(hw)
    await session.commit()
    await session.refresh(hw)
    return hw


async def toggle_homework(session: AsyncSession, homework_id: int, user_id: int) -> Homework | None:
    hw = await session.get(Homework, homework_id)
    if hw is None or hw.user_id != user_id:
        return None
    hw.is_done = not hw.is_done
    await session.commit()
    await session.refresh(hw)
    return hw


async def delete_progress_note(session: AsyncSession, note_id: int) -> bool:
    note = await session.get(ProgressNote, note_id)
    if note is None:
        return False
    await session.delete(note)
    await session.commit()
    return True


async def delete_homework(session: AsyncSession, homework_id: int) -> bool:
    hw = await session.get(Homework, homework_id)
    if hw is None:
        return False
    await session.delete(hw)
    await session.commit()
    return True

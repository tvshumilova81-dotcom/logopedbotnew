from __future__ import annotations

from aiogram.types import User as TgUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import User


async def get_or_create_user(session: AsyncSession, tg_user: TgUser) -> User:
    result = await session.execute(
        select(User).where(User.telegram_id == tg_user.id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            telegram_id=tg_user.id,
            username=tg_user.username,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    elif user.username != tg_user.username:
        user.username = tg_user.username
        await session.commit()
    return user


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def search_users(session: AsyncSession, query: str) -> list[User]:
    like = f"%{query}%"
    stmt = select(User).where(
        (User.parent_name.ilike(like))
        | (User.child_name.ilike(like))
        | (User.username.ilike(like))
    )
    if query.isdigit():
        stmt = select(User).where(
            (User.telegram_id == int(query)) | (User.parent_name.ilike(like))
        )
    result = await session.execute(stmt.limit(30))
    return list(result.scalars().all())


async def all_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User))
    return list(result.scalars().all())

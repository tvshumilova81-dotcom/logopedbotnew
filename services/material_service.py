from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.material import Material
from database.models.purchase import Purchase


async def list_active_materials(session: AsyncSession) -> list[Material]:
    result = await session.execute(
        select(Material).where(Material.is_active.is_(True)).order_by(Material.id)
    )
    return list(result.scalars().all())


async def get_material(session: AsyncSession, material_id: int) -> Material | None:
    return await session.get(Material, material_id)


async def get_material_by_slug(session: AsyncSession, slug: str) -> Material | None:
    result = await session.execute(select(Material).where(Material.slug == slug))
    return result.scalar_one_or_none()


async def create_material(session: AsyncSession, **kwargs) -> Material:
    material = Material(**kwargs)
    session.add(material)
    await session.commit()
    await session.refresh(material)
    return material


async def delete_material(session: AsyncSession, material_id: int) -> None:
    material = await session.get(Material, material_id)
    if material:
        material.is_active = False
        await session.commit()


async def user_purchased_material_ids(session: AsyncSession, user_id: int) -> set[int]:
    result = await session.execute(
        select(Purchase.material_id).where(Purchase.user_id == user_id)
    )
    return set(result.scalars().all())


async def has_purchased(session: AsyncSession, user_id: int, material_id: int) -> bool:
    result = await session.execute(
        select(Purchase).where(
            Purchase.user_id == user_id, Purchase.material_id == material_id
        )
    )
    return result.scalar_one_or_none() is not None


async def create_purchase(
    session: AsyncSession,
    user_id: int,
    material_id: int,
    price_stars: int,
    charge_id: str,
) -> Purchase:
    purchase = Purchase(
        user_id=user_id,
        material_id=material_id,
        price_stars=price_stars,
        telegram_payment_charge_id=charge_id,
    )
    session.add(purchase)
    await session.commit()
    await session.refresh(purchase)
    return purchase


async def user_purchases(session: AsyncSession, user_id: int) -> list[Material]:
    result = await session.execute(
        select(Material)
        .join(Purchase, Purchase.material_id == Material.id)
        .where(Purchase.user_id == user_id)
    )
    return list(result.scalars().all())


async def sales_stats(session: AsyncSession) -> list[tuple[str, int, int]]:
    """Возвращает (название материала, количество продаж, доход в Stars)."""
    result = await session.execute(
        select(
            Material.title,
            func.count(Purchase.id),
            func.coalesce(func.sum(Purchase.price_stars), 0),
        )
        .join(Purchase, Purchase.material_id == Material.id, isouter=True)
        .group_by(Material.id)
    )
    return [(row[0], row[1], row[2]) for row in result.all()]


async def total_revenue(session: AsyncSession) -> int:
    result = await session.execute(select(func.coalesce(func.sum(Purchase.price_stars), 0)))
    return result.scalar_one()


async def total_sold(session: AsyncSession) -> int:
    result = await session.execute(select(func.count(Purchase.id)))
    return result.scalar_one()

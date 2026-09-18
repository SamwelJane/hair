import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.identity import Address
from app.models.orders import Order, Review


async def list_own_orders_with_details(db: AsyncSession, user_id: uuid.UUID) -> list[Order]:
    return list(
        (
            await db.execute(
                select(Order)
                .where(Order.user_id == user_id)
                .options(
                    selectinload(Order.items),
                    selectinload(Order.payments),
                    selectinload(Order.status_history),
                )
                .order_by(Order.created_at.desc())
            )
        )
        .scalars()
        .all()
    )


async def list_own_addresses(db: AsyncSession, user_id: uuid.UUID) -> list[Address]:
    return list((await db.execute(select(Address).where(Address.user_id == user_id))).scalars().all())


async def list_own_reviews(db: AsyncSession, user_id: uuid.UUID) -> list[Review]:
    return list((await db.execute(select(Review).where(Review.user_id == user_id))).scalars().all())

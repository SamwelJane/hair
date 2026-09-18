import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import Address


class AddressNotFoundError(Exception):
    pass


async def list_addresses(db: AsyncSession, user_id: uuid.UUID) -> list[Address]:
    return list(
        (
            await db.execute(
                select(Address)
                .where(Address.user_id == user_id)
                .order_by(Address.is_default.desc(), Address.created_at.desc())
            )
        )
        .scalars()
        .all()
    )


async def create_address(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    label: str | None,
    full_name: str,
    line1: str,
    line2: str | None,
    city: str,
    country_code: str,
    postal_code: str | None,
    phone: str,
    is_default: bool,
) -> Address:
    if is_default:
        await db.execute(update(Address).where(Address.user_id == user_id).values(is_default=False))

    address = Address(
        user_id=user_id, label=label, full_name=full_name, line1=line1, line2=line2, city=city,
        country_code=country_code, postal_code=postal_code, phone=phone, is_default=is_default,
    )
    db.add(address)
    await db.commit()
    await db.refresh(address)
    return address


async def delete_address(db: AsyncSession, address_id: uuid.UUID, user_id: uuid.UUID) -> None:
    address = await db.get(Address, address_id)
    if address is None or address.user_id != user_id:
        raise AddressNotFoundError(f"Address {address_id} not found")
    await db.delete(address)
    await db.commit()


async def set_default_address(db: AsyncSession, address_id: uuid.UUID, user_id: uuid.UUID) -> Address:
    address = await db.get(Address, address_id)
    if address is None or address.user_id != user_id:
        raise AddressNotFoundError(f"Address {address_id} not found")

    await db.execute(update(Address).where(Address.user_id == user_id).values(is_default=False))
    address.is_default = True
    await db.commit()
    await db.refresh(address)
    return address

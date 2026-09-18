import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.identity import Address, User
from app.schemas.addresses import AddressOut, CreateAddressRequest
from app.services import addresses as addresses_service

router = APIRouter(prefix="/addresses", tags=["addresses"], dependencies=[Depends(get_current_user)])


def _to_out(address: Address) -> AddressOut:
    return AddressOut(
        id=address.id, label=address.label, full_name=address.full_name, line1=address.line1,
        line2=address.line2, city=address.city, country_code=address.country_code,
        postal_code=address.postal_code, phone=address.phone, is_default=address.is_default,
    )


@router.get("", response_model=list[AddressOut])
async def list_my_addresses(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> list[AddressOut]:
    addresses = await addresses_service.list_addresses(db, user.id)
    return [_to_out(a) for a in addresses]


@router.post("", response_model=AddressOut, status_code=status.HTTP_201_CREATED)
async def create_my_address(
    payload: CreateAddressRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> AddressOut:
    address = await addresses_service.create_address(
        db, user.id, label=payload.label, full_name=payload.full_name, line1=payload.line1, line2=payload.line2,
        city=payload.city, country_code=payload.country_code, postal_code=payload.postal_code, phone=payload.phone,
        is_default=payload.is_default,
    )
    return _to_out(address)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_address(
    address_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> None:
    try:
        await addresses_service.delete_address(db, address_id, user.id)
    except addresses_service.AddressNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{address_id}/set-default", response_model=AddressOut)
async def set_my_default_address(
    address_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> AddressOut:
    try:
        address = await addresses_service.set_default_address(db, address_id, user.id)
    except addresses_service.AddressNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_out(address)

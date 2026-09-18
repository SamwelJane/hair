import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_permission
from app.models.external_shipments import ExternalShipment
from app.models.identity import User
from app.schemas.warehouse import (
    ExternalShipmentCreateRequest,
    ExternalShipmentListOut,
    ExternalShipmentOut,
)
from app.services import external_shipments as external_shipments_service

router = APIRouter(prefix="/warehouse/external-shipments", tags=["warehouse-external-shipments"])

PAGE_SIZE = 20


def _to_out(shipment: ExternalShipment) -> ExternalShipmentOut:
    return ExternalShipmentOut(
        id=shipment.id,
        tracking_number=shipment.tracking_number,
        customer_name=shipment.customer_name,
        customer_phone=shipment.customer_phone,
        customer_email=shipment.customer_email,
        supplier_reference=shipment.supplier_reference,
        notes=shipment.notes,
        status=shipment.status,
        created_at=shipment.created_at,
    )


@router.post("", response_model=ExternalShipmentOut, status_code=201)
async def create_external_shipment(
    payload: ExternalShipmentCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("external_shipments.create")),
) -> ExternalShipmentOut:
    shipment, _package = await external_shipments_service.create_external_shipment(
        db,
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        customer_email=payload.customer_email,
        supplier_reference=payload.supplier_reference,
        notes=payload.notes,
        weight_grams=payload.weight_grams,
        length_cm=payload.length_cm,
        width_cm=payload.width_cm,
        height_cm=payload.height_cm,
        actor_user_id=user.id,
    )
    return _to_out(shipment)


@router.get("", response_model=ExternalShipmentListOut)
async def list_external_shipments(
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("external_shipments.read")),
) -> ExternalShipmentListOut:
    stmt = select(ExternalShipment)
    count_stmt = select(func.count()).select_from(ExternalShipment)
    if q:
        pattern = f"%{q}%"
        condition = or_(ExternalShipment.tracking_number.ilike(pattern), ExternalShipment.customer_phone.ilike(pattern))
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)

    stmt = stmt.order_by(ExternalShipment.created_at.desc()).limit(PAGE_SIZE).offset((page - 1) * PAGE_SIZE)
    shipments = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(count_stmt)).scalar_one()

    return ExternalShipmentListOut(
        external_shipments=[_to_out(s) for s in shipments], total=total, page=page, page_size=PAGE_SIZE
    )


@router.get("/{shipment_id}", response_model=ExternalShipmentOut)
async def get_external_shipment(
    shipment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("external_shipments.read")),
) -> ExternalShipmentOut:
    shipment = await db.get(ExternalShipment, shipment_id)
    if shipment is None:
        raise HTTPException(status_code=404, detail="External shipment not found")
    return _to_out(shipment)

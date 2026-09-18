import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_db, require_admin, require_strict_admin
from app.models.catalog import Product, Supplier
from app.models.identity import User
from app.models.orders import Order
from app.models.payments import SupplierOrder
from app.schemas.admin_suppliers import (
    CreateSupplierRequest,
    PendingSupplierOrderOut,
    SupplierDetailOut,
    SupplierOut,
    SupplierPerformanceOut,
)
from app.services import suppliers as suppliers_service

router = APIRouter(prefix="/admin", tags=["admin-suppliers"], dependencies=[Depends(require_admin)])


def _supplier_to_out(supplier: Supplier, product_count: int = 0) -> SupplierOut:
    return SupplierOut(
        id=supplier.id,
        name=supplier.name,
        country=supplier.country,
        email=supplier.email,
        whatsapp_number=supplier.whatsapp_number,
        default_margin_pct=supplier.default_margin_pct,
        status=supplier.status,
        user_id=supplier.user_id,
        product_count=product_count,
    )


@router.get("/suppliers", response_model=list[SupplierOut])
async def list_suppliers(db: AsyncSession = Depends(get_db)) -> list[SupplierOut]:
    suppliers = (await db.execute(select(Supplier).order_by(Supplier.created_at.desc()))).scalars().all()
    result = []
    for supplier in suppliers:
        count = await db.scalar(select(func.count()).select_from(Product).where(Product.supplier_id == supplier.id))
        result.append(_supplier_to_out(supplier, count or 0))
    return result


@router.post("/suppliers", response_model=SupplierOut, status_code=201)
async def create_supplier(
    payload: CreateSupplierRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_strict_admin),
) -> SupplierOut:
    """Creating/managing supplier business-entity records is ADMIN-only -
    STAFF can still view the supplier list and advance orders day-to-day."""
    supplier = await suppliers_service.create_supplier(
        db,
        name=payload.name,
        country=payload.country,
        email=payload.email,
        whatsapp_number=payload.whatsapp_number,
        default_margin_pct=payload.default_margin_pct,
        temporary_password=payload.temporary_password,
        actor_user_id=admin.id,
    )
    return _supplier_to_out(supplier)


@router.get("/suppliers/{supplier_id}", response_model=SupplierDetailOut)
async def get_supplier_detail(supplier_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> SupplierDetailOut:
    supplier = await db.get(Supplier, supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")

    performance = await suppliers_service.get_supplier_performance(db, supplier_id)

    supplier_orders = (
        (
            await db.execute(
                select(SupplierOrder)
                .where(SupplierOrder.supplier_id == supplier_id)
                .options(selectinload(SupplierOrder.order).selectinload(Order.user))
                .order_by(SupplierOrder.sent_at.desc())
            )
        )
        .scalars()
        .all()
    )
    pending = [so for so in supplier_orders if so.status.value != "READY"]

    return SupplierDetailOut(
        supplier=_supplier_to_out(supplier),
        performance=SupplierPerformanceOut(
            total_orders=performance.total_orders,
            completed_orders=performance.completed_orders,
            avg_processing_days=performance.avg_processing_days,
            on_time_rate_pct=performance.on_time_rate_pct,
        ),
        pending_orders=[
            PendingSupplierOrderOut(
                id=so.id,
                order_id=so.order_id,
                order_number=so.order.order_number,
                customer_email=so.order.user.email,
                status=so.status.value,
                sent_at=so.sent_at,
            )
            for so in pending
        ],
    )


@router.post("/supplier-orders/{supplier_order_id}/advance", response_model=PendingSupplierOrderOut)
async def advance_supplier_order(
    supplier_order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> PendingSupplierOrderOut:
    try:
        supplier_order = await suppliers_service.advance_supplier_order(
            db, supplier_order_id, actor_user_id=admin.id
        )
    except suppliers_service.SupplierOrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except suppliers_service.NoNextStatusError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    order = await db.get(Order, supplier_order.order_id, options=[selectinload(Order.user)])
    assert order is not None
    return PendingSupplierOrderOut(
        id=supplier_order.id,
        order_id=supplier_order.order_id,
        order_number=order.order_number,
        customer_email=order.user.email,
        status=supplier_order.status.value,
        sent_at=supplier_order.sent_at,
    )

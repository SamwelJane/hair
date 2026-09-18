import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_supplier, get_db, require_supplier
from app.models.catalog import Supplier
from app.models.identity import User
from app.models.orders import Order, OrderItem
from app.models.payments import SupplierOrder
from app.schemas.supplier_orders import (
    SupplierOrderItemOut,
    SupplierOrderOut,
    UpdateSupplierOrderStatusRequest,
)
from app.services import suppliers as suppliers_service

router = APIRouter(prefix="/supplier", tags=["supplier"], dependencies=[Depends(require_supplier)])


def _supplier_order_select():
    return select(SupplierOrder).options(
        selectinload(SupplierOrder.order).selectinload(Order.user),
        selectinload(SupplierOrder.order).selectinload(Order.items).selectinload(OrderItem.product),
        selectinload(SupplierOrder.order).selectinload(Order.items).selectinload(OrderItem.variant),
    )


def _to_out(supplier_order: SupplierOrder) -> SupplierOrderOut:
    order = supplier_order.order
    # A single order can be split across multiple suppliers - only surface
    # this supplier's own line items, not the whole order's contents.
    items = [
        SupplierOrderItemOut(
            product_name=item.product.name,
            variant_sku=item.variant.sku if item.variant else None,
            quantity=item.quantity,
        )
        for item in order.items
        if item.product.supplier_id == supplier_order.supplier_id
    ]
    return SupplierOrderOut(
        id=supplier_order.id,
        order_id=order.id,
        order_number=order.order_number,
        customer_name=order.user.name,
        status=supplier_order.status,
        sent_at=supplier_order.sent_at,
        eta_days=supplier_order.eta_days,
        decline_reason=supplier_order.decline_reason,
        items=items,
    )


@router.get("/orders", response_model=list[SupplierOrderOut])
async def list_my_orders(
    db: AsyncSession = Depends(get_db),
    supplier: Supplier = Depends(get_current_supplier),
) -> list[SupplierOrderOut]:
    supplier_orders = (
        (
            await db.execute(
                _supplier_order_select()
                .where(SupplierOrder.supplier_id == supplier.id)
                .order_by(SupplierOrder.sent_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return [_to_out(so) for so in supplier_orders]


@router.post("/orders/{supplier_order_id}/status", response_model=SupplierOrderOut)
async def update_my_order_status(
    supplier_order_id: uuid.UUID,
    payload: UpdateSupplierOrderStatusRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_supplier),
    supplier: Supplier = Depends(get_current_supplier),
) -> SupplierOrderOut:
    try:
        await suppliers_service.update_supplier_order_status(
            db,
            supplier_order_id,
            supplier_id=supplier.id,
            to_status=payload.to_status,
            eta_days=payload.eta_days,
            decline_reason=payload.decline_reason,
            actor_user_id=user.id,
        )
    except suppliers_service.SupplierOrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except suppliers_service.ForbiddenSupplierOrderError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except suppliers_service.InvalidTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    refreshed = (
        await db.execute(_supplier_order_select().where(SupplierOrder.id == supplier_order_id))
    ).scalar_one()
    return _to_out(refreshed)

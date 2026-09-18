import uuid
from datetime import datetime, time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_db, require_admin
from app.models.catalog import ProductVariant
from app.models.enums import OrderStatus
from app.models.identity import User
from app.models.orders import Order, OrderItem, OrderStatusHistory
from app.models.packages import Package
from app.models.payments import Payment, SupplierOrder
from app.schemas.admin_orders import (
    AdminOrderDetailOut,
    AdminOrderItemOut,
    AdminOrderListItemOut,
    AdminOrderListOut,
    AdminOrderPackageOut,
    AdminOrderStatusHistoryOut,
    AdminPaymentOut,
    AdminSupplierOrderOut,
    UpdateOrderStatusRequest,
)
from app.services import order_state_machine

router = APIRouter(prefix="/admin/orders", tags=["admin-orders"], dependencies=[Depends(require_admin)])

PAGE_SIZE = 20


@router.get("", response_model=AdminOrderListOut)
async def list_orders(
    q: str | None = None,
    status: OrderStatus | None = None,
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
    page: int = 1,
    db: AsyncSession = Depends(get_db),
) -> AdminOrderListOut:
    page = max(1, page)
    stmt = select(Order).options(
        selectinload(Order.user), selectinload(Order.supplier_orders).selectinload(SupplierOrder.supplier)
    )
    count_stmt = select(func.count()).select_from(Order)

    if status is not None:
        stmt = stmt.where(Order.status == status)
        count_stmt = count_stmt.where(Order.status == status)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.join(User, Order.user_id == User.id).where(
            or_(Order.order_number.ilike(pattern), User.email.ilike(pattern))
        )
        count_stmt = count_stmt.join(User, Order.user_id == User.id).where(
            or_(Order.order_number.ilike(pattern), User.email.ilike(pattern))
        )
    if date_from:
        stmt = stmt.where(Order.created_at >= datetime.fromisoformat(date_from))
        count_stmt = count_stmt.where(Order.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        end_of_day = datetime.combine(datetime.fromisoformat(date_to).date(), time.max)
        stmt = stmt.where(Order.created_at <= end_of_day)
        count_stmt = count_stmt.where(Order.created_at <= end_of_day)

    stmt = stmt.order_by(Order.created_at.desc()).limit(PAGE_SIZE).offset((page - 1) * PAGE_SIZE)

    orders = (await db.execute(stmt)).scalars().unique().all()
    total = (await db.execute(count_stmt)).scalar_one()

    return AdminOrderListOut(
        orders=[
            AdminOrderListItemOut(
                id=o.id,
                order_number=o.order_number,
                tracking_number=o.tracking_number,
                customer_email=o.user.email,
                supplier_names=[so.supplier.name for so in o.supplier_orders],
                status=o.status,
                total_amount_usd=o.total_amount_usd,
                created_at=o.created_at,
            )
            for o in orders
        ],
        total=total,
        page=page,
        page_size=PAGE_SIZE,
    )


async def _load_order_detail(db: AsyncSession, order_id: uuid.UUID) -> Order:
    # populate_existing=True: without it, db.get() returns whatever's already
    # in the identity map (e.g. from an earlier plain db.get() call earlier
    # in this same request) without applying these options at all - silently
    # skipping the eager loads and leaving relationship access to fall back
    # to lazy-loading, which isn't supported synchronously under the async
    # engine and raises MissingGreenlet.
    order = await db.get(
        Order,
        order_id,
        populate_existing=True,
        options=[
            selectinload(Order.user),
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.items).selectinload(OrderItem.variant),
            selectinload(Order.status_history).selectinload(OrderStatusHistory.changed_by),
            selectinload(Order.supplier_orders).selectinload(SupplierOrder.supplier),
            selectinload(Order.payments).selectinload(Payment.confirmed_by),
            selectinload(Order.packages).selectinload(Package.consolidation),
        ],
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def _order_to_detail_out(order: Order) -> AdminOrderDetailOut:
    next_statuses = [s for s in OrderStatus if order_state_machine.can_transition(order.status, s)]

    def variant_label(variant: ProductVariant | None) -> str | None:
        if variant is None:
            return None
        parts = [p for p in (variant.length, variant.color, variant.texture) if p]
        return " / ".join(parts) if parts else None

    return AdminOrderDetailOut(
        id=order.id,
        order_number=order.order_number,
        tracking_number=order.tracking_number,
        status=order.status,
        customer_name=order.user.name,
        customer_email=order.user.email,
        total_amount_usd=order.total_amount_usd,
        total_amount_kes=order.total_amount_kes,
        items=[
            AdminOrderItemOut(
                id=item.id,
                product_name=item.product.name,
                variant_label=variant_label(item.variant),
                quantity=item.quantity,
                line_total_usd=item.line_total_usd,
            )
            for item in order.items
        ],
        supplier_orders=[
            AdminSupplierOrderOut(id=so.id, supplier_name=so.supplier.name, status=so.status.value)
            for so in order.supplier_orders
        ],
        payments=[
            AdminPaymentOut(
                id=p.id,
                provider=p.provider.value,
                status=p.status.value,
                amount_kes=p.amount_kes,
                provider_ref=p.provider_ref,
                confirmed_by_name=p.confirmed_by.name if p.confirmed_by else None,
                proof_of_payment_url=p.proof_of_payment_url,
            )
            for p in order.payments
        ],
        status_history=[
            AdminOrderStatusHistoryOut(
                id=h.id,
                to_status=h.to_status,
                changed_by_name=h.changed_by.name if h.changed_by else None,
                note=h.note,
                created_at=h.created_at,
            )
            for h in order.status_history
        ],
        packages=[
            AdminOrderPackageOut(
                id=p.id,
                package_code=p.package_code,
                status=p.status.value,
                qc_status=p.qc_status.value,
                consolidation_code=p.consolidation.consolidation_code if p.consolidation else None,
                shipment_code=p.consolidation.shipment_code if p.consolidation else None,
            )
            for p in order.packages
        ],
        next_statuses=next_statuses,
    )


@router.get("/{order_id}", response_model=AdminOrderDetailOut)
async def get_order_detail(order_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> AdminOrderDetailOut:
    order = await _load_order_detail(db, order_id)
    return _order_to_detail_out(order)


@router.post("/{order_id}/status", response_model=AdminOrderDetailOut)
async def update_order_status(
    order_id: uuid.UUID,
    payload: UpdateOrderStatusRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> AdminOrderDetailOut:
    try:
        await order_state_machine.transition_order_status(
            db, order_id, payload.to_status, actor_user_id=admin.id, note=payload.note
        )
    except order_state_machine.OrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except order_state_machine.InvalidTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    order = await _load_order_detail(db, order_id)
    return _order_to_detail_out(order)

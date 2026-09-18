import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.models.catalog import Supplier
from app.models.enums import SupplierOrderStatus, UserRole
from app.models.identity import User
from app.models.orders import OrderItem
from app.models.payments import SupplierOrder
from app.services.audit import log_audit
from app.services.order_state_machine import sync_order_status_from_supplier_orders

# Declining isn't part of this linear "advance one step" admin flow - see
# SUPPLIER_TRANSITIONS/update_supplier_order_status below for the
# supplier-facing decline action.
_NEXT_STATUS: dict[SupplierOrderStatus, SupplierOrderStatus | None] = {
    SupplierOrderStatus.SENT: SupplierOrderStatus.ACKNOWLEDGED,
    SupplierOrderStatus.ACKNOWLEDGED: SupplierOrderStatus.IN_PRODUCTION,
    SupplierOrderStatus.IN_PRODUCTION: SupplierOrderStatus.READY,
    SupplierOrderStatus.READY: None,
    SupplierOrderStatus.DECLINED: None,
}


class SupplierOrderNotFoundError(Exception):
    pass


class NoNextStatusError(Exception):
    pass


class ForbiddenSupplierOrderError(Exception):
    pass


class InvalidTransitionError(Exception):
    pass


# Mirrors SUPPLIER_TRANSITIONS in the old app's src/app/supplier/orders/page.tsx.
# Unlike the admin "advance one step" flow above, a supplier may also decline
# from SENT or ACKNOWLEDGED, and gives an ETA when acknowledging.
SUPPLIER_TRANSITIONS: dict[SupplierOrderStatus, tuple[SupplierOrderStatus, ...]] = {
    SupplierOrderStatus.SENT: (SupplierOrderStatus.ACKNOWLEDGED, SupplierOrderStatus.DECLINED),
    SupplierOrderStatus.ACKNOWLEDGED: (SupplierOrderStatus.IN_PRODUCTION, SupplierOrderStatus.DECLINED),
    SupplierOrderStatus.IN_PRODUCTION: (SupplierOrderStatus.READY,),
    SupplierOrderStatus.READY: (),
    SupplierOrderStatus.DECLINED: (),
}


class SupplierPerformance:
    def __init__(self, total_orders: int, completed_orders: int, avg_processing_days: float | None, on_time_rate_pct: float | None) -> None:
        self.total_orders = total_orders
        self.completed_orders = completed_orders
        self.avg_processing_days = avg_processing_days
        self.on_time_rate_pct = on_time_rate_pct


async def create_supplier(
    db: AsyncSession,
    *,
    name: str,
    country: str,
    email: str,
    whatsapp_number: str,
    default_margin_pct: Decimal,
    temporary_password: str | None,
    actor_user_id: uuid.UUID,
) -> Supplier:
    normalized_email = email.strip().lower()
    supplier = Supplier(
        name=name, country=country, email=normalized_email, whatsapp_number=whatsapp_number,
        default_margin_pct=default_margin_pct,
    )
    db.add(supplier)
    await db.flush()

    await log_audit(
        db, user_id=actor_user_id, action="CREATE_SUPPLIER", entity_type="Supplier", entity_id=str(supplier.id),
        metadata={"name": supplier.name},
    )

    # New vs. the old app: links via a real FK (Supplier.user_id) instead of
    # matching on lowercased email string at request time - see catalog.py's
    # Supplier model docstring for why that was fragile.
    if temporary_password:
        user = User(
            email=normalized_email, name=supplier.name, password_hash=hash_password(temporary_password),
            role=UserRole.SUPPLIER,
        )
        db.add(user)
        await db.flush()
        supplier.user_id = user.id

        await log_audit(
            db, user_id=actor_user_id, action="CREATE_SUPPLIER_LOGIN", entity_type="User", entity_id=str(user.id),
            metadata={"supplierId": str(supplier.id), "email": normalized_email},
        )

    await db.commit()
    await db.refresh(supplier)
    return supplier


async def advance_supplier_order(db: AsyncSession, supplier_order_id: uuid.UUID, *, actor_user_id: uuid.UUID) -> SupplierOrder:
    supplier_order = await db.get(SupplierOrder, supplier_order_id)
    if supplier_order is None:
        raise SupplierOrderNotFoundError(f"SupplierOrder {supplier_order_id} not found")

    next_status = _NEXT_STATUS.get(supplier_order.status)
    if next_status is None:
        raise NoNextStatusError(f"SupplierOrder {supplier_order_id} has no next status from {supplier_order.status}")

    from_status = supplier_order.status
    supplier_order.status = next_status
    if next_status == SupplierOrderStatus.READY:
        supplier_order.confirmed_at = datetime.now(UTC)

    await log_audit(
        db, user_id=actor_user_id, action="ADVANCE_SUPPLIER_ORDER", entity_type="SupplierOrder",
        entity_id=str(supplier_order_id), metadata={"from": from_status.value, "to": next_status.value},
    )
    await db.commit()

    await sync_order_status_from_supplier_orders(db, supplier_order.order_id)
    await db.refresh(supplier_order)
    return supplier_order


async def update_supplier_order_status(
    db: AsyncSession,
    supplier_order_id: uuid.UUID,
    *,
    supplier_id: uuid.UUID,
    to_status: SupplierOrderStatus,
    eta_days: int | None,
    decline_reason: str | None,
    actor_user_id: uuid.UUID,
) -> SupplierOrder:
    """Supplier self-service transition, gated by SUPPLIER_TRANSITIONS above.
    Ownership (supplier_id match) is checked here rather than left to the
    caller, since this is the one place both the id and the intended actor
    are in scope together."""
    supplier_order = await db.get(SupplierOrder, supplier_order_id)
    if supplier_order is None:
        raise SupplierOrderNotFoundError(f"SupplierOrder {supplier_order_id} not found")
    if supplier_order.supplier_id != supplier_id:
        raise ForbiddenSupplierOrderError("This order does not belong to your supplier account")

    allowed = SUPPLIER_TRANSITIONS.get(supplier_order.status, ())
    if to_status not in allowed:
        raise InvalidTransitionError(f"Invalid transition: {supplier_order.status.value} -> {to_status.value}")
    if to_status == SupplierOrderStatus.DECLINED and not decline_reason:
        raise InvalidTransitionError("A reason is required to decline an order.")

    from_status = supplier_order.status
    supplier_order.status = to_status
    if to_status == SupplierOrderStatus.ACKNOWLEDGED:
        supplier_order.eta_days = eta_days
    if to_status == SupplierOrderStatus.DECLINED:
        supplier_order.decline_reason = decline_reason
    if to_status == SupplierOrderStatus.READY:
        supplier_order.confirmed_at = datetime.now(UTC)

    await log_audit(
        db, user_id=actor_user_id, action="SUPPLIER_UPDATE_ORDER", entity_type="SupplierOrder",
        entity_id=str(supplier_order_id),
        metadata={"from": from_status.value, "to": to_status.value, "etaDays": eta_days, "declineReason": decline_reason},
    )
    await db.commit()

    await sync_order_status_from_supplier_orders(db, supplier_order.order_id)
    await db.refresh(supplier_order)
    return supplier_order


async def get_supplier_performance(db: AsyncSession, supplier_id: uuid.UUID) -> SupplierPerformance:
    """Processing time is measured from when a SupplierOrder was sent to
    when it was confirmed ready. "On time" compares that duration against
    the product's declared processing_time_days (using the slowest product
    in that supplier order as the bar to clear)."""
    supplier_orders = (
        (await db.execute(select(SupplierOrder).where(SupplierOrder.supplier_id == supplier_id)))
        .scalars()
        .all()
    )

    completed = [so for so in supplier_orders if so.confirmed_at is not None]
    if not completed:
        return SupplierPerformance(len(supplier_orders), 0, None, None)

    total_days = 0.0
    on_time_count = 0

    for so in completed:
        assert so.confirmed_at is not None  # narrowed by the `completed` filter above
        days = (so.confirmed_at - so.sent_at).total_seconds() / 86400
        total_days += days

        order_items = (
            (
                await db.execute(
                    select(OrderItem)
                    .where(OrderItem.order_id == so.order_id)
                    .options(selectinload(OrderItem.product))
                )
            )
            .scalars()
            .all()
        )
        relevant = [item for item in order_items if item.product.supplier_id == supplier_id]
        expected_days = max((item.product.processing_time_days for item in relevant), default=0)
        if days <= expected_days:
            on_time_count += 1

    return SupplierPerformance(
        total_orders=len(supplier_orders),
        completed_orders=len(completed),
        avg_processing_days=round(total_days / len(completed), 1),
        on_time_rate_pct=round((on_time_count / len(completed)) * 100, 1),
    )

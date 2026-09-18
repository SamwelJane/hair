from decimal import Decimal
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.catalog import ProductVariant
from app.models.enums import OrderStatus, SupplierOrderStatus
from app.models.orders import Order, OrderItem, OrderStatusHistory
from app.models.payments import SupplierOrder
from app.services.audit import log_audit
from app.services.notifications.whatsapp import (
    customer_order_status_whatsapp_message,
    send_whatsapp,
)
from app.worker.pool import enqueue_notify_supplier_new_order

# Canonical backend status flow. The client-facing stepper and the internal
# supplier timeline (see mockups) are presentation-layer groupings of this
# single enum, not separate status fields.
TRANSITIONS: dict[OrderStatus, list[OrderStatus]] = {
    OrderStatus.PENDING_PAYMENT: [OrderStatus.PAID, OrderStatus.CANCELLED],
    OrderStatus.PAID: [OrderStatus.SENT_TO_SUPPLIER, OrderStatus.CANCELLED],
    OrderStatus.SENT_TO_SUPPLIER: [OrderStatus.SUPPLIER_PROCESSING, OrderStatus.CANCELLED],
    OrderStatus.SUPPLIER_PROCESSING: [OrderStatus.READY_FOR_PICKUP, OrderStatus.CANCELLED],
    OrderStatus.READY_FOR_PICKUP: [OrderStatus.RECEIVED_AT_OFFICE],
    OrderStatus.RECEIVED_AT_OFFICE: [OrderStatus.SHIPPED_INTERNATIONALLY],
    OrderStatus.SHIPPED_INTERNATIONALLY: [OrderStatus.IN_TRANSIT],
    OrderStatus.IN_TRANSIT: [OrderStatus.DELIVERED],
    OrderStatus.DELIVERED: [],
    OrderStatus.CANCELLED: [],
}

# Groupings used to render the client-facing stepper from the mockup
# (Order Received -> Payment Confirmed -> Processing -> In Warehouse -> Shipping -> Out for Delivery).
CLIENT_STEPPER_GROUPS: list[dict] = [
    {"label": "Order Received", "statuses": [OrderStatus.PENDING_PAYMENT]},
    {"label": "Payment Confirmed", "statuses": [OrderStatus.PAID]},
    {
        "label": "Processing",
        "statuses": [OrderStatus.SENT_TO_SUPPLIER, OrderStatus.SUPPLIER_PROCESSING, OrderStatus.READY_FOR_PICKUP],
    },
    {"label": "In Warehouse", "statuses": [OrderStatus.RECEIVED_AT_OFFICE]},
    {"label": "Shipping", "statuses": [OrderStatus.SHIPPED_INTERNATIONALLY]},
    {"label": "Out for Delivery", "statuses": [OrderStatus.IN_TRANSIT, OrderStatus.DELIVERED]},
]

# Groupings used to render the internal supplier timeline from the admin mockup
# (Order Created -> Sent to Supplier -> In Production -> Pending Quality Check -> Ready for Dispatch).
SUPPLIER_TIMELINE_GROUPS: list[dict] = [
    {"label": "Order Created", "statuses": [OrderStatus.PENDING_PAYMENT, OrderStatus.PAID]},
    {"label": "Sent to Supplier", "statuses": [OrderStatus.SENT_TO_SUPPLIER]},
    {"label": "In Production", "statuses": [OrderStatus.SUPPLIER_PROCESSING]},
    {"label": "Pending Quality Check", "statuses": [OrderStatus.READY_FOR_PICKUP]},
    {"label": "Ready for Dispatch", "statuses": [OrderStatus.RECEIVED_AT_OFFICE]},
]


class InvalidTransitionError(Exception):
    pass


class OrderNotFoundError(Exception):
    pass


def can_transition(from_status: OrderStatus, to_status: OrderStatus) -> bool:
    return to_status in TRANSITIONS.get(from_status, [])


def assert_valid_transition(from_status: OrderStatus, to_status: OrderStatus) -> None:
    if not can_transition(from_status, to_status):
        raise InvalidTransitionError(f"Invalid order status transition: {from_status} -> {to_status}")


async def transition_order_status(
    db: AsyncSession,
    order_id: uuid.UUID,
    to_status: OrderStatus,
    *,
    actor_user_id: uuid.UUID | None = None,
    note: str | None = None,
) -> Order:
    # populate_existing=True: this order may already be in the session's
    # identity map without these relationships loaded (e.g. a plain db.get()
    # earlier in the same request) - without it, db.get() silently skips
    # these options and later synchronous attribute access (order.supplier_orders,
    # item.product) falls back to lazy-loading, which isn't supported under
    # the async engine and raises MissingGreenlet.
    order = await db.get(
        Order,
        order_id,
        populate_existing=True,
        options=[
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.items).selectinload(OrderItem.variant),
            selectinload(Order.user),
            selectinload(Order.supplier_orders),
        ],
    )
    if order is None:
        raise OrderNotFoundError(f"Order {order_id} not found")

    assert_valid_transition(order.status, to_status)
    from_status = order.status

    order.status = to_status
    db.add(OrderStatusHistory(order_id=order_id, from_status=from_status, to_status=to_status, changed_by_id=actor_user_id, note=note))

    new_supplier_order_ids: list[uuid.UUID] = []
    if to_status == OrderStatus.SENT_TO_SUPPLIER:
        supplier_ids = sorted({item.product.supplier_id for item in order.items}, key=str)
        for idx, supplier_id in enumerate(supplier_ids, start=1):
            existing = next((so for so in order.supplier_orders if so.supplier_id == supplier_id), None)
            if existing is None:
                sub_order_number = f"{order.order_number}-{idx:03d}"
                new_supplier_order = SupplierOrder(
                    order_id=order_id,
                    supplier_id=supplier_id,
                    status=SupplierOrderStatus.SENT,
                    sub_order_number=sub_order_number,
                )
                db.add(new_supplier_order)
                await db.flush()
                new_supplier_order_ids.append(new_supplier_order.id)
    elif to_status == OrderStatus.CANCELLED:
        # Tiered cancellation fee: 20% in SUPPLIER_PROCESSING, 0% beforehand
        if from_status == OrderStatus.SUPPLIER_PROCESSING:
            fee = (order.total_amount_usd * Decimal("0.20")).quantize(Decimal("0.01"))
            order.cancellation_fee_usd = fee
            order.refund_amount_usd = (order.total_amount_usd - fee).quantize(Decimal("0.01"))
        else:
            order.cancellation_fee_usd = Decimal("0.00")
            order.refund_amount_usd = order.total_amount_usd

        # Inventory restocking
        for item in order.items:
            if item.variant is not None:
                item.variant.stock_qty += item.quantity

        # Decline active supplier orders
        for so in order.supplier_orders:
            if so.status != SupplierOrderStatus.DECLINED:
                so.status = SupplierOrderStatus.DECLINED
                so.decline_reason = note or "Order cancelled"

    await log_audit(
        db,
        user_id=actor_user_id,
        action="TRANSITION_ORDER_STATUS",
        entity_type="Order",
        entity_id=str(order_id),
        metadata={"from": from_status.value, "to": to_status.value, "note": note},
    )
    await db.commit()

    for supplier_order_id in new_supplier_order_ids:
        await enqueue_notify_supplier_new_order(str(supplier_order_id))

    if order.user.phone:
        await send_whatsapp(
            order.user.phone,
            customer_order_status_whatsapp_message(
                order_number=order.order_number,
                status=to_status.value,
                tracking_number=order.tracking_number,
            ),
        )

    return order


async def sync_order_status_from_supplier_orders(db: AsyncSession, order_id: uuid.UUID) -> None:
    """Reconciles Order.status with the aggregate state of its SupplierOrders.
    Call this after any SupplierOrder.status change so admins/suppliers don't
    have to separately mirror supplier progress onto the parent order.

    Only auto-advances out of SUPPLIER_PROCESSING - every later stage has no
    supplier-side signal to reconcile against and stays on the manual admin
    workflow. If any supplier declines their portion, this does NOT
    auto-cancel the order (a multi-supplier order might still be fulfillable)
    - it just flags it for admin attention.
    """
    order = await db.get(Order, order_id, options=[selectinload(Order.supplier_orders)])
    if order is None or order.status != OrderStatus.SUPPLIER_PROCESSING or not order.supplier_orders:
        return

    declined = [so for so in order.supplier_orders if so.status == SupplierOrderStatus.DECLINED]
    if declined:
        await log_audit(
            db,
            user_id=None,
            action="SUPPLIER_ORDER_DECLINED_FLAG",
            entity_type="Order",
            entity_id=str(order_id),
            metadata={
                "reason": "One or more suppliers declined their portion - admin must resolve manually",
                "declinedSupplierOrderIds": [str(so.id) for so in declined],
            },
        )
        await db.commit()
        return

    all_ready = all(so.status == SupplierOrderStatus.READY for so in order.supplier_orders)
    if all_ready:
        await transition_order_status(
            db,
            order_id,
            OrderStatus.READY_FOR_PICKUP,
            note="Auto-advanced: all suppliers marked their portion ready",
        )

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.db.session import async_session_factory
from app.models.orders import OrderItem
from app.models.payments import SupplierOrder
from app.services.notifications.email import (
    send_email,
    supplier_order_email,
    supplier_order_status_change_email,
)
from app.services.notifications.whatsapp import send_whatsapp, supplier_order_whatsapp_message

logger = logging.getLogger(__name__)
settings = get_settings()


async def notify_supplier_new_order(ctx: dict[str, Any], supplier_order_id: str) -> None:
    """Port of the old app's queue/jobs/notify-supplier.ts processOne() for
    NEW_ORDER jobs. Runs in the arq worker process, on its own DB session."""
    async with async_session_factory() as db:
        supplier_order = await db.get(
            SupplierOrder,
            supplier_order_id,
            options=[selectinload(SupplierOrder.supplier), selectinload(SupplierOrder.order)],
        )
        if supplier_order is None:
            logger.warning("notify_supplier_new_order: SupplierOrder %s not found", supplier_order_id)
            return

        items = (
            (
                await db.execute(
                    select(OrderItem)
                    .where(OrderItem.order_id == supplier_order.order_id)
                    .options(selectinload(OrderItem.product), selectinload(OrderItem.variant))
                )
            )
            .scalars()
            .all()
        )

        product_lines = [
            f"{item.quantity}x {item.product.name}"
            + (f" ({item.variant.length or ''} {item.variant.color or ''})".strip() if item.variant else "")
            for item in items
        ]

        subject, html = supplier_order_email(
            supplier_name=supplier_order.supplier.name,
            order_number=supplier_order.order.order_number,
            product_lines=product_lines,
        )
        await send_email(supplier_order.supplier.email, subject, html)

        await send_whatsapp(
            supplier_order.supplier.whatsapp_number,
            supplier_order_whatsapp_message(
                supplier_name=supplier_order.supplier.name,
                order_number=supplier_order.order.order_number,
                product_lines=product_lines,
            ),
        )


async def notify_supplier_status_change(ctx: dict[str, Any], supplier_order_id: str, to_status: str) -> None:
    """Internal ops notification whenever a supplier updates their portion of
    an order - fires on every SupplierOrder status change past the initial
    send. Skipped entirely if ADMIN_NOTIFICATION_EMAIL isn't configured."""
    if not settings.admin_notification_email:
        logger.warning("ADMIN_NOTIFICATION_EMAIL not set - skipping status-change notification")
        return

    async with async_session_factory() as db:
        supplier_order = await db.get(
            SupplierOrder,
            supplier_order_id,
            options=[selectinload(SupplierOrder.supplier), selectinload(SupplierOrder.order)],
        )
        if supplier_order is None:
            logger.warning("notify_supplier_status_change: SupplierOrder %s not found", supplier_order_id)
            return

        subject, html = supplier_order_status_change_email(
            supplier_name=supplier_order.supplier.name,
            order_number=supplier_order.order.order_number,
            status=to_status,
            eta_days=supplier_order.eta_days,
            decline_reason=supplier_order.decline_reason,
        )
        await send_email(settings.admin_notification_email, subject, html)

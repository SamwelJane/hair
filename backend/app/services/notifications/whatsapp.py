"""WhatsApp notification service — Meta WhatsApp Business Cloud API.

Replaces the former Twilio-based sender. All outbound messages route through
app.integrations.meta_whatsapp.send_text_message(), which gracefully no-ops
in dev/test when META_WHATSAPP_TOKEN is absent.

This module is the single canonical place for:
  1. Sending WhatsApp messages from backend services / workers.
  2. Defining all customer-facing message body templates.
"""

from __future__ import annotations

import logging

from app.integrations.meta_whatsapp import send_text_message

logger = logging.getLogger(__name__)


async def send_whatsapp(to: str, body: str) -> None:
    """Send a WhatsApp message via Meta Cloud API.

    Falls back to a log warning (no-op) when the integration is not
    configured — same behaviour the old Twilio version used so existing
    callers require no changes.
    """
    try:
        await send_text_message(to, body)
    except Exception as exc:  # noqa: BLE001
        # Never let a notification failure crash the request/job.
        logger.warning("WhatsApp send failed to %s: %s", to, exc)


def customer_order_status_whatsapp_message(*, order_number: str, status: str, tracking_number: str | None) -> str:
    tracking = f"\nTracking: {tracking_number}" if tracking_number else ""
    status_label = status.replace("_", " ").title()
    return (
        f"[ORDER UPDATE] Hiar Business\n\n"
        f"Your order *{order_number}* is now: *{status_label}*{tracking}\n\n"
        f"Reply with your order number at any time for live status."
    )


def customer_package_received_whatsapp_message(*, order_number: str, tracking_number: str) -> str:
    return (
        f"[PACKAGE RECEIVED] Hiar Business\n\n"
        f"Your package for order *{order_number}* has arrived at our Vietnam warehouse "
        f"and is being processed.\n"
        f"Tracking: {tracking_number}\n\n"
        f"We will notify you when it is dispatched to Kenya."
    )


def customer_customs_cleared_whatsapp_message(*, order_number: str, tracking_number: str) -> str:
    return (
        f"[READY FOR PICKUP] Hiar Business\n\n"
        f"Order *{order_number}* has cleared Kenya customs and is ready for collection "
        f"at our Nairobi office.\n"
        f"Tracking: {tracking_number}\n\n"
        f"Our team will be in touch with collection details."
    )


def customer_departed_vietnam_whatsapp_message(*, order_number: str) -> str:
    return (
        f"[ORDER DISPATCHED] Hiar Business\n\n"
        f"Your order *{order_number}* has left our Vietnam warehouse and is on its way "
        f"to Kenya. Expected transit time: 5–7 business days.\n\n"
        f"We will update you once it clears customs."
    )


def supplier_order_whatsapp_message(*, supplier_name: str, order_number: str, product_lines: list[str]) -> str:
    lines = [f"Hello {supplier_name}, new order to produce: *{order_number}*."]
    lines.extend(f"• {line}" for line in product_lines)
    lines.append("\nPlease confirm receipt and expected completion date.")
    return "\n".join(lines)

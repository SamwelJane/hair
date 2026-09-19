"""Meta WhatsApp Business Cloud API webhook handler.

Registers two endpoints at /webhooks/whatsapp:

GET  /webhooks/whatsapp  — Hub verification handshake (Meta requires this on
                           webhook registration). Validates the hub.verify_token
                           and echoes back hub.challenge.

POST /webhooks/whatsapp  — Inbound message handler. Parses incoming WhatsApp
                           messages and runs a simple two-way interactive bot:

  Customer sends:  → any text containing an order number (e.g. ORD-20250918-00123)
  Bot replies:     → live order status + next step description

  Customer sends "HELP" or unrecognised text → usage instructions.

Meta webhook payload reference:
  https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples
"""

from __future__ import annotations

import re

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import get_db
from app.integrations.meta_whatsapp import send_text_message
from app.models.orders import Order
from app.services.order_state_machine import CLIENT_STEPPER_GROUPS

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/webhooks/whatsapp", tags=["webhooks"])

_ORDER_NUMBER_RE = re.compile(r"\bORD-\d{8}-\d{5}\b", re.IGNORECASE)

_STATUS_DESCRIPTIONS: dict[str, str] = {
    "PENDING_PAYMENT":        "Waiting for your payment confirmation.",
    "PAID":                   "Payment confirmed — we're preparing your order.",
    "SENT_TO_SUPPLIER":       "Order sent to the factory for production.",
    "SUPPLIER_PROCESSING":    "Your hair is being crafted — this can take 7–14 days.",
    "READY_FOR_PICKUP":       "Production complete. Being packed and dispatched from Vietnam.",
    "RECEIVED_AT_OFFICE":     "Arrived at our Vietnam office, ready for air freight.",
    "SHIPPED_INTERNATIONALLY":"Dispatched internationally — on its way to Kenya.",
    "IN_TRANSIT":             "Clearing customs in Kenya.",
    "DELIVERED":              "Delivered — thank you for choosing Hiar Business.",
    "CANCELLED":              "Order cancelled. Contact us if this was a mistake.",
}


# ── GET — Hub Verification ────────────────────────────────────────────────────

@router.get("")
async def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> Response:
    settings = get_settings()
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_whatsapp_verify_token:
        return Response(content=hub_challenge or "", media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification token mismatch")


# ── POST — Inbound Message Bot ────────────────────────────────────────────────

@router.post("")
async def receive_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Process inbound messages from Meta. Always returns 200 immediately to
    prevent Meta from retrying on a slow bot reply (replies are fire-and-forget
    after we acknowledge)."""
    try:
        payload = await request.json()
    except Exception:
        # Malformed body — still 200 so Meta doesn't keep retrying
        return {"status": "ignored"}

    log.debug("meta_whatsapp.webhook_received", payload=payload)

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                sender = message.get("from")  # E.164 phone number
                msg_type = message.get("type")

                if msg_type != "text":
                    # Ignore non-text (images, stickers, reactions, etc.)
                    continue

                body: str = message.get("text", {}).get("body", "").strip()
                if not body or not sender:
                    continue

                # Run the bot in the background (non-blocking reply)
                await _handle_inbound_text(db=db, sender=sender, body=body)

    return {"status": "ok"}


async def _handle_inbound_text(*, db: AsyncSession, sender: str, body: str) -> None:
    """Parse inbound text and reply with live order status or help text."""
    upper = body.upper()

    # Check if the message contains an order number
    matches = _ORDER_NUMBER_RE.findall(body)
    if matches:
        order_number = matches[0].upper()
        reply = await _build_status_reply(db, order_number)
    elif upper in ("HELP", "HI", "HELLO", "STATUS"):
        reply = (
            "*Hi! Welcome to Hiar Business.*\n\n"
            "To check your order status, simply send your order number "
            "(e.g. *ORD-20250918-00123*).\n\n"
            "You can find your order number in your confirmation email or "
            "SMS from us."
        )
    else:
        reply = (
            "*Hiar Business Support*\n\n"
            "To track your order, please reply with your order number "
            "(e.g. *ORD-20250918-00123*).\n\n"
            "If you need further assistance, call us at +254 700 000 000."
        )

    try:
        await send_text_message(sender, reply)
    except Exception as exc:
        log.warning("meta_whatsapp.bot_reply_failed", sender=sender, error=str(exc))


async def _build_status_reply(db: AsyncSession, order_number: str) -> str:
    order = await db.scalar(
        select(Order).where(Order.order_number == order_number.upper())
    )
    if order is None:
        return (
            f"[NOT FOUND] Order *{order_number}* was not found.\n\n"
            "Please check the order number and try again, or contact us "
            "at +254 700 000 000."
        )

    status = order.status.value
    description = _STATUS_DESCRIPTIONS.get(status, status.replace("_", " ").title())

    # Determine progress step from CLIENT_STEPPER_GROUPS
    step_label = "Processing"
    for group in CLIENT_STEPPER_GROUPS:
        if order.status in group["statuses"]:
            step_label = group["label"]
            break

    tracking_line = f"\nTracking Number: `{order.tracking_number}`" if order.tracking_number else ""

    return (
        f"[ORDER STATUS] {order_number}\n\n"
        f"Stage: *{step_label}*\n"
        f"Status: *{status.replace('_', ' ').title()}*\n"
        f"{description}{tracking_line}\n\n"
        f"Reply HELP for assistance."
    )


"""Meta WhatsApp Business Cloud API integration.

Replaces the old Twilio-based send_whatsapp() helper with a direct HTTPS call
to Meta's Cloud API (graph.facebook.com/v19.0/{phone_number_id}/messages).

Features:
- Outbound text messages (milestone alerts, order confirmations)
- Outbound template messages (pre-approved Business templates)
- Inbound webhook: GET (hub challenge) + POST (interactive bot)
- Graceful mock fallback when META_WHATSAPP_TOKEN is absent (dev/test)

Environment variables (set via Settings in core/config.py):
    META_WHATSAPP_TOKEN              — Bearer token from Meta Business Suite
    META_WHATSAPP_PHONE_NUMBER_ID    — Phone Number ID for your WhatsApp Business number
    META_WHATSAPP_VERIFY_TOKEN       — Arbitrary secret for webhook hub verification
"""

from __future__ import annotations

import re

import httpx
import structlog

from app.core.config import get_settings

log = structlog.get_logger(__name__)

META_GRAPH_URL = "https://graph.facebook.com/v19.0"

# Maximum characters per single WhatsApp text message
_MAX_MSG_LEN = 4096


def normalize_phone_e164(phone: str) -> str:
    """Normalize phone number to E.164 digits format (e.g. 254712345678)."""
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("0") and len(digits) == 10:
        return "254" + digits[1:]
    if len(digits) == 9 and (digits.startswith("7") or digits.startswith("1")):
        return "254" + digits
    return digits


async def send_text_message(to: str, body: str) -> dict:
    """Send a plain-text WhatsApp message to the given phone number (E.164).

    Returns the raw Meta API response dict on success. In dev/test when no
    token is configured, logs the would-be message and returns a mock dict.
    """
    settings = get_settings()
    normalized_to = normalize_phone_e164(to)

    if not settings.meta_whatsapp_token or not settings.meta_whatsapp_phone_number_id or settings.meta_whatsapp_token in ("placeholder", "your-whatsapp-token"):
        log.info(
            "meta_whatsapp.mock_send",
            to=normalized_to,
            body_preview=body[:80],
        )
        return {"mock": True, "to": normalized_to, "status": "skipped_no_token"}

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": normalized_to,
        "type": "text",
        "text": {"preview_url": False, "body": body[:_MAX_MSG_LEN]},
    }

    url = f"{META_GRAPH_URL}/{settings.meta_whatsapp_phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.meta_whatsapp_token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json=payload, headers=headers)

    if resp.is_error:
        log.error(
            "meta_whatsapp.send_failed",
            to=normalized_to,
            status_code=resp.status_code,
            body=resp.text[:500],
        )
        resp.raise_for_status()

    result = resp.json()
    log.info("meta_whatsapp.sent", to=normalized_to, message_id=result.get("messages", [{}])[0].get("id"))
    return result


async def send_template_message(to: str, template_name: str, language_code: str = "en_US", components: list | None = None) -> dict:
    """Send a pre-approved WhatsApp Business template message.

    components follows Meta's component format:
        [{"type": "header", "parameters": [...]}, {"type": "body", "parameters": [...]}]
    """
    settings = get_settings()
    normalized_to = normalize_phone_e164(to)

    if not settings.meta_whatsapp_token or not settings.meta_whatsapp_phone_number_id or settings.meta_whatsapp_token in ("placeholder", "your-whatsapp-token"):
        log.info(
            "meta_whatsapp.mock_template",
            to=normalized_to,
            template=template_name,
        )
        return {"mock": True, "to": normalized_to, "template": template_name, "status": "skipped_no_token"}

    payload: dict = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": normalized_to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
        },
    }
    if components:
        payload["template"]["components"] = components

    url = f"{META_GRAPH_URL}/{settings.meta_whatsapp_phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.meta_whatsapp_token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json=payload, headers=headers)

    if resp.is_error:
        log.error(
            "meta_whatsapp.template_failed",
            to=normalized_to,
            template=template_name,
            status_code=resp.status_code,
            body=resp.text[:500],
        )
        resp.raise_for_status()

    result = resp.json()
    log.info("meta_whatsapp.template_sent", to=normalized_to, template=template_name, message_id=result.get("messages", [{}])[0].get("id"))
    return result


# ── Milestone message builders ────────────────────────────────────────────────

def departed_vietnam_message(order_number: str) -> str:
    return (
        f"[ORDER DISPATCHED] Hiar Business Update\n\n"
        f"Great news! Your order {order_number} has been dispatched from our Vietnam "
        f"warehouse and is in transit to Kenya.\n\n"
        f"You will receive another update once it clears customs and is ready for collection."
    )


def ready_for_pickup_message(order_number: str) -> str:
    return (
        f"[READY FOR PICKUP] Hiar Business\n\n"
        f"Order {order_number} has cleared Kenya customs and is ready for collection "
        f"at our Nairobi office.\n\n"
        f"Reply with your order number at any time to check your delivery status."
    )


def order_status_message(order_number: str, status: str, tracking_number: str | None = None) -> str:
    tracking_line = f"\nTracking: {tracking_number}" if tracking_number else ""
    return (
        f"[STATUS UPDATE] Hiar Business\n\n"
        f"Order {order_number} is now: {status.replace('_', ' ').title()}{tracking_line}\n\n"
        f"Reply with your order number for live status."
    )



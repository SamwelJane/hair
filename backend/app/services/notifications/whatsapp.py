import logging

from twilio.rest import Client as TwilioClient

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_client() -> TwilioClient | None:
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        return None
    return TwilioClient(settings.twilio_account_sid, settings.twilio_auth_token)


async def send_whatsapp(to: str, body: str) -> None:
    """Port of src/lib/notifications/whatsapp.ts. No-ops with a log warning
    if Twilio isn't configured, exactly like the old app."""
    client = _get_client()
    if client is None:
        logger.warning("Twilio not configured - skipping WhatsApp send to %s", to)
        return

    client.messages.create(from_=settings.twilio_whatsapp_from, to=f"whatsapp:{to}", body=body)


def customer_order_status_whatsapp_message(*, order_number: str, status: str, tracking_number: str | None) -> str:
    tracking = f" Tracking number: {tracking_number}." if tracking_number else ""
    status_label = status.replace("_", " ").lower()
    return f"Hiar Business update: order {order_number} is now {status_label}.{tracking}"


def customer_package_received_whatsapp_message(*, order_number: str, tracking_number: str) -> str:
    return (
        f"Hiar Business update: your package for order {order_number} has arrived at our Vietnam warehouse "
        f"and is being processed. Tracking number: {tracking_number}."
    )


def customer_customs_cleared_whatsapp_message(*, order_number: str, tracking_number: str) -> str:
    return (
        f"Hiar Business update: your order {order_number} has cleared customs in Kenya and is ready for delivery. "
        f"Tracking number: {tracking_number}."
    )


def supplier_order_whatsapp_message(*, supplier_name: str, order_number: str, product_lines: list[str]) -> str:
    lines = [f"Hello {supplier_name}, new order to produce: {order_number}."]
    lines.extend(f"- {line}" for line in product_lines)
    lines.append("Please confirm receipt and expected completion time.")
    return "\n".join(lines)

import logging

import resend

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def send_email(to: str, subject: str, html: str) -> None:
    """Port of src/lib/notifications/email.ts. No-ops with a log warning if
    RESEND_API_KEY isn't configured, exactly like the old app - email is
    never a hard dependency for a request to succeed."""
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not set - skipping email to %s (%s)", to, subject)
        return

    resend.api_key = settings.resend_api_key
    resend.Emails.send(
        {
            "from": settings.email_from,
            "to": [to],
            "subject": subject,
            "html": html,
        }
    )


async def send_password_reset_email(to: str, raw_token: str) -> None:
    reset_link = f"{settings.frontend_url}/reset-password?token={raw_token}"
    await send_email(
        to,
        subject="Reset your password",
        html=f'<p>Click <a href="{reset_link}">here</a> to reset your password. This link expires in 30 minutes.</p>',
    )


def supplier_order_email(*, supplier_name: str, order_number: str, product_lines: list[str]) -> tuple[str, str]:
    """Returns (subject, html). Port of src/lib/notifications/email.ts
    supplierOrderEmail()."""
    subject = f"New order to produce: {order_number}"
    items_html = "".join(f"<li>{line}</li>" for line in product_lines)
    html = f"""
      <p>Hello {supplier_name},</p>
      <p>A new order has been sent to you for production:</p>
      <ul>{items_html}</ul>
      <p>Order reference: <strong>{order_number}</strong></p>
      <p>Please confirm receipt and expected completion time.</p>
    """
    return subject, html


def supplier_order_status_change_email(
    *, supplier_name: str, order_number: str, status: str, eta_days: int | None, decline_reason: str | None
) -> tuple[str, str]:
    """Internal ops notification (not sent to the supplier or customer)
    whenever a supplier updates their portion of an order. Port of
    src/lib/notifications/email.ts supplierOrderStatusChangeEmail()."""
    if status == "DECLINED":
        detail = f"<p>Decline reason: <strong>{decline_reason or '(none given)'}</strong></p>"
    elif eta_days:
        detail = f"<p>Supplier's estimated completion: <strong>{eta_days} day(s)</strong></p>"
    else:
        detail = ""

    subject = f"Supplier update on {order_number}: {status}"
    html = f"""
      <p>{supplier_name} updated order <strong>{order_number}</strong> to <strong>{status}</strong>.</p>
      {detail}
    """
    return subject, html

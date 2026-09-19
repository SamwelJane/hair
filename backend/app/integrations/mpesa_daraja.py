import base64
import logging
import re
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from math import ceil

import httpx
from pydantic import BaseModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def normalize_kenyan_phone(phone: str) -> str:
    """Normalize Kenyan phone number to 254XXXXXXXXX format."""
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("254") and len(digits) == 12:
        return digits
    if digits.startswith("0") and len(digits) == 10:
        return "254" + digits[1:]
    if len(digits) == 9 and (digits.startswith("7") or digits.startswith("1")):
        return "254" + digits
    if digits.startswith("254") and len(digits) > 12:
        return digits[:12]
    return digits


def is_mpesa_configured() -> bool:
    """Check if valid M-Pesa Daraja API credentials are configured."""
    return bool(
        settings.mpesa_consumer_key
        and settings.mpesa_consumer_key.strip()
        and settings.mpesa_consumer_key.strip() not in ("your-consumer-key", "placeholder", "none")
        and settings.mpesa_consumer_secret
        and settings.mpesa_consumer_secret.strip()
        and settings.mpesa_consumer_secret.strip() not in ("your-consumer-secret", "placeholder", "none")
        and settings.mpesa_passkey
        and settings.mpesa_passkey.strip()
        and settings.mpesa_passkey.strip() not in ("your-passkey", "placeholder", "none")
    )


def _base_url() -> str:
    return "https://api.safaricom.co.ke" if settings.mpesa_env == "production" else "https://sandbox.safaricom.co.ke"


class StkPushResponse(BaseModel):
    MerchantRequestID: str
    CheckoutRequestID: str
    ResponseCode: str
    ResponseDescription: str
    CustomerMessage: str


async def _get_access_token() -> str:
    credentials = f"{settings.mpesa_consumer_key}:{settings.mpesa_consumer_secret}"
    auth = base64.b64encode(credentials.encode("utf-8")).decode("ascii")

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_base_url()}/oauth/v1/generate",
            params={"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {auth}"},
        )
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to get Daraja access token: {resp.status_code}")
    return resp.json()["access_token"]


def _build_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d%H%M%S")


async def stk_push(*, phone: str, amount_kes: Decimal, account_reference: str, transaction_desc: str) -> StkPushResponse:
    """Initiate M-Pesa STK push. Supports both live Daraja API and mock fallback."""
    normalized_phone = normalize_kenyan_phone(phone)

    if not is_mpesa_configured():
        logger.warning(
            "Daraja credentials not configured in settings. Returning simulated STK push success for %s (Amount KES: %s)",
            normalized_phone,
            amount_kes,
        )
        return StkPushResponse(
            MerchantRequestID=f"MOCK-MERCHANT-{uuid.uuid4().hex[:8].upper()}",
            CheckoutRequestID=f"ws_CO_{datetime.now(UTC).strftime('%d%m%Y%H%M%S')}_{uuid.uuid4().hex[:6]}",
            ResponseCode="0",
            ResponseDescription="Success. Request accepted for processing (simulated mock mode)",
            CustomerMessage="Success. Request accepted for processing",
        )

    shortcode = settings.mpesa_shortcode
    passkey = settings.mpesa_passkey
    timestamp = _build_timestamp()
    password = base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode("ascii")

    access_token = await _get_access_token()

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": ceil(amount_kes),
        "PartyA": normalized_phone,
        "PartyB": shortcode,
        "PhoneNumber": normalized_phone,
        "CallBackURL": settings.mpesa_callback_url,
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_base_url()}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if resp.status_code != 200:
        raise RuntimeError(f"Daraja STK push failed: {resp.status_code} {resp.text}")

    return StkPushResponse.model_validate(resp.json())


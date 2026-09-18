import base64
from datetime import UTC, datetime
from decimal import Decimal
from math import ceil

import httpx
from pydantic import BaseModel

from app.core.config import get_settings

settings = get_settings()


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
    """Direct port of src/lib/payments/mpesa/daraja-client.ts stkPush()."""
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
        "PartyA": phone,
        "PartyB": shortcode,
        "PhoneNumber": phone,
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

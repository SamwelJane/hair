import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_strict_admin
from app.core.rate_limit import get_client_ip, rate_limit
from app.models.enums import PaymentProviderType
from app.models.identity import User
from app.models.payments import Payment
from app.services import payments as payments_service

router = APIRouter(prefix="/payments", tags=["payments"])


class BankTransferConfirmRequest(BaseModel):
    payment_id: uuid.UUID


@router.post("/bank-transfer/confirm")
async def confirm_bank_transfer(
    payload: BankTransferConfirmRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_strict_admin),
) -> dict[str, bool]:
    try:
        await payments_service.confirm_bank_transfer_payment(db, payload.payment_id, admin.id)
    except payments_service.PaymentActionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


@router.post("/bank-transfer/reject")
async def reject_bank_transfer(
    payload: BankTransferConfirmRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_strict_admin),
) -> dict[str, bool]:
    try:
        await payments_service.reject_bank_transfer_payment(db, payload.payment_id, admin.id)
    except payments_service.PaymentActionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


@router.post("/mpesa/callback")
async def mpesa_callback(request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Safaricom Daraja STK push result webhook.

    NOTE: Safaricom does not sign this callback by default - the trust
    anchor is that we only ever act when CheckoutRequestID matches a payment
    we ourselves initiated (see lookup below); an attacker can't invent a
    valid ref. TODO before production M-Pesa go-live: add IP allowlisting
    and/or a shared-secret query param per Safaricom's current Daraja docs -
    deferred because the exact mechanism needs verifying against their
    current API, not something to guess at here.
    """
    ip = get_client_ip(dict(request.headers), request.client.host if request.client else None)
    if not await rate_limit(f"mpesa-callback:{ip}", limit=60, window_seconds=60):
        return {"ResultCode": 1, "ResultDesc": "Rate limited"}

    payload = await request.json()
    callback = payload["Body"]["stkCallback"]

    payment = await db.scalar(
        select(Payment).where(
            Payment.provider == PaymentProviderType.MPESA, Payment.provider_ref == callback["CheckoutRequestID"]
        )
    )
    if payment is None:
        # Acknowledge anyway so Safaricom doesn't retry indefinitely on an
        # unknown ref.
        return {"ResultCode": 0, "ResultDesc": "Accepted"}

    is_success = callback["ResultCode"] == 0
    receipt_number = None
    for item in (callback.get("CallbackMetadata") or {}).get("Item", []):
        if item.get("Name") == "MpesaReceiptNumber":
            receipt_number = item.get("Value")
            break

    await payments_service.apply_mpesa_callback(
        db,
        payment,
        is_success=is_success,
        result_desc=callback.get("ResultDesc", ""),
        raw_payload=payload,
        receipt_number=str(receipt_number) if receipt_number is not None else None,
    )

    return {"ResultCode": 0, "ResultDesc": "Accepted"}

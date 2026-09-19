from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.routers.payments import mpesa_callback

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/mpesa")
async def mpesa_webhook_endpoint(
    request: Request, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """Endpoint for Safaricom Daraja STK callback configured at /webhooks/mpesa.

    Matches MPESA_CALLBACK_URL=https://api.hiarbusiness.com/webhooks/mpesa.
    Delegates directly to mpesa_callback implementation.
    """
    return await mpesa_callback(request, db)


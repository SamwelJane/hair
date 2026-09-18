from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_admin
from app.models.enums import PaymentProviderType, PaymentStatus
from app.models.payments import Payment
from app.schemas.admin_payments import AdminPaymentListItemOut, AdminPaymentsOut
from app.services import payments as payments_service

router = APIRouter(prefix="/admin/payments", tags=["admin-payments"], dependencies=[Depends(require_admin)])


def _to_out(payment: Payment) -> AdminPaymentListItemOut:
    return AdminPaymentListItemOut(
        id=payment.id,
        order_number=payment.order.order_number,
        customer_email=payment.order.user.email,
        provider=payment.provider,
        status=payment.status,
        amount_kes=payment.amount_kes,
        provider_ref=payment.provider_ref,
        confirmed_by_name=payment.confirmed_by.name if payment.confirmed_by else None,
        created_at=payment.created_at,
    )


@router.get("", response_model=AdminPaymentsOut)
async def list_admin_payments(db: AsyncSession = Depends(get_db)) -> AdminPaymentsOut:
    """Three independently-filtered views over the same Payment table,
    matching the old app's admin payments page - not a general paginated
    payments list (that isn't a need this page has)."""
    pending_bank_transfers = await payments_service.list_payments(
        db, provider=PaymentProviderType.BANK_TRANSFER, statuses=[PaymentStatus.INITIATED, PaymentStatus.PENDING]
    )
    mpesa_payments = await payments_service.list_payments(db, provider=PaymentProviderType.MPESA)
    resolved_bank_transfers = await payments_service.list_payments(
        db, provider=PaymentProviderType.BANK_TRANSFER, statuses=[PaymentStatus.SUCCESS, PaymentStatus.FAILED]
    )

    return AdminPaymentsOut(
        pending_bank_transfers=[_to_out(p) for p in pending_bank_transfers],
        mpesa_payments=[_to_out(p) for p in mpesa_payments],
        resolved_bank_transfers=[_to_out(p) for p in resolved_bank_transfers],
    )

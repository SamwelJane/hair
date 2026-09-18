import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.rate_limit import rate_limit
from app.models.enums import OrderStatus, PaymentProviderType, PaymentStatus
from app.models.orders import Order, OrderStatusHistory
from app.models.payments import Payment
from app.services.audit import log_audit


class PaymentActionError(Exception):
    pass


class PaymentNotFoundError(PaymentActionError):
    pass


class NotBankTransferError(PaymentActionError):
    pass


class RateLimitedError(PaymentActionError):
    pass


async def confirm_bank_transfer_payment(db: AsyncSession, payment_id: uuid.UUID, admin_user_id: uuid.UUID) -> None:
    if not await rate_limit(f"confirm-bank-transfer:{admin_user_id}", limit=30, window_seconds=60):
        raise RateLimitedError("Too many payment confirmations in a short time. Please slow down.")

    payment = await db.get(Payment, payment_id)
    if payment is None:
        raise PaymentNotFoundError("Payment not found")
    if payment.provider != PaymentProviderType.BANK_TRANSFER:
        raise NotBankTransferError("Not a bank transfer payment")

    payment.status = PaymentStatus.SUCCESS
    payment.confirmed_by_id = admin_user_id

    order = await db.get(Order, payment.order_id)
    if order is None:
        raise PaymentActionError("Order not found")
    from_status = order.status
    order.status = OrderStatus.PAID
    db.add(
        OrderStatusHistory(
            order_id=order.id,
            from_status=from_status,
            to_status=OrderStatus.PAID,
            changed_by_id=admin_user_id,
            note="Bank transfer manually confirmed by admin",
        )
    )

    await log_audit(
        db,
        user_id=admin_user_id,
        action="CONFIRM_BANK_TRANSFER_PAYMENT",
        entity_type="Payment",
        entity_id=str(payment.id),
        metadata={"orderId": str(payment.order_id), "amountKes": str(payment.amount_kes)},
    )
    await db.commit()


async def reject_bank_transfer_payment(db: AsyncSession, payment_id: uuid.UUID, admin_user_id: uuid.UUID) -> None:
    if not await rate_limit(f"reject-bank-transfer:{admin_user_id}", limit=30, window_seconds=60):
        raise RateLimitedError("Too many payment actions in a short time. Please slow down.")

    payment = await db.get(Payment, payment_id)
    if payment is None:
        raise PaymentNotFoundError("Payment not found")
    if payment.provider != PaymentProviderType.BANK_TRANSFER:
        raise NotBankTransferError("Not a bank transfer payment")

    payment.status = PaymentStatus.FAILED
    payment.confirmed_by_id = admin_user_id

    await log_audit(
        db,
        user_id=admin_user_id,
        action="REJECT_BANK_TRANSFER_PAYMENT",
        entity_type="Payment",
        entity_id=str(payment.id),
        metadata={"orderId": str(payment.order_id)},
    )
    await db.commit()


async def list_payments(
    db: AsyncSession, *, provider: PaymentProviderType | None = None, statuses: list[PaymentStatus] | None = None, limit: int = 50
) -> list[Payment]:
    """Backs the admin payments page (src/app/admin/payments/page.tsx in the
    old app split this into 3 differently-filtered queries against the same
    table - callers here pass the same filters per section)."""
    stmt = select(Payment).options(
        selectinload(Payment.order).selectinload(Order.user), selectinload(Payment.confirmed_by)
    )
    if provider is not None:
        stmt = stmt.where(Payment.provider == provider)
    if statuses:
        stmt = stmt.where(Payment.status.in_(statuses))
    stmt = stmt.order_by(Payment.created_at.desc()).limit(limit)
    return list((await db.execute(stmt)).scalars().all())


async def apply_mpesa_callback(db: AsyncSession, payment: Payment, *, is_success: bool, result_desc: str, raw_payload: dict[str, Any], receipt_number: str | None) -> None:
    """Idempotency guard vs. the old app: only applies the callback if the
    payment is still INITIATED/PENDING - a replayed or duplicate webhook call
    for an already-resolved payment is a no-op rather than re-writing order
    status history a second time."""
    if payment.status not in (PaymentStatus.INITIATED, PaymentStatus.PENDING):
        return

    payment.status = PaymentStatus.SUCCESS if is_success else PaymentStatus.FAILED
    if receipt_number:
        payment.provider_ref = receipt_number
    payment.raw_callback_payload = raw_payload

    if is_success:
        order = await db.get(Order, payment.order_id)
        if order is not None:
            from_status = order.status
            order.status = OrderStatus.PAID
            db.add(
                OrderStatusHistory(
                    order_id=order.id,
                    from_status=from_status,
                    to_status=OrderStatus.PAID,
                    note=f"M-Pesa payment confirmed ({result_desc})",
                )
            )

    await log_audit(
        db,
        user_id=None,
        action="MPESA_PAYMENT_SUCCESS" if is_success else "MPESA_PAYMENT_FAILED",
        entity_type="Payment",
        entity_id=str(payment.id),
        metadata={"resultDesc": result_desc, "orderId": str(payment.order_id)},
    )
    await db.commit()

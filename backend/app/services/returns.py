import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import OrderStatus, ReturnStatus
from app.models.orders import Order, Return
from app.services.audit import log_audit


class ReturnNotFoundError(Exception):
    pass


class OrderNotFoundError(Exception):
    pass


class OrderNotDeliveredError(Exception):
    pass


class OpenReturnAlreadyExistsError(Exception):
    pass


async def create_return(db: AsyncSession, *, user_id: uuid.UUID, order_id: uuid.UUID, reason: str) -> Return:
    """Customer-facing counterpart to resolve_return above. Unlike the old
    app (which only hid the request form once a Return row existed, with no
    DB-level guard), this rejects a new request outright while an
    unresolved one is still open - a deliberate hardening now that the
    endpoint is a real API surface shared by two frontends, not a
    UI-only rule."""
    order = await db.get(Order, order_id)
    if order is None or order.user_id != user_id:
        raise OrderNotFoundError(f"Order {order_id} not found")
    if order.status != OrderStatus.DELIVERED:
        raise OrderNotDeliveredError("Returns can only be requested for delivered orders.")

    open_return = await db.scalar(
        select(Return).where(Return.order_id == order_id, Return.status == ReturnStatus.REQUESTED)
    )
    if open_return is not None:
        raise OpenReturnAlreadyExistsError("A return request for this order is already pending.")

    return_request = Return(order_id=order_id, requested_by_id=user_id, reason=reason, status=ReturnStatus.REQUESTED)
    db.add(return_request)
    await db.flush()

    await log_audit(
        db, user_id=user_id, action="REQUEST_RETURN", entity_type="Return", entity_id=str(return_request.id),
        metadata={"orderId": str(order_id)},
    )
    await db.commit()
    await db.refresh(return_request)
    return return_request


async def resolve_return(
    db: AsyncSession,
    return_id: uuid.UUID,
    *,
    status: ReturnStatus,
    refund_amount_usd: Decimal | None,
    actor_user_id: uuid.UUID,
) -> Return:
    return_request = await db.get(Return, return_id)
    if return_request is None:
        raise ReturnNotFoundError(f"Return {return_id} not found")

    return_request.status = status
    return_request.refund_amount_usd = refund_amount_usd
    return_request.resolved_by_id = actor_user_id
    return_request.resolved_at = datetime.now(UTC)

    await log_audit(
        db,
        user_id=actor_user_id,
        action=f"RETURN_{status.value}",
        entity_type="Return",
        entity_id=str(return_id),
        metadata={"refundAmountUsd": str(refund_amount_usd) if refund_amount_usd is not None else None},
    )
    await db.commit()
    await db.refresh(return_request)
    return return_request

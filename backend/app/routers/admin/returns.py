import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_db, require_admin
from app.models.identity import User
from app.models.orders import Order, Return
from app.schemas.admin_moderation import ResolveReturnRequest, ReturnOut
from app.services import returns as returns_service

router = APIRouter(prefix="/admin/returns", tags=["admin-returns"], dependencies=[Depends(require_admin)])


def _to_out(r: Return) -> ReturnOut:
    return ReturnOut(
        id=r.id,
        order_id=r.order_id,
        order_number=r.order.order_number,
        customer_email=r.order.user.email,
        reason=r.reason,
        status=r.status,
        refund_amount_usd=r.refund_amount_usd,
        resolved_by_name=r.resolved_by.name if r.resolved_by else None,
        created_at=r.created_at,
    )


@router.get("", response_model=list[ReturnOut])
async def list_returns(db: AsyncSession = Depends(get_db)) -> list[ReturnOut]:
    returns = (
        (
            await db.execute(
                select(Return)
                .options(selectinload(Return.order).selectinload(Order.user), selectinload(Return.resolved_by))
                .order_by(Return.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return [_to_out(r) for r in returns]


@router.post("/{return_id}/resolve", response_model=ReturnOut)
async def resolve_return(
    return_id: uuid.UUID,
    payload: ResolveReturnRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ReturnOut:
    try:
        await returns_service.resolve_return(
            db, return_id, status=payload.status, refund_amount_usd=payload.refund_amount_usd, actor_user_id=admin.id
        )
    except returns_service.ReturnNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    reloaded = await db.get(
        Return,
        return_id,
        populate_existing=True,
        options=[selectinload(Return.order).selectinload(Order.user), selectinload(Return.resolved_by)],
    )
    assert reloaded is not None
    return _to_out(reloaded)

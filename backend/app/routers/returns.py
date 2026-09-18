from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.identity import User
from app.schemas.returns import CreateReturnRequest, MyReturnOut
from app.services import returns as returns_service

router = APIRouter(prefix="/returns", tags=["returns"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=MyReturnOut, status_code=status.HTTP_201_CREATED)
async def request_return(
    payload: CreateReturnRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> MyReturnOut:
    try:
        return_request = await returns_service.create_return(
            db, user_id=user.id, order_id=payload.order_id, reason=payload.reason
        )
    except returns_service.OrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except returns_service.OrderNotDeliveredError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except returns_service.OpenReturnAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return MyReturnOut(
        id=return_request.id, order_id=return_request.order_id, reason=return_request.reason,
        status=return_request.status, refund_amount_usd=return_request.refund_amount_usd,
        created_at=return_request.created_at,
    )

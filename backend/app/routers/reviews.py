from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.identity import User
from app.schemas.reviews import CreateReviewRequest, MyReviewOut
from app.services import reviews as reviews_service

# Sibling to routers/admin/reviews.py (moderation), not nested under it -
# this is the customer-facing counterpart.
router = APIRouter(prefix="/reviews", tags=["reviews"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=MyReviewOut, status_code=status.HTTP_201_CREATED)
async def submit_review(
    payload: CreateReviewRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> MyReviewOut:
    try:
        review = await reviews_service.create_review(
            db, user_id=user.id, order_id=payload.order_id, product_id=payload.product_id,
            rating=payload.rating, body=payload.body,
        )
    except reviews_service.OrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (reviews_service.OrderNotDeliveredError, reviews_service.ProductNotInOrderError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except reviews_service.DuplicateReviewError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return MyReviewOut(
        id=review.id, product_id=review.product_id, order_id=review.order_id, rating=review.rating,
        body=review.body, status=review.status, created_at=review.created_at,
    )

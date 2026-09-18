import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_db, require_admin
from app.models.identity import User
from app.models.orders import Review
from app.schemas.admin_moderation import ModerateReviewRequest, ReviewOut
from app.services import reviews as reviews_service

router = APIRouter(prefix="/admin/reviews", tags=["admin-reviews"], dependencies=[Depends(require_admin)])


def _to_out(r: Review) -> ReviewOut:
    return ReviewOut(
        id=r.id, product_name=r.product.name, user_name=r.user.name, rating=r.rating, body=r.body,
        status=r.status, created_at=r.created_at,
    )


@router.get("", response_model=list[ReviewOut])
async def list_reviews(db: AsyncSession = Depends(get_db)) -> list[ReviewOut]:
    reviews = (
        (
            await db.execute(
                select(Review)
                .options(selectinload(Review.product), selectinload(Review.user))
                .order_by(Review.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return [_to_out(r) for r in reviews]


@router.post("/{review_id}/moderate", response_model=ReviewOut)
async def moderate_review(
    review_id: uuid.UUID,
    payload: ModerateReviewRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ReviewOut:
    try:
        await reviews_service.moderate_review(db, review_id, status=payload.status, actor_user_id=admin.id)
    except reviews_service.ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    reloaded = await db.get(
        Review, review_id, populate_existing=True, options=[selectinload(Review.product), selectinload(Review.user)]
    )
    assert reloaded is not None
    return _to_out(reloaded)

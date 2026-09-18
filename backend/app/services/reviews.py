import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import OrderStatus, ReviewStatus
from app.models.orders import Order, Review
from app.services.audit import log_audit


class ReviewNotFoundError(Exception):
    pass


class OrderNotFoundError(Exception):
    pass


class OrderNotDeliveredError(Exception):
    pass


class ProductNotInOrderError(Exception):
    pass


class DuplicateReviewError(Exception):
    pass


async def create_review(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    order_id: uuid.UUID,
    product_id: uuid.UUID,
    rating: int,
    body: str,
) -> Review:
    """Customer-facing counterpart to moderate_review above. Unlike the old
    app's submitReview (which trusted a hidden productId form field without
    checking it belonged to the order), this validates product_id is
    actually one of the order's items - a deliberate hardening now that the
    endpoint is a real API surface, not a same-origin form post."""
    order = await db.get(Order, order_id, options=[selectinload(Order.items)])
    if order is None or order.user_id != user_id:
        raise OrderNotFoundError(f"Order {order_id} not found")
    if order.status != OrderStatus.DELIVERED:
        raise OrderNotDeliveredError("You can only review delivered orders.")
    if not any(item.product_id == product_id for item in order.items):
        raise ProductNotInOrderError("This product is not part of that order.")

    existing = await db.scalar(
        select(Review).where(Review.order_id == order_id, Review.user_id == user_id, Review.product_id == product_id)
    )
    if existing is not None:
        raise DuplicateReviewError("You've already reviewed this product for this order.")

    review = Review(product_id=product_id, user_id=user_id, order_id=order_id, rating=rating, body=body, status=ReviewStatus.PENDING)
    db.add(review)
    await db.flush()

    await log_audit(
        db, user_id=user_id, action="CREATE_REVIEW", entity_type="Review", entity_id=str(review.id),
        metadata={"orderId": str(order_id), "productId": str(product_id)},
    )
    await db.commit()
    await db.refresh(review)
    return review


async def moderate_review(
    db: AsyncSession, review_id: uuid.UUID, *, status: ReviewStatus, actor_user_id: uuid.UUID
) -> Review:
    review = await db.get(Review, review_id)
    if review is None:
        raise ReviewNotFoundError(f"Review {review_id} not found")

    review.status = status
    await log_audit(
        db,
        user_id=actor_user_id,
        action=f"REVIEW_{status.value.upper()}",
        entity_type="Review",
        entity_id=str(review_id),
    )
    await db.commit()
    await db.refresh(review)
    return review

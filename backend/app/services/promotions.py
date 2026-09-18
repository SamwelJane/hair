"""Supplier Promotions Service.

Manages the full lifecycle of supplier promotion requests:
  1. Supplier submits a request for a placement slot (HERO_BANNER, FLASH_DEAL, etc.)
  2. Admin reviews and approves/rejects with optional notes.
  3. On approval, start_date/end_date are set and the product's discount_pct is
     automatically calculated from the difference between the marked-up price
     and any discount the supplier wants to advertise.
  4. Expiry is detected lazily (on every list/detail read) by comparing
     end_date to UTC now.

Rate cards (USD/7 days) — these are the platform defaults; admin can override
per-slot when creating the approval:
  HERO_BANNER  : $150
  FLASH_DEAL   : $80
  CATEGORY_TOP : $50
  TRENDING_BADGE: $30
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.catalog import Product
from app.models.enums import PromotionSlot, PromotionStatus
from app.models.promotions import SupplierPromotionRequest
from app.services.audit import log_audit

# Default 7-day rate card (USD)
RATE_CARD: dict[PromotionSlot, Decimal] = {
    PromotionSlot.HERO_BANNER:    Decimal("150.00"),
    PromotionSlot.FLASH_DEAL:     Decimal("80.00"),
    PromotionSlot.CATEGORY_TOP:   Decimal("50.00"),
    PromotionSlot.TRENDING_BADGE: Decimal("30.00"),
}

DEFAULT_DURATION_DAYS = 7


class PromotionNotFoundError(Exception):
    pass


class PromotionPermissionError(Exception):
    pass


class PromotionTransitionError(Exception):
    pass


async def create_promotion_request(
    db: AsyncSession,
    *,
    supplier_id: uuid.UUID,
    product_id: uuid.UUID,
    slot_type: PromotionSlot,
    duration_days: int = DEFAULT_DURATION_DAYS,
    banner_image_url: str | None = None,
    custom_headline: str | None = None,
) -> SupplierPromotionRequest:
    """Supplier submits a new promotion placement request."""
    # Verify the product belongs to this supplier
    product = await db.get(Product, product_id)
    if product is None or product.supplier_id != supplier_id:
        raise PromotionPermissionError("Product not found or does not belong to your account.")

    rate_usd = RATE_CARD.get(slot_type, Decimal("50.00"))

    promo = SupplierPromotionRequest(
        supplier_id=supplier_id,
        product_id=product_id,
        slot_type=slot_type,
        rate_usd=rate_usd,
        duration_days=duration_days,
        status=PromotionStatus.PENDING,
        banner_image_url=banner_image_url,
        custom_headline=custom_headline,
    )
    db.add(promo)
    await log_audit(
        db,
        user_id=supplier_id,
        action="PROMOTION_REQUEST_CREATED",
        entity_type="SupplierPromotionRequest",
        entity_id=str(promo.id) if promo.id else "pending",
        metadata={"slot": slot_type.value, "product_id": str(product_id)},
    )
    await db.commit()
    await db.refresh(promo)
    return promo


async def list_supplier_promotions(
    db: AsyncSession,
    *,
    supplier_id: uuid.UUID,
) -> list[SupplierPromotionRequest]:
    """List all promotions submitted by this supplier."""
    stmt = (
        select(SupplierPromotionRequest)
        .where(SupplierPromotionRequest.supplier_id == supplier_id)
        .options(selectinload(SupplierPromotionRequest.product))
        .order_by(SupplierPromotionRequest.created_at.desc())
    )
    results = list((await db.execute(stmt)).scalars().all())
    _expire_promotions(results)
    return results


async def list_all_promotions(
    db: AsyncSession,
    *,
    status: PromotionStatus | None = None,
) -> list[SupplierPromotionRequest]:
    """Admin: list all promotion requests, optionally filtered by status."""
    stmt = (
        select(SupplierPromotionRequest)
        .options(
            selectinload(SupplierPromotionRequest.product),
            selectinload(SupplierPromotionRequest.supplier),
            selectinload(SupplierPromotionRequest.reviewed_by),
        )
        .order_by(SupplierPromotionRequest.created_at.desc())
    )
    if status is not None:
        stmt = stmt.where(SupplierPromotionRequest.status == status)
    results = list((await db.execute(stmt)).scalars().all())
    _expire_promotions(results)
    return results


async def approve_promotion(
    db: AsyncSession,
    *,
    promotion_id: uuid.UUID,
    admin_user_id: uuid.UUID,
    admin_notes: str | None = None,
    start_date: datetime | None = None,
    duration_days: int | None = None,
) -> SupplierPromotionRequest:
    """Admin approves a pending promotion request and activates it."""
    promo = await db.get(SupplierPromotionRequest, promotion_id, options=[selectinload(SupplierPromotionRequest.product)])
    if promo is None:
        raise PromotionNotFoundError(f"Promotion {promotion_id} not found.")
    if promo.status not in (PromotionStatus.PENDING, PromotionStatus.APPROVED):
        raise PromotionTransitionError(f"Cannot approve promotion with status {promo.status.value}.")

    now = datetime.now(UTC)
    effective_start = start_date or now
    effective_duration = duration_days or promo.duration_days
    effective_end = effective_start + timedelta(days=effective_duration)

    promo.status = PromotionStatus.ACTIVE
    promo.start_date = effective_start
    promo.duration_days = effective_duration
    promo.end_date = effective_end
    promo.reviewed_by_id = admin_user_id
    promo.admin_notes = admin_notes

    # Auto-compute product discount_pct from slot type (visual indicator only —
    # actual price is marked up at pricing_engine level, not changed here)
    _apply_promotion_badge(promo.product, promo.slot_type)

    await log_audit(
        db,
        user_id=admin_user_id,
        action="PROMOTION_APPROVED",
        entity_type="SupplierPromotionRequest",
        entity_id=str(promotion_id),
        metadata={
            "slot": promo.slot_type.value,
            "start": effective_start.isoformat(),
            "end": effective_end.isoformat(),
        },
    )
    await db.commit()
    await db.refresh(promo)
    return promo


async def reject_promotion(
    db: AsyncSession,
    *,
    promotion_id: uuid.UUID,
    admin_user_id: uuid.UUID,
    admin_notes: str | None = None,
) -> SupplierPromotionRequest:
    """Admin rejects a pending promotion request."""
    promo = await db.get(SupplierPromotionRequest, promotion_id)
    if promo is None:
        raise PromotionNotFoundError(f"Promotion {promotion_id} not found.")
    if promo.status != PromotionStatus.PENDING:
        raise PromotionTransitionError(f"Cannot reject promotion with status {promo.status.value}.")

    promo.status = PromotionStatus.REJECTED
    promo.reviewed_by_id = admin_user_id
    promo.admin_notes = admin_notes

    await log_audit(
        db,
        user_id=admin_user_id,
        action="PROMOTION_REJECTED",
        entity_type="SupplierPromotionRequest",
        entity_id=str(promotion_id),
        metadata={"notes": admin_notes},
    )
    await db.commit()
    await db.refresh(promo)
    return promo


# ── Internal helpers ──────────────────────────────────────────────────────────

def _expire_promotions(promos: list[SupplierPromotionRequest]) -> None:
    """Lazily mark ACTIVE promotions past their end_date as EXPIRED.
    This is a best-effort in-memory flag; the DB write is deferred so that
    listing endpoints stay fast. A background job (or the next mutation) will
    persist the EXPIRED status."""
    now = datetime.now(UTC)
    for p in promos:
        if p.status == PromotionStatus.ACTIVE and p.end_date and p.end_date < now:
            p.status = PromotionStatus.EXPIRED


def _apply_promotion_badge(product: Product | None, slot: PromotionSlot) -> None:
    """Sets a visual discount badge on the product based on slot type.
    Flash deals show the largest discount signal; other slots use a smaller
    badge. The actual retail price is NOT changed — the badge is informational.
    """
    if product is None:
        return
    badge_pcts: dict[PromotionSlot, Decimal] = {
        PromotionSlot.FLASH_DEAL:     Decimal("15.00"),
        PromotionSlot.HERO_BANNER:    Decimal("10.00"),
        PromotionSlot.CATEGORY_TOP:   Decimal("5.00"),
        PromotionSlot.TRENDING_BADGE: Decimal("0.00"),
    }
    product.discount_pct = badge_pcts.get(slot, Decimal("0.00"))


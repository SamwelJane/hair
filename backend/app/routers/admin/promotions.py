"""Admin Promotions Router — /admin/promotions

Gives admins full visibility and control over all supplier promotion requests:
  GET  /admin/promotions            — list all (filter by status)
  POST /admin/promotions/{id}/approve  — approve & activate a promotion
  POST /admin/promotions/{id}/reject   — reject a pending request
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user, require_admin
from app.models.enums import PromotionSlot, PromotionStatus
from app.models.identity import User
from app.models.promotions import SupplierPromotionRequest
from app.services import promotions as promotions_service

router = APIRouter(
    prefix="/admin/promotions",
    tags=["admin-promotions"],
    dependencies=[Depends(require_admin)],
)


# ── Schemas ───────────────────────────────────────────────────────────────────

class AdminPromotionOut(BaseModel):
    id: uuid.UUID
    supplier_name: str
    product_id: uuid.UUID
    product_name: str
    slot_type: PromotionSlot
    rate_usd: Decimal
    duration_days: int
    status: PromotionStatus
    start_date: datetime | None
    end_date: datetime | None
    banner_image_url: str | None
    custom_headline: str | None
    admin_notes: str | None
    reviewed_by_name: str | None
    impressions_count: int
    clicks_count: int
    orders_count: int
    created_at: datetime


class ApprovePromotionIn(BaseModel):
    admin_notes: str | None = None
    start_date: datetime | None = None
    duration_days: int | None = Field(default=None, ge=1, le=90)


class RejectPromotionIn(BaseModel):
    admin_notes: str = Field(min_length=3)


def _to_admin_out(promo: SupplierPromotionRequest) -> AdminPromotionOut:
    return AdminPromotionOut(
        id=promo.id,
        supplier_name=promo.supplier.name if promo.supplier else "Unknown",
        product_id=promo.product_id,
        product_name=promo.product.name if promo.product else "Unknown",
        slot_type=promo.slot_type,
        rate_usd=promo.rate_usd,
        duration_days=promo.duration_days,
        status=promo.status,
        start_date=promo.start_date,
        end_date=promo.end_date,
        banner_image_url=promo.banner_image_url,
        custom_headline=promo.custom_headline,
        admin_notes=promo.admin_notes,
        reviewed_by_name=promo.reviewed_by.name if promo.reviewed_by else None,
        impressions_count=promo.impressions_count,
        clicks_count=promo.clicks_count,
        orders_count=promo.orders_count,
        created_at=promo.created_at,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=list[AdminPromotionOut])
async def list_all_promotions(
    status: PromotionStatus | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[AdminPromotionOut]:
    promos = await promotions_service.list_all_promotions(db, status=status)
    return [_to_admin_out(p) for p in promos]


@router.post("/{promotion_id}/approve", response_model=AdminPromotionOut)
async def approve_promotion(
    promotion_id: uuid.UUID,
    payload: ApprovePromotionIn,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user),
) -> AdminPromotionOut:
    try:
        promo = await promotions_service.approve_promotion(
            db,
            promotion_id=promotion_id,
            admin_user_id=admin.id,
            admin_notes=payload.admin_notes,
            start_date=payload.start_date,
            duration_days=payload.duration_days,
        )
    except promotions_service.PromotionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except promotions_service.PromotionTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Reload with relationships for serialization
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select as sa_select
    promo = (
        await db.execute(
            sa_select(SupplierPromotionRequest)
            .where(SupplierPromotionRequest.id == promotion_id)
            .options(
                selectinload(SupplierPromotionRequest.supplier),
                selectinload(SupplierPromotionRequest.product),
                selectinload(SupplierPromotionRequest.reviewed_by),
            )
        )
    ).scalar_one_or_none()
    if promo is None:
        raise HTTPException(status_code=404, detail="Promotion not found")
    return _to_admin_out(promo)


@router.post("/{promotion_id}/reject", response_model=AdminPromotionOut)
async def reject_promotion(
    promotion_id: uuid.UUID,
    payload: RejectPromotionIn,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user),
) -> AdminPromotionOut:
    try:
        promo = await promotions_service.reject_promotion(
            db,
            promotion_id=promotion_id,
            admin_user_id=admin.id,
            admin_notes=payload.admin_notes,
        )
    except promotions_service.PromotionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except promotions_service.PromotionTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Reload with relationships
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select as sa_select
    promo = (
        await db.execute(
            sa_select(SupplierPromotionRequest)
            .where(SupplierPromotionRequest.id == promotion_id)
            .options(
                selectinload(SupplierPromotionRequest.supplier),
                selectinload(SupplierPromotionRequest.product),
                selectinload(SupplierPromotionRequest.reviewed_by),
            )
        )
    ).scalar_one_or_none()
    if promo is None:
        raise HTTPException(status_code=404, detail="Promotion not found")
    return _to_admin_out(promo)


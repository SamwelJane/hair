"""Supplier Promotions Router — /supplier/promotions

Allows suppliers to manage their own promotion requests:
  GET  /supplier/promotions         — list my promotions
  POST /supplier/promotions         — submit a new request
  GET  /supplier/promotions/{id}    — get one request
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_supplier, require_supplier
from app.models.catalog import Supplier
from app.models.enums import PromotionSlot, PromotionStatus
from app.models.promotions import SupplierPromotionRequest
from app.services import promotions as promotions_service

router = APIRouter(
    prefix="/supplier/promotions",
    tags=["supplier-promotions"],
    dependencies=[Depends(require_supplier)],
)


# ── Schemas ───────────────────────────────────────────────────────────────────

class PromotionRequestIn(BaseModel):
    product_id: uuid.UUID
    slot_type: PromotionSlot
    duration_days: int = Field(default=7, ge=1, le=90)
    banner_image_url: str | None = None
    custom_headline: str | None = Field(default=None, max_length=120)


class PromotionOut(BaseModel):
    id: uuid.UUID
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
    impressions_count: int
    clicks_count: int
    orders_count: int
    created_at: datetime


def _to_out(promo: SupplierPromotionRequest) -> PromotionOut:
    return PromotionOut(
        id=promo.id,
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
        impressions_count=promo.impressions_count,
        clicks_count=promo.clicks_count,
        orders_count=promo.orders_count,
        created_at=promo.created_at,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=list[PromotionOut])
async def list_my_promotions(
    db: AsyncSession = Depends(get_db),
    supplier: Supplier = Depends(get_current_supplier),
) -> list[PromotionOut]:
    promos = await promotions_service.list_supplier_promotions(db, supplier_id=supplier.id)
    return [_to_out(p) for p in promos]


@router.post("", response_model=PromotionOut, status_code=201)
async def create_promotion(
    payload: PromotionRequestIn,
    db: AsyncSession = Depends(get_db),
    supplier: Supplier = Depends(get_current_supplier),
) -> PromotionOut:
    try:
        promo = await promotions_service.create_promotion_request(
            db,
            supplier_id=supplier.id,
            product_id=payload.product_id,
            slot_type=payload.slot_type,
            duration_days=payload.duration_days,
            banner_image_url=payload.banner_image_url,
            custom_headline=payload.custom_headline,
        )
    except promotions_service.PromotionPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return _to_out(promo)


@router.get("/{promotion_id}", response_model=PromotionOut)
async def get_promotion(
    promotion_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    supplier: Supplier = Depends(get_current_supplier),
) -> PromotionOut:
    try:
        promo = await db.get(
            SupplierPromotionRequest,
            promotion_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Promotion not found") from exc

    if promo is None or promo.supplier_id != supplier.id:
        raise HTTPException(status_code=404, detail="Promotion not found")

    # Lazy load product
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select as sa_select
    promo = (
        await db.execute(
            sa_select(SupplierPromotionRequest)
            .where(SupplierPromotionRequest.id == promotion_id)
            .options(selectinload(SupplierPromotionRequest.product))
        )
    ).scalar_one_or_none()
    if promo is None:
        raise HTTPException(status_code=404, detail="Promotion not found")
    return _to_out(promo)


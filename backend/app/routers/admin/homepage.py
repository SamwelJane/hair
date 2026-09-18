import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_admin
from app.integrations.cloudinary_client import upload_image
from app.models.homepage import HomepageBanner, HomepageProductPlacement
from app.models.identity import User
from app.schemas.admin_products import (
    BannerOut,
    BannerRequest,
    ProductPlacementOut,
    ProductPlacementRequest,
    ProductPlacementUpdateRequest,
)
from app.services import homepage as homepage_service

router = APIRouter(prefix="/admin/homepage", tags=["admin-homepage"], dependencies=[Depends(require_admin)])


def _banner_out(banner: HomepageBanner) -> BannerOut:
    return BannerOut(
        id=banner.id, image_url=banner.image_url, headline=banner.headline, subheadline=banner.subheadline,
        cta_label=banner.cta_label, cta_url=banner.cta_url, sort_order=banner.sort_order, is_active=banner.is_active,
    )


def _placement_out(placement: HomepageProductPlacement) -> ProductPlacementOut:
    return ProductPlacementOut(
        id=placement.id, product_id=placement.product_id, product_name=placement.product.name,
        product_slug=placement.product.slug, section=placement.section, sale_price_usd=placement.sale_price_usd,
        starts_at=placement.starts_at, ends_at=placement.ends_at, sort_order=placement.sort_order,
        is_active=placement.is_active,
    )


@router.get("/banners", response_model=list[BannerOut])
async def list_banners(db: AsyncSession = Depends(get_db)) -> list[BannerOut]:
    return [_banner_out(b) for b in await homepage_service.list_banners(db)]


@router.post("/banners", response_model=BannerOut, status_code=201)
async def create_banner(
    payload: BannerRequest, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)
) -> BannerOut:
    banner = await homepage_service.create_banner(
        db, headline=payload.headline, subheadline=payload.subheadline, cta_label=payload.cta_label,
        cta_url=payload.cta_url, sort_order=payload.sort_order, is_active=payload.is_active, actor_user_id=admin.id,
    )
    return _banner_out(banner)


@router.patch("/banners/{banner_id}", response_model=BannerOut)
async def update_banner(
    banner_id: uuid.UUID, payload: BannerRequest, db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> BannerOut:
    try:
        banner = await homepage_service.update_banner(
            db, banner_id, headline=payload.headline, subheadline=payload.subheadline, cta_label=payload.cta_label,
            cta_url=payload.cta_url, sort_order=payload.sort_order, is_active=payload.is_active,
            actor_user_id=admin.id,
        )
    except homepage_service.BannerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _banner_out(banner)


@router.post("/banners/{banner_id}/image", response_model=BannerOut, status_code=201)
async def upload_banner_image(
    banner_id: uuid.UUID, file: UploadFile = File(...), db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> BannerOut:
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    url, public_id = upload_image(file_bytes, folder="hiar-business/homepage")
    try:
        banner = await homepage_service.set_banner_image(
            db, banner_id, image_url=url, cloudinary_public_id=public_id, actor_user_id=admin.id
        )
    except homepage_service.BannerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _banner_out(banner)


@router.delete("/banners/{banner_id}", status_code=204)
async def delete_banner(
    banner_id: uuid.UUID, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)
) -> None:
    try:
        await homepage_service.delete_banner(db, banner_id, actor_user_id=admin.id)
    except homepage_service.BannerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/product-placements", response_model=list[ProductPlacementOut])
async def list_placements(db: AsyncSession = Depends(get_db)) -> list[ProductPlacementOut]:
    return [_placement_out(p) for p in await homepage_service.list_placements(db)]


@router.post("/product-placements", response_model=ProductPlacementOut, status_code=201)
async def create_placement(
    payload: ProductPlacementRequest, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)
) -> ProductPlacementOut:
    placement = await homepage_service.create_placement(
        db, product_id=payload.product_id, section=payload.section, sale_price_usd=payload.sale_price_usd,
        starts_at=payload.starts_at, ends_at=payload.ends_at, sort_order=payload.sort_order,
        is_active=payload.is_active, actor_user_id=admin.id,
    )
    return _placement_out(placement)


@router.patch("/product-placements/{placement_id}", response_model=ProductPlacementOut)
async def update_placement(
    placement_id: uuid.UUID, payload: ProductPlacementUpdateRequest, db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ProductPlacementOut:
    try:
        placement = await homepage_service.update_placement(
            db, placement_id, section=payload.section, sale_price_usd=payload.sale_price_usd,
            starts_at=payload.starts_at, ends_at=payload.ends_at, sort_order=payload.sort_order,
            is_active=payload.is_active, actor_user_id=admin.id,
        )
    except homepage_service.PlacementNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _placement_out(placement)


@router.delete("/product-placements/{placement_id}", status_code=204)
async def delete_placement(
    placement_id: uuid.UUID, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)
) -> None:
    try:
        await homepage_service.delete_placement(db, placement_id, actor_user_id=admin.id)
    except homepage_service.PlacementNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

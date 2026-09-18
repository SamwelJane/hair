import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import ColumnElement, and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.catalog import Category, Product
from app.models.enums import HomepagePlacementSection, ProductStatus
from app.models.homepage import HomepageBanner, HomepageProductPlacement
from app.services.audit import log_audit
from app.services.product_catalog import rating_summary


class BannerNotFoundError(Exception):
    pass


class PlacementNotFoundError(Exception):
    pass


def _active_window_clause() -> ColumnElement[bool]:
    now = datetime.now(UTC)
    return and_(
        or_(HomepageProductPlacement.starts_at.is_(None), HomepageProductPlacement.starts_at <= now),
        or_(HomepageProductPlacement.ends_at.is_(None), HomepageProductPlacement.ends_at >= now),
    )


async def _placements_to_homepage_products(
    db: AsyncSession, placements: list[HomepageProductPlacement]
) -> list[tuple[HomepageProductPlacement, Product, tuple[float | None, int]]]:
    products = [p.product for p in placements]
    ratings = await rating_summary(db, [p.id for p in products])
    return [(placement, placement.product, ratings.get(placement.product_id, (None, 0))) for placement in placements]


async def _load_active_placements(db: AsyncSession, section: HomepagePlacementSection) -> list[HomepageProductPlacement]:
    stmt = (
        select(HomepageProductPlacement)
        .where(
            HomepageProductPlacement.section == section,
            HomepageProductPlacement.is_active.is_(True),
            _active_window_clause(),
        )
        .join(Product, HomepageProductPlacement.product_id == Product.id)
        .where(Product.status == ProductStatus.PUBLISHED)
        .options(selectinload(HomepageProductPlacement.product).selectinload(Product.images))
        .order_by(HomepageProductPlacement.sort_order)
    )
    return list((await db.execute(stmt)).scalars().all())


async def get_active_deal_for_product(db: AsyncSession, product_id: uuid.UUID) -> HomepageProductPlacement | None:
    """Shared by the homepage Deals rail and the product-detail page - a
    product can have at most one *active* deal at a time in practice, so the
    first match by sort_order is used if more than one somehow overlaps."""
    stmt = (
        select(HomepageProductPlacement)
        .where(
            HomepageProductPlacement.product_id == product_id,
            HomepageProductPlacement.section == HomepagePlacementSection.DEAL,
            HomepageProductPlacement.is_active.is_(True),
            _active_window_clause(),
        )
        .order_by(HomepageProductPlacement.sort_order)
    )
    return await db.scalar(stmt)


async def get_public_homepage_content(db: AsyncSession) -> dict:
    banners = list(
        (
            await db.execute(
                select(HomepageBanner)
                .where(HomepageBanner.is_active.is_(True), HomepageBanner.image_url.is_not(None))
                .order_by(HomepageBanner.sort_order)
            )
        )
        .scalars()
        .all()
    )
    featured_categories = list(
        (
            await db.execute(
                select(Category)
                .where(Category.is_featured.is_(True), Category.image_url.is_not(None))
                .order_by(Category.sort_order)
            )
        )
        .scalars()
        .all()
    )

    featured_rows = await _placements_to_homepage_products(db, await _load_active_placements(db, HomepagePlacementSection.FEATURED))
    deal_rows = await _placements_to_homepage_products(db, await _load_active_placements(db, HomepagePlacementSection.DEAL))

    return {
        "banners": banners,
        "featured_categories": featured_categories,
        "featured_products": featured_rows,
        "deals": deal_rows,
    }


async def create_banner(
    db: AsyncSession, *, headline: str, subheadline: str | None, cta_label: str | None, cta_url: str | None,
    sort_order: int, is_active: bool, actor_user_id: uuid.UUID,
) -> HomepageBanner:
    banner = HomepageBanner(
        headline=headline, subheadline=subheadline, cta_label=cta_label, cta_url=cta_url,
        sort_order=sort_order, is_active=is_active,
    )
    db.add(banner)
    await db.flush()
    await log_audit(
        db, user_id=actor_user_id, action="CREATE_HOMEPAGE_BANNER", entity_type="HomepageBanner",
        entity_id=str(banner.id), metadata={"headline": headline},
    )
    await db.commit()
    await db.refresh(banner)
    return banner


async def update_banner(
    db: AsyncSession, banner_id: uuid.UUID, *, headline: str, subheadline: str | None, cta_label: str | None,
    cta_url: str | None, sort_order: int, is_active: bool, actor_user_id: uuid.UUID,
) -> HomepageBanner:
    banner = await db.get(HomepageBanner, banner_id)
    if banner is None:
        raise BannerNotFoundError(f"Banner {banner_id} not found.")

    banner.headline = headline
    banner.subheadline = subheadline
    banner.cta_label = cta_label
    banner.cta_url = cta_url
    banner.sort_order = sort_order
    banner.is_active = is_active

    await log_audit(db, user_id=actor_user_id, action="UPDATE_HOMEPAGE_BANNER", entity_type="HomepageBanner", entity_id=str(banner.id), metadata={})
    await db.commit()
    await db.refresh(banner)
    return banner


async def set_banner_image(
    db: AsyncSession, banner_id: uuid.UUID, *, image_url: str, cloudinary_public_id: str, actor_user_id: uuid.UUID
) -> HomepageBanner:
    banner = await db.get(HomepageBanner, banner_id)
    if banner is None:
        raise BannerNotFoundError(f"Banner {banner_id} not found.")

    banner.image_url = image_url
    banner.cloudinary_public_id = cloudinary_public_id

    await log_audit(db, user_id=actor_user_id, action="SET_HOMEPAGE_BANNER_IMAGE", entity_type="HomepageBanner", entity_id=str(banner.id), metadata={})
    await db.commit()
    await db.refresh(banner)
    return banner


async def delete_banner(db: AsyncSession, banner_id: uuid.UUID, *, actor_user_id: uuid.UUID) -> None:
    banner = await db.get(HomepageBanner, banner_id)
    if banner is None:
        raise BannerNotFoundError(f"Banner {banner_id} not found.")

    await log_audit(db, user_id=actor_user_id, action="DELETE_HOMEPAGE_BANNER", entity_type="HomepageBanner", entity_id=str(banner.id), metadata={})
    await db.delete(banner)
    await db.commit()


async def create_placement(
    db: AsyncSession, *, product_id: uuid.UUID, section: HomepagePlacementSection, sale_price_usd: Decimal | None,
    starts_at: datetime | None, ends_at: datetime | None, sort_order: int, is_active: bool, actor_user_id: uuid.UUID,
) -> HomepageProductPlacement:
    placement = HomepageProductPlacement(
        product_id=product_id, section=section, sale_price_usd=sale_price_usd, starts_at=starts_at, ends_at=ends_at,
        sort_order=sort_order, is_active=is_active,
    )
    db.add(placement)
    await db.flush()
    await log_audit(
        db, user_id=actor_user_id, action="CREATE_HOMEPAGE_PLACEMENT", entity_type="HomepageProductPlacement",
        entity_id=str(placement.id), metadata={"productId": str(product_id), "section": section.value},
    )
    await db.commit()
    # attribute_names includes the relationship so _placement_out's
    # placement.product.name/slug access doesn't hit an unloaded attribute -
    # async sessions can't lazy-load implicitly.
    await db.refresh(placement, attribute_names=["product"])
    return placement


async def update_placement(
    db: AsyncSession, placement_id: uuid.UUID, *, section: HomepagePlacementSection, sale_price_usd: Decimal | None,
    starts_at: datetime | None, ends_at: datetime | None, sort_order: int, is_active: bool, actor_user_id: uuid.UUID,
) -> HomepageProductPlacement:
    placement = await db.get(HomepageProductPlacement, placement_id)
    if placement is None:
        raise PlacementNotFoundError(f"Placement {placement_id} not found.")

    placement.section = section
    placement.sale_price_usd = sale_price_usd
    placement.starts_at = starts_at
    placement.ends_at = ends_at
    placement.sort_order = sort_order
    placement.is_active = is_active

    await log_audit(
        db, user_id=actor_user_id, action="UPDATE_HOMEPAGE_PLACEMENT", entity_type="HomepageProductPlacement",
        entity_id=str(placement.id), metadata={},
    )
    await db.commit()
    await db.refresh(placement, attribute_names=["product"])
    return placement


async def delete_placement(db: AsyncSession, placement_id: uuid.UUID, *, actor_user_id: uuid.UUID) -> None:
    placement = await db.get(HomepageProductPlacement, placement_id)
    if placement is None:
        raise PlacementNotFoundError(f"Placement {placement_id} not found.")

    await log_audit(
        db, user_id=actor_user_id, action="DELETE_HOMEPAGE_PLACEMENT", entity_type="HomepageProductPlacement",
        entity_id=str(placement.id), metadata={},
    )
    await db.delete(placement)
    await db.commit()


async def list_placements(db: AsyncSession) -> list[HomepageProductPlacement]:
    stmt = (
        select(HomepageProductPlacement)
        .options(selectinload(HomepageProductPlacement.product))
        .order_by(HomepageProductPlacement.section, HomepageProductPlacement.sort_order)
    )
    return list((await db.execute(stmt)).scalars().all())


async def list_banners(db: AsyncSession) -> list[HomepageBanner]:
    return list((await db.execute(select(HomepageBanner).order_by(HomepageBanner.sort_order))).scalars().all())

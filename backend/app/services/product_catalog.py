import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.catalog import Category, Product, ProductVariant, Supplier
from app.models.enums import ProductStatus, ReviewStatus
from app.models.orders import Review

SortOption = Literal["newest", "price_asc", "price_desc"]


@dataclass
class ProductFilters:
    """Plain field bag mirroring the old app's ProductFilters interface in
    src/lib/products/queries.ts - kept separate from admin's mutation-only
    app/services/products.py since this module is public-read-only."""

    category_slug: str | None = None
    supplier_id: uuid.UUID | None = None
    search: str | None = None
    min_price_usd: Decimal | None = None
    max_price_usd: Decimal | None = None
    length: str | None = None
    texture: str | None = None
    color: str | None = None
    sort: SortOption = "newest"


def _apply_filters(stmt: Select, filters: ProductFilters) -> Select:
    stmt = stmt.where(Product.status == ProductStatus.PUBLISHED)

    if filters.category_slug:
        stmt = stmt.where(Product.category.has(Category.slug == filters.category_slug))
    if filters.supplier_id:
        stmt = stmt.where(Product.supplier_id == filters.supplier_id)
    if filters.search:
        pattern = f"%{filters.search}%"
        stmt = stmt.where(
            or_(
                Product.name.ilike(pattern),
                Product.description.ilike(pattern),
                Product.hair_length.ilike(pattern),
                Product.texture.ilike(pattern),
                Product.color.ilike(pattern),
            )
        )
    if filters.min_price_usd is not None:
        stmt = stmt.where(Product.base_price_usd >= filters.min_price_usd)
    if filters.max_price_usd is not None:
        stmt = stmt.where(Product.base_price_usd <= filters.max_price_usd)
    if filters.length or filters.texture or filters.color:
        conditions = [ProductVariant.product_id == Product.id]
        if filters.length:
            conditions.append(ProductVariant.length == filters.length)
        if filters.texture:
            conditions.append(ProductVariant.texture == filters.texture)
        if filters.color:
            conditions.append(ProductVariant.color == filters.color)
        stmt = stmt.where(select(ProductVariant.id).where(*conditions).exists())

    return stmt


async def rating_summary(
    db: AsyncSession, product_ids: list[uuid.UUID]
) -> dict[uuid.UUID, tuple[float | None, int]]:
    """Public (not module-private) since services/homepage.py also needs it
    for the Featured/Deals rails - kept as one shared implementation rather
    than a second near-identical aggregate query."""
    if not product_ids:
        return {}
    rows = (
        await db.execute(
            select(Review.product_id, func.avg(Review.rating), func.count(Review.id))
            .where(Review.product_id.in_(product_ids), Review.status == ReviewStatus.APPROVED)
            .group_by(Review.product_id)
        )
    ).all()
    return {
        product_id: (round(float(avg_rating), 1) if avg_rating is not None else None, count)
        for product_id, avg_rating, count in rows
    }


async def list_published_products(
    db: AsyncSession, filters: ProductFilters, *, page: int, page_size: int
) -> tuple[list[Product], int, dict[uuid.UUID, tuple[float | None, int]]]:
    total = await db.scalar(_apply_filters(select(func.count(Product.id)), filters)) or 0

    stmt = _apply_filters(select(Product), filters)
    if filters.sort == "price_asc":
        stmt = stmt.order_by(Product.base_price_usd.asc())
    elif filters.sort == "price_desc":
        stmt = stmt.order_by(Product.base_price_usd.desc())
    else:
        stmt = stmt.order_by(Product.created_at.desc())

    stmt = stmt.options(selectinload(Product.images)).offset((page - 1) * page_size).limit(page_size)
    products = list((await db.execute(stmt)).scalars().all())

    ratings = await rating_summary(db, [p.id for p in products])
    return products, total, ratings


class ProductNotFoundError(Exception):
    pass


async def get_product_by_slug(db: AsyncSession, slug: str) -> tuple[Product, list[Review]]:
    """Unlike the old app's getProductBySlug (which didn't filter by status,
    so a draft product's slug was viewable by anyone who guessed/knew it),
    this enforces PUBLISHED - a deliberate hardening for a router with no
    auth at all, now serving two separate public frontends."""
    product = (
        await db.execute(
            select(Product)
            .where(Product.slug == slug, Product.status == ProductStatus.PUBLISHED)
            .options(
                selectinload(Product.variants),
                selectinload(Product.images),
                selectinload(Product.category),
                selectinload(Product.supplier),
            )
        )
    ).scalar_one_or_none()
    if product is None:
        raise ProductNotFoundError(f"Product '{slug}' not found")

    reviews = list(
        (
            await db.execute(
                select(Review)
                .where(Review.product_id == product.id, Review.status == ReviewStatus.APPROVED)
                .options(selectinload(Review.user))
                .order_by(Review.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return product, reviews


async def list_categories(db: AsyncSession) -> list[Category]:
    return list((await db.execute(select(Category).order_by(Category.name))).scalars().all())


async def list_active_suppliers(db: AsyncSession) -> list[Supplier]:
    return list(
        (await db.execute(select(Supplier).where(Supplier.status == "active").order_by(Supplier.name)))
        .scalars()
        .all()
    )


async def list_variant_facets(db: AsyncSession) -> tuple[list[str], list[str], list[str]]:
    rows = (await db.execute(select(ProductVariant.length, ProductVariant.texture, ProductVariant.color))).all()
    lengths = sorted({r[0] for r in rows if r[0]})
    textures = sorted({r[1] for r in rows if r[1]})
    colors = sorted({r[2] for r in rows if r[2]})
    return lengths, textures, colors


def average_rating(reviews: list[Review]) -> float | None:
    if not reviews:
        return None
    return round(sum(r.rating for r in reviews) / len(reviews), 1)

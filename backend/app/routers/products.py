import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.models.catalog import Product
from app.schemas.products import (
    CategoryOut,
    ProductDetailOut,
    ProductImagePublicOut,
    ProductListItemOut,
    ProductListOut,
    ProductVariantPublicOut,
    ReviewPublicOut,
    SupplierPublicOut,
    VariantFacetsOut,
)
from app.services import homepage as homepage_service
from app.services import product_catalog

router = APIRouter(tags=["products"])

DEFAULT_PAGE_SIZE = 12


def _list_item(product: Product, rating: tuple[float | None, int]) -> ProductListItemOut:
    average_rating, review_count = rating
    return ProductListItemOut(
        id=product.id,
        slug=product.slug,
        name=product.name,
        base_price_usd=product.base_price_usd,
        country_of_origin=product.country_of_origin,
        hair_category=product.hair_category,
        image_url=product.images[0].url if product.images else None,
        average_rating=average_rating,
        review_count=review_count,
    )


@router.get("/products", response_model=ProductListOut)
async def list_products(
    db: AsyncSession = Depends(get_db),
    category: str | None = None,
    supplier_id: uuid.UUID | None = None,
    q: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    length: str | None = None,
    texture: str | None = None,
    color: str | None = None,
    sort: product_catalog.SortOption = "newest",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=60),
) -> ProductListOut:
    filters = product_catalog.ProductFilters(
        category_slug=category,
        supplier_id=supplier_id,
        search=q,
        min_price_usd=min_price,
        max_price_usd=max_price,
        length=length,
        texture=texture,
        color=color,
        sort=sort,
    )
    products, total, ratings = await product_catalog.list_published_products(
        db, filters, page=page, page_size=page_size
    )
    return ProductListOut(
        items=[_list_item(p, ratings.get(p.id, (None, 0))) for p in products],
        total=total,
        page=page,
        page_size=page_size,
    )


# Registered before /products/{slug} - FastAPI/Starlette matches routes in
# declaration order, and "facets" would otherwise be captured as a slug.
@router.get("/products/facets", response_model=VariantFacetsOut)
async def get_product_facets(db: AsyncSession = Depends(get_db)) -> VariantFacetsOut:
    lengths, textures, colors = await product_catalog.list_variant_facets(db)
    return VariantFacetsOut(lengths=lengths, textures=textures, colors=colors)


@router.get("/products/{slug}", response_model=ProductDetailOut)
async def get_product(slug: str, db: AsyncSession = Depends(get_db)) -> ProductDetailOut:
    try:
        product, reviews = await product_catalog.get_product_by_slug(db, slug)
    except product_catalog.ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    deal = await homepage_service.get_active_deal_for_product(db, product.id)

    return ProductDetailOut(
        id=product.id,
        slug=product.slug,
        name=product.name,
        description=product.description,
        category=CategoryOut(
            id=product.category.id, name=product.category.name, slug=product.category.slug,
            parent_id=product.category.parent_id, image_url=product.category.image_url,
        ),
        supplier=SupplierPublicOut(id=product.supplier.id, name=product.supplier.name, country=product.supplier.country),
        country_of_origin=product.country_of_origin,
        base_price_usd=product.base_price_usd,
        hair_category=product.hair_category,
        hair_length=product.hair_length,
        texture=product.texture,
        color=product.color,
        quality=product.quality,
        accessory_type=product.accessory_type,
        processing_time_days=product.processing_time_days,
        base_weight_grams=product.base_weight_grams,
        drawn_type=product.drawn_type,
        texture_category=product.texture_category,
        attachment_type=product.attachment_type,
        tip_type=product.tip_type,
        wig_construction=product.wig_construction,
        wig_cap_size=product.wig_cap_size,
        wig_features=product.wig_features,
        variants=[
            ProductVariantPublicOut(
                id=v.id, sku=v.sku, length=v.length, length_inches=v.length_inches, density=v.density,
                texture=v.texture, color=v.color, price_delta_usd=v.price_delta_usd, stock_qty=v.stock_qty,
                weight_override_grams=v.weight_override_grams,
            )
            for v in product.variants
        ],
        images=[
            ProductImagePublicOut(
                id=i.id, variant_id=i.variant_id, url=i.url, alt_text=i.alt_text, sort_order=i.sort_order
            )
            for i in sorted(product.images, key=lambda i: i.sort_order)
        ],
        reviews=[
            ReviewPublicOut(id=r.id, rating=r.rating, body=r.body, user_name=r.user.name, created_at=r.created_at)
            for r in reviews
        ],
        average_rating=product_catalog.average_rating(reviews),
        sale_price_usd=deal.sale_price_usd if deal else None,
        deal_ends_at=deal.ends_at if deal else None,
    )


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)) -> list[CategoryOut]:
    categories = await product_catalog.list_categories(db)
    return [
        CategoryOut(id=c.id, name=c.name, slug=c.slug, parent_id=c.parent_id, image_url=c.image_url)
        for c in categories
    ]


@router.get("/suppliers", response_model=list[SupplierPublicOut])
async def list_suppliers(db: AsyncSession = Depends(get_db)) -> list[SupplierPublicOut]:
    suppliers = await product_catalog.list_active_suppliers(db)
    return [SupplierPublicOut(id=s.id, name=s.name, country=s.country) for s in suppliers]

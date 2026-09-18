from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.models.catalog import Product
from app.models.homepage import HomepageProductPlacement
from app.schemas.homepage import BannerOut, CategoryTileOut, HomepageContentOut, HomepageProductOut
from app.services import homepage as homepage_service

router = APIRouter(tags=["homepage"])


def _homepage_product_out(
    placement: HomepageProductPlacement, product: Product, rating: tuple[float | None, int]
) -> HomepageProductOut:
    average_rating, review_count = rating
    return HomepageProductOut(
        id=product.id,
        slug=product.slug,
        name=product.name,
        image_url=product.images[0].url if product.images else None,
        base_price_usd=product.base_price_usd,
        sale_price_usd=placement.sale_price_usd,
        average_rating=average_rating,
        review_count=review_count,
        deal_ends_at=placement.ends_at,
    )


@router.get("/homepage", response_model=HomepageContentOut)
async def get_homepage(db: AsyncSession = Depends(get_db)) -> HomepageContentOut:
    content = await homepage_service.get_public_homepage_content(db)
    return HomepageContentOut(
        banners=[
            BannerOut(
                # image_url is guaranteed non-None here - get_public_homepage_content
                # only returns banners with one set.
                id=b.id, image_url=b.image_url, headline=b.headline, subheadline=b.subheadline,
                cta_label=b.cta_label, cta_url=b.cta_url,
            )
            for b in content["banners"]
            if b.image_url is not None
        ],
        featured_categories=[
            CategoryTileOut(id=c.id, name=c.name, slug=c.slug, image_url=c.image_url)
            for c in content["featured_categories"]
        ],
        featured_products=[_homepage_product_out(*row) for row in content["featured_products"]],
        deals=[_homepage_product_out(*row) for row in content["deals"]],
    )

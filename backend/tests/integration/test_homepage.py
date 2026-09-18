from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.models.enums import HomepagePlacementSection
from app.models.homepage import HomepageBanner, HomepageProductPlacement


async def test_homepage_empty_by_default(client):
    resp = await client.get("/homepage")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"banners": [], "featured_categories": [], "featured_products": [], "deals": []}


async def test_homepage_returns_active_banner_ordered(client, db):
    db.add_all(
        [
            HomepageBanner(image_url="https://img/b2.jpg", headline="Second", sort_order=2, is_active=True),
            HomepageBanner(image_url="https://img/b1.jpg", headline="First", sort_order=1, is_active=True),
            HomepageBanner(image_url="https://img/b3.jpg", headline="Inactive", sort_order=0, is_active=False),
            HomepageBanner(image_url=None, headline="No image yet", sort_order=0, is_active=True),
        ]
    )
    await db.commit()

    resp = await client.get("/homepage")
    assert resp.status_code == 200
    headlines = [b["headline"] for b in resp.json()["banners"]]
    assert headlines == ["First", "Second"]


async def test_homepage_returns_featured_category_with_image_only(client, db, checkout_fixtures):
    category = checkout_fixtures["category"]
    category.is_featured = True
    category.image_url = "https://img/cat.jpg"
    await db.commit()

    resp = await client.get("/homepage")
    body = resp.json()
    assert len(body["featured_categories"]) == 1
    assert body["featured_categories"][0]["slug"] == category.slug


async def test_homepage_featured_products_and_deals(client, db, checkout_fixtures):
    product = checkout_fixtures["product"]
    db.add(
        HomepageProductPlacement(
            product_id=product.id, section=HomepagePlacementSection.FEATURED, sort_order=0, is_active=True
        )
    )
    await db.commit()

    resp = await client.get("/homepage")
    body = resp.json()
    assert len(body["featured_products"]) == 1
    assert body["featured_products"][0]["slug"] == product.slug
    assert body["deals"] == []


async def test_homepage_deal_shows_sale_price_and_respects_date_window(client, db, checkout_fixtures):
    product = checkout_fixtures["product"]
    now = datetime.now(UTC)
    db.add_all(
        [
            HomepageProductPlacement(
                product_id=product.id, section=HomepagePlacementSection.DEAL, sale_price_usd=Decimal("39.99"),
                ends_at=now + timedelta(days=1), sort_order=0, is_active=True,
            ),
        ]
    )
    await db.commit()

    resp = await client.get("/homepage")
    body = resp.json()
    assert len(body["deals"]) == 1
    assert body["deals"][0]["sale_price_usd"] == "39.99"


async def test_homepage_expired_deal_is_excluded(client, db, checkout_fixtures):
    product = checkout_fixtures["product"]
    now = datetime.now(UTC)
    db.add(
        HomepageProductPlacement(
            product_id=product.id, section=HomepagePlacementSection.DEAL, sale_price_usd=Decimal("10.00"),
            ends_at=now - timedelta(days=1), sort_order=0, is_active=True,
        )
    )
    await db.commit()

    resp = await client.get("/homepage")
    assert resp.json()["deals"] == []

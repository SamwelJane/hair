from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.models.catalog import Product, ProductVariant
from app.models.enums import HairCategory, HomepagePlacementSection, ReviewStatus
from app.models.homepage import HomepageProductPlacement
from app.models.orders import Order, OrderItem, Review


async def test_list_products_only_returns_published(client, db, checkout_fixtures):
    draft = Product(
        name="Draft Wig", slug="draft-wig", category_id=checkout_fixtures["category"].id,
        supplier_id=checkout_fixtures["supplier"].id, description="Not yet live.", country_of_origin="KE",
        base_price_usd=Decimal("50.00"), hair_category=HairCategory.WIG, status="draft",
    )
    db.add(draft)
    await db.commit()

    resp = await client.get("/products")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["slug"] == checkout_fixtures["product"].slug


async def test_get_draft_product_by_slug_returns_404(client, db, checkout_fixtures):
    draft = Product(
        name="Draft Wig", slug="draft-wig", category_id=checkout_fixtures["category"].id,
        supplier_id=checkout_fixtures["supplier"].id, description="Not yet live.", country_of_origin="KE",
        base_price_usd=Decimal("50.00"), hair_category=HairCategory.WIG, status="draft",
    )
    db.add(draft)
    await db.commit()

    resp = await client.get("/products/draft-wig")
    assert resp.status_code == 404


async def test_get_published_product_includes_variants_and_approved_reviews_only(client, db, admin_user, checkout_fixtures):
    product = checkout_fixtures["product"]

    order = Order(
        order_number="ORD-TEST-0001", tracking_number="VNKE-TEST-0001", user_id=admin_user.id, status="DELIVERED", subtotal_usd=Decimal(100),
        shipping_fee_usd=Decimal(10), total_amount_usd=Decimal(110), shipping_country="KE",
        shipping_address={"full_name": "Admin", "line1": "x", "city": "Nairobi", "country_code": "KE", "phone": "+254700000000"},
    )
    db.add(order)
    await db.flush()
    db.add(
        OrderItem(
            order_id=order.id, product_id=product.id, variant_id=checkout_fixtures["variant"].id, quantity=1,
            unit_price_usd_at_purchase=Decimal(100), line_total_usd=Decimal(100),
        )
    )
    db.add(Review(product_id=product.id, user_id=admin_user.id, order_id=order.id, rating=5, body="Great!", status=ReviewStatus.APPROVED))
    db.add(Review(product_id=product.id, user_id=admin_user.id, order_id=order.id, rating=1, body="Pending mod", status=ReviewStatus.PENDING))
    await db.commit()

    resp = await client.get(f"/products/{product.slug}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["slug"] == product.slug
    assert len(body["variants"]) == 1
    assert len(body["reviews"]) == 1
    assert body["reviews"][0]["body"] == "Great!"
    assert body["average_rating"] == 5.0


async def test_filter_by_variant_length(client, db, checkout_fixtures):
    other_product = Product(
        name="Straight Bundle", slug="straight-bundle", category_id=checkout_fixtures["category"].id,
        supplier_id=checkout_fixtures["supplier"].id, description="Straight.", country_of_origin="KE",
        base_price_usd=Decimal("60.00"), hair_category=HairCategory.BULK_HAIR, status="published",
    )
    db.add(other_product)
    await db.flush()
    db.add(ProductVariant(product_id=other_product.id, sku="SB-20-BLK", stock_qty=5, length="20 inches"))
    await db.commit()

    resp = await client.get("/products", params={"length": "20 inches"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["slug"] == "straight-bundle"


async def test_price_range_and_sort(client, db, checkout_fixtures):
    resp = await client.get("/products", params={"min_price": "1000"})
    assert resp.json()["total"] == 0

    resp = await client.get("/products", params={"sort": "price_asc"})
    assert resp.status_code == 200


async def test_facets_returns_distinct_variant_attributes(client, checkout_fixtures):
    resp = await client.get("/products/facets")
    assert resp.status_code == 200
    body = resp.json()
    assert body["lengths"] == []
    assert body["textures"] == []
    assert body["colors"] == []


async def test_product_detail_has_no_deal_price_by_default(client, checkout_fixtures):
    product = checkout_fixtures["product"]
    resp = await client.get(f"/products/{product.slug}")
    body = resp.json()
    assert body["sale_price_usd"] is None
    assert body["deal_ends_at"] is None


async def test_product_detail_shows_active_deal_price(client, db, checkout_fixtures):
    product = checkout_fixtures["product"]
    ends_at = datetime.now(UTC) + timedelta(days=2)
    db.add(
        HomepageProductPlacement(
            product_id=product.id, section=HomepagePlacementSection.DEAL, sale_price_usd=Decimal("29.99"),
            ends_at=ends_at, sort_order=0, is_active=True,
        )
    )
    await db.commit()

    resp = await client.get(f"/products/{product.slug}")
    body = resp.json()
    assert body["sale_price_usd"] == "29.99"
    assert body["deal_ends_at"] is not None


async def test_list_categories_and_active_suppliers(client, db, checkout_fixtures):
    categories_resp = await client.get("/categories")
    assert categories_resp.status_code == 200
    assert any(c["slug"] == "wigs" for c in categories_resp.json())

    suppliers_resp = await client.get("/suppliers")
    assert suppliers_resp.status_code == 200
    assert any(s["name"] == checkout_fixtures["supplier"].name for s in suppliers_resp.json())

    checkout_fixtures["supplier"].status = "inactive"
    await db.commit()
    suppliers_resp2 = await client.get("/suppliers")
    assert all(s["name"] != checkout_fixtures["supplier"].name for s in suppliers_resp2.json())

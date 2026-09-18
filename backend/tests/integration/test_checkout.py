from decimal import Decimal

from sqlalchemy import select

from app.models.identity import User
from app.models.orders import Order
from app.models.pricing import DiscountCode
from tests.integration.conftest import checkout_payload


async def test_guest_checkout_bank_transfer_happy_path(client, db, checkout_fixtures):
    product = checkout_fixtures["product"]
    variant = checkout_fixtures["variant"]

    resp = await client.post("/orders", json=checkout_payload(product.id, variant.id))
    assert resp.status_code == 201
    body = resp.json()
    assert body["order_number"].startswith("ORD-")
    assert body["tracking_number"].startswith("VNKE-")
    assert "bankDetails" in body["payment_instructions"]
    assert body["guest_access_token"]

    order = (await db.execute(select(Order).where(Order.order_number == body["order_number"]))).scalar_one()
    assert order.tracking_number == body["tracking_number"]
    # unit price = 100 + 20 variant delta = 120
    assert order.subtotal_usd == Decimal("120.00")
    # PricingSetting.shipping_per_kg_usd (default 60) overrides the country
    # rule's own per_kg_fee_usd (5) - that's not a test bug, it's the ported
    # engine's actual precedence (settings always win when set; see
    # cart_breakdown.calculate_cart_breakdown, which always passes the
    # global setting through): base(10) + 60*0.3kg + packaging(2) = 30.
    assert order.shipping_fee_usd == Decimal("30.00")

    guest_user = (await db.execute(select(User).where(User.email == "guest@example.com"))).scalar_one()
    assert guest_user.id == order.user_id


async def test_guest_checkout_without_email_rejected(client, checkout_fixtures):
    product, variant = checkout_fixtures["product"], checkout_fixtures["variant"]
    payload = checkout_payload(product.id, variant.id)
    payload["shipping_address"]["email"] = None
    resp = await client.post("/orders", json=payload)
    assert resp.status_code == 400


async def test_checkout_reuses_existing_account_for_known_email(client, db, checkout_fixtures):
    from app.core.security import hash_password
    from app.models.identity import User as UserModel

    existing = UserModel(email="returning@example.com", name="Returning Customer", password_hash=hash_password("whatever1"))
    db.add(existing)
    await db.commit()
    await db.refresh(existing)

    product, variant = checkout_fixtures["product"], checkout_fixtures["variant"]
    resp = await client.post("/orders", json=checkout_payload(product.id, variant.id, email="returning@example.com"))
    assert resp.status_code == 201

    order = (await db.execute(select(Order).where(Order.order_number == resp.json()["order_number"]))).scalar_one()
    assert order.user_id == existing.id


async def test_checkout_decrements_variant_stock(client, db, checkout_fixtures):
    variant = checkout_fixtures["variant"]
    product = checkout_fixtures["product"]
    assert variant.stock_qty == 5

    resp = await client.post("/orders", json=checkout_payload(product.id, variant.id, quantity=2))
    assert resp.status_code == 201

    await db.refresh(variant)
    assert variant.stock_qty == 3


async def test_checkout_rejects_when_insufficient_stock(client, checkout_fixtures):
    product, variant = checkout_fixtures["product"], checkout_fixtures["variant"]
    # stock_qty is 5 (see checkout_fixtures); 10 is within the 1-50 per-line
    # quantity validation range but still exceeds available stock.
    resp = await client.post("/orders", json=checkout_payload(product.id, variant.id, quantity=10))
    assert resp.status_code == 400
    assert "stock" in resp.json()["detail"].lower()


async def test_checkout_without_shipping_rule_for_country_rejected(client, checkout_fixtures):
    product, variant = checkout_fixtures["product"], checkout_fixtures["variant"]
    payload = checkout_payload(product.id, variant.id)
    payload["shipping_address"]["country_code"] = "US"  # no shipping rule seeded for US
    resp = await client.post("/orders", json=payload)
    assert resp.status_code == 400


async def test_checkout_with_valid_discount_code_reduces_total_and_increments_usage(client, db, checkout_fixtures):
    discount = DiscountCode(code="SAVE10", type="fixed", value=Decimal("10.00"), active=True)
    db.add(discount)
    await db.commit()
    await db.refresh(discount)

    product, variant = checkout_fixtures["product"], checkout_fixtures["variant"]
    payload = checkout_payload(product.id, variant.id)
    payload["discount_code"] = "SAVE10"
    resp = await client.post("/orders", json=payload)
    assert resp.status_code == 201

    order = (await db.execute(select(Order).where(Order.order_number == resp.json()["order_number"]))).scalar_one()
    assert order.discount_code_id == discount.id

    await db.refresh(discount)
    assert discount.times_used == 1


async def test_checkout_rejects_discount_code_at_usage_limit(client, db, checkout_fixtures):
    discount = DiscountCode(code="ONEUSE", type="fixed", value=Decimal("5.00"), usage_limit=1, times_used=1, active=True)
    db.add(discount)
    await db.commit()

    product, variant = checkout_fixtures["product"], checkout_fixtures["variant"]
    payload = checkout_payload(product.id, variant.id)
    payload["discount_code"] = "ONEUSE"
    resp = await client.post("/orders", json=payload)
    # findActiveDiscountCode itself excludes an already-maxed-out code, so
    # the discount is simply not applied rather than the checkout failing.
    assert resp.status_code == 201
    order = (await db.execute(select(Order).where(Order.order_number == resp.json()["order_number"]))).scalar_one()
    assert order.discount_code_id is None


async def test_get_order_accessible_with_valid_guest_token(client, checkout_fixtures):
    product, variant = checkout_fixtures["product"], checkout_fixtures["variant"]
    checkout_resp = await client.post("/orders", json=checkout_payload(product.id, variant.id))
    order_number = checkout_resp.json()["order_number"]
    guest_token = checkout_resp.json()["guest_access_token"]

    resp = await client.get(f"/orders/{order_number}", params={"guest_token": guest_token})
    assert resp.status_code == 200
    assert resp.json()["order_number"] == order_number


async def test_get_order_rejected_without_guest_token_or_session(client, checkout_fixtures):
    product, variant = checkout_fixtures["product"], checkout_fixtures["variant"]
    checkout_resp = await client.post("/orders", json=checkout_payload(product.id, variant.id))
    order_number = checkout_resp.json()["order_number"]

    resp = await client.get(f"/orders/{order_number}")
    assert resp.status_code == 403


async def test_get_order_rejected_with_guest_token_for_different_order(client, checkout_fixtures):
    product, variant = checkout_fixtures["product"], checkout_fixtures["variant"]
    first = await client.post("/orders", json=checkout_payload(product.id, variant.id))
    second = await client.post("/orders", json=checkout_payload(product.id, variant.id, email="another@example.com"))

    resp = await client.get(
        f"/orders/{second.json()['order_number']}", params={"guest_token": first.json()["guest_access_token"]}
    )
    assert resp.status_code == 403


async def test_logged_in_checkout_uses_session_user_not_guest_flow(client, db, checkout_fixtures):
    register_resp = await client.post(
        "/auth/register", json={"name": "Logged In", "email": "loggedin@example.com", "password": "supersecret1"}
    )
    access_token = register_resp.json()["access_token"]

    product, variant = checkout_fixtures["product"], checkout_fixtures["variant"]
    payload = checkout_payload(product.id, variant.id)
    resp = await client.post("/orders", json=payload, headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 201
    assert resp.json()["guest_access_token"] is None

    order = (await db.execute(select(Order).where(Order.order_number == resp.json()["order_number"]))).scalar_one()
    logged_in_user = (await db.execute(select(User).where(User.email == "loggedin@example.com"))).scalar_one()
    assert order.user_id == logged_in_user.id

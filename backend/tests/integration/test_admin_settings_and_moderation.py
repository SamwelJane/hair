
from sqlalchemy import select

from app.models.enums import ReturnStatus, ReviewStatus, UserRole
from app.models.identity import User
from app.models.orders import Order, Return, Review
from tests.integration.conftest import checkout_payload


async def _login(client, email, password) -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _staff_headers(client, db) -> dict:
    from app.core.security import hash_password

    staff = User(email="staffmod@example.com", name="Staff", password_hash=hash_password("staffpass1"), role=UserRole.STAFF)
    db.add(staff)
    await db.commit()
    token = await _login(client, "staffmod@example.com", "staffpass1")
    return {"Authorization": f"Bearer {token}"}


# ---------- Returns ----------


async def test_resolve_return_approves_with_refund(client, db, admin_user, checkout_fixtures):
    order_number = (await client.post("/orders", json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id))).json()["order_number"]
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()

    customer = (await db.execute(select(User).where(User.email == "guest@example.com"))).scalar_one()
    return_request = Return(order_id=order.id, requested_by_id=customer.id, reason="Wrong color")
    db.add(return_request)
    await db.commit()
    await db.refresh(return_request)

    token = await _login(client, admin_user.email, "adminpass1")
    resp = await client.post(
        f"/admin/returns/{return_request.id}/resolve",
        json={"status": "REFUNDED", "refund_amount_usd": "50.00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "REFUNDED"
    assert body["refund_amount_usd"] == "50.00"
    assert body["order_number"] == order_number

    await db.refresh(return_request)
    assert return_request.status == ReturnStatus.REFUNDED
    assert return_request.resolved_by_id == admin_user.id


async def test_list_returns_visible_to_staff(client, db, checkout_fixtures):
    headers = await _staff_headers(client, db)
    resp = await client.get("/admin/returns", headers=headers)
    assert resp.status_code == 200


async def test_resolve_nonexistent_return_404(client, admin_user):
    token = await _login(client, admin_user.email, "adminpass1")
    resp = await client.post(
        "/admin/returns/00000000-0000-0000-0000-000000000000/resolve",
        json={"status": "APPROVED"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


# ---------- Reviews ----------


async def test_moderate_review_approves(client, db, admin_user, checkout_fixtures):
    customer = User(email="reviewer@example.com", name="Reviewer", password_hash="x")
    db.add(customer)
    await db.commit()
    await db.refresh(customer)

    review = Review(product_id=checkout_fixtures["product"].id, user_id=customer.id, rating=5, body="Great!")
    db.add(review)
    await db.commit()
    await db.refresh(review)

    token = await _login(client, admin_user.email, "adminpass1")
    resp = await client.post(
        f"/admin/reviews/{review.id}/moderate",
        json={"status": "approved"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"

    await db.refresh(review)
    assert review.status == ReviewStatus.APPROVED


# ---------- Discount codes (strict admin) ----------


async def test_create_and_toggle_discount_code_strict_admin_only(client, admin_user):
    token = await _login(client, admin_user.email, "adminpass1")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post(
        "/admin/settings/discount-codes",
        json={"code": "summer20", "type": "percent", "value": "20", "usage_limit": 5},
        headers=headers,
    )
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["code"] == "SUMMER20"
    assert body["status"] == "ACTIVE"
    assert body["is_enabled"] is True

    toggle_resp = await client.post(f"/admin/settings/discount-codes/{body['id']}/toggle-active", headers=headers)
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["is_enabled"] is False
    assert toggle_resp.json()["status"] == "DISABLED"


async def test_staff_cannot_create_discount_code(client, db):
    headers = await _staff_headers(client, db)
    resp = await client.post(
        "/admin/settings/discount-codes",
        json={"code": "X", "type": "fixed", "value": "1"},
        headers=headers,
    )
    assert resp.status_code == 403


async def test_exhausted_discount_code_status(client, db, admin_user):
    token = await _login(client, admin_user.email, "adminpass1")
    headers = {"Authorization": f"Bearer {token}"}
    create_resp = await client.post(
        "/admin/settings/discount-codes",
        json={"code": "ONECODE", "type": "fixed", "value": "5", "usage_limit": 1},
        headers=headers,
    )
    discount_id = create_resp.json()["id"]

    import uuid

    from app.models.pricing import DiscountCode

    discount = await db.get(DiscountCode, uuid.UUID(discount_id))
    discount.times_used = 1
    await db.commit()

    list_resp = await client.get("/admin/settings/discount-codes", headers=headers)
    updated = next(c for c in list_resp.json() if c["id"] == discount_id)
    assert updated["status"] == "EXHAUSTED"
    assert updated["is_enabled"] is True  # still enabled - just exhausted, a real distinction from DISABLED


# ---------- Exchange rate (strict admin) ----------


async def test_update_and_get_exchange_rate(client, admin_user, checkout_fixtures):
    token = await _login(client, admin_user.email, "adminpass1")
    headers = {"Authorization": f"Bearer {token}"}

    update_resp = await client.put("/admin/settings/exchange-rate", json={"rate": "135.5"}, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["rate"] == "135.5000"
    assert update_resp.json()["updated_by_name"] == admin_user.name

    get_resp = await client.get("/admin/settings/exchange-rate", headers=headers)
    assert get_resp.json()["rate"] == "135.5000"


async def test_staff_cannot_update_exchange_rate(client, db, checkout_fixtures):
    headers = await _staff_headers(client, db)
    resp = await client.put("/admin/settings/exchange-rate", json={"rate": "999"}, headers=headers)
    assert resp.status_code == 403


# ---------- Pricing settings (strict admin) ----------


async def test_update_pricing_settings(client, admin_user, checkout_fixtures):
    token = await _login(client, admin_user.email, "adminpass1")
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.put(
        "/admin/settings/pricing",
        json={"commission_pct": "8", "shipping_per_kg_usd": "55", "packaging_fee_usd": "3", "kes_adjustment": "5"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["commission_pct"] == "8.00"

    get_resp = await client.get("/admin/settings/pricing", headers=headers)
    assert get_resp.json()["shipping_per_kg_usd"] == "55.00"


# ---------- Shipping rules (regular admin, NOT strict) ----------


async def test_staff_can_manage_shipping_rules_not_strict_admin_gated(client, db):
    headers = await _staff_headers(client, db)

    create_resp = await client.put(
        "/admin/settings/shipping-rules",
        json={
            "country_code": "us",
            "country_name": "United States",
            "base_fee_usd": "15",
            "per_kg_fee_usd": "6",
            "estimated_days_min": 5,
            "estimated_days_max": 10,
        },
        headers=headers,
    )
    assert create_resp.status_code == 200
    assert create_resp.json()["country_code"] == "US"

    list_resp = await client.get("/admin/settings/shipping-rules", headers=headers)
    assert any(r["country_code"] == "US" for r in list_resp.json())

    delete_resp = await client.delete("/admin/settings/shipping-rules/US", headers=headers)
    assert delete_resp.status_code == 204


async def test_upsert_shipping_rule_updates_existing(client, admin_user, checkout_fixtures):
    token = await _login(client, admin_user.email, "adminpass1")
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.put(
        "/admin/settings/shipping-rules",
        json={
            "country_code": "KE",
            "country_name": "Kenya Updated",
            "base_fee_usd": "20",
            "per_kg_fee_usd": "7",
            "estimated_days_min": 2,
            "estimated_days_max": 5,
        },
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["country_name"] == "Kenya Updated"
    assert resp.json()["base_fee_usd"] == "20.00"


async def test_delete_nonexistent_shipping_rule_404(client, admin_user):
    token = await _login(client, admin_user.email, "adminpass1")
    resp = await client.delete("/admin/settings/shipping-rules/ZZ", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


# ---------- Users (strict admin) ----------


async def test_strict_admin_can_create_user(client, admin_user):
    token = await _login(client, admin_user.email, "adminpass1")
    resp = await client.post(
        "/admin/users",
        json={"email": "newstaff@example.com", "name": "New Staff", "role": "STAFF", "password": "tempword123"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["role"] == "STAFF"
    assert resp.json()["is_active"] is True


async def test_create_user_duplicate_email_rejected(client, admin_user):
    token = await _login(client, admin_user.email, "adminpass1")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"email": "dupe@example.com", "name": "Dupe", "role": "STAFF", "password": "tempword123"}
    first = await client.post("/admin/users", json=payload, headers=headers)
    assert first.status_code == 201
    second = await client.post("/admin/users", json=payload, headers=headers)
    assert second.status_code == 409


async def test_staff_cannot_create_users(client, db):
    headers = await _staff_headers(client, db)
    resp = await client.post(
        "/admin/users",
        json={"email": "x@example.com", "name": "X", "role": "STAFF", "password": "tempword123"},
        headers=headers,
    )
    assert resp.status_code == 403


async def test_admin_cannot_deactivate_self(client, admin_user):
    token = await _login(client, admin_user.email, "adminpass1")
    resp = await client.post(
        f"/admin/users/{admin_user.id}/toggle-active", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 400


async def test_admin_can_deactivate_other_user(client, db, admin_user):
    token = await _login(client, admin_user.email, "adminpass1")
    headers = {"Authorization": f"Bearer {token}"}
    create_resp = await client.post(
        "/admin/users",
        json={"email": "todeactivate@example.com", "name": "Bye", "role": "STAFF", "password": "tempword123"},
        headers=headers,
    )
    user_id = create_resp.json()["id"]

    toggle_resp = await client.post(f"/admin/users/{user_id}/toggle-active", headers=headers)
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["is_active"] is False

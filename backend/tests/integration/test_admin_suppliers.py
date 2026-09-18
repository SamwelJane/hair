from sqlalchemy import select

from app.models.identity import User
from app.models.orders import Order
from app.models.payments import SupplierOrder
from tests.integration.conftest import checkout_payload


async def _login(client, email, password) -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def test_admin_can_list_suppliers_with_product_count(client, admin_user, checkout_fixtures):
    token = await _login(client, admin_user.email, "adminpass1")
    resp = await client.get("/admin/suppliers", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["name"] == checkout_fixtures["supplier"].name
    assert body[0]["product_count"] == 1
    assert body[0]["user_id"] is None


async def test_strict_admin_can_create_supplier_with_login(client, db, admin_user):
    token = await _login(client, admin_user.email, "adminpass1")
    resp = await client.post(
        "/admin/suppliers",
        json={
            "name": "Supplier B",
            "country": "VN",
            "email": "SupplierB@Example.com",
            "whatsapp_number": "+84900000000",
            "default_margin_pct": "12.5",
            "temporary_password": "temp12345",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "supplierb@example.com"
    assert body["user_id"] is not None

    # The linked login is a real FK now, not an email-string match.
    user = (await db.execute(select(User).where(User.email == "supplierb@example.com"))).scalar_one()
    assert user.role.value == "SUPPLIER"
    assert str(user.id) == body["user_id"]


async def test_create_supplier_without_temporary_password_has_no_linked_user(client, admin_user):
    token = await _login(client, admin_user.email, "adminpass1")
    resp = await client.post(
        "/admin/suppliers",
        json={
            "name": "Supplier C",
            "country": "VN",
            "email": "supplierc@example.com",
            "whatsapp_number": "+84900000001",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["user_id"] is None


async def test_staff_cannot_create_supplier_strict_admin_only(client, db, checkout_fixtures):
    from app.core.security import hash_password
    from app.models.enums import UserRole

    staff = User(email="staffsup@example.com", name="Staff", password_hash=hash_password("staffpass1"), role=UserRole.STAFF)
    db.add(staff)
    await db.commit()

    token = await _login(client, "staffsup@example.com", "staffpass1")
    resp = await client.post(
        "/admin/suppliers",
        json={"name": "X", "country": "KE", "email": "x@example.com", "whatsapp_number": "+254700000001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_supplier_detail_shows_performance_and_pending_orders(client, db, admin_user, checkout_fixtures):
    token = await _login(client, admin_user.email, "adminpass1")
    headers = {"Authorization": f"Bearer {token}"}

    order_number = (await client.post("/orders", json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id))).json()["order_number"]
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()
    await client.post(f"/admin/orders/{order.id}/status", json={"to_status": "PAID"}, headers=headers)
    await client.post(f"/admin/orders/{order.id}/status", json={"to_status": "SENT_TO_SUPPLIER"}, headers=headers)

    supplier = checkout_fixtures["supplier"]
    detail_resp = await client.get(f"/admin/suppliers/{supplier.id}", headers=headers)
    assert detail_resp.status_code == 200
    body = detail_resp.json()
    assert body["performance"]["total_orders"] == 1
    assert body["performance"]["completed_orders"] == 0
    assert len(body["pending_orders"]) == 1
    assert body["pending_orders"][0]["status"] == "SENT"
    assert body["pending_orders"][0]["order_number"] == order_number


async def test_advance_supplier_order_through_full_lifecycle_and_syncs_order_status(client, db, admin_user, checkout_fixtures):
    token = await _login(client, admin_user.email, "adminpass1")
    headers = {"Authorization": f"Bearer {token}"}

    order_number = (await client.post("/orders", json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id))).json()["order_number"]
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()
    await client.post(f"/admin/orders/{order.id}/status", json={"to_status": "PAID"}, headers=headers)
    await client.post(f"/admin/orders/{order.id}/status", json={"to_status": "SENT_TO_SUPPLIER"}, headers=headers)
    await client.post(f"/admin/orders/{order.id}/status", json={"to_status": "SUPPLIER_PROCESSING"}, headers=headers)

    supplier_order = (await db.execute(select(SupplierOrder).where(SupplierOrder.order_id == order.id))).scalar_one()

    advance1 = await client.post(f"/admin/supplier-orders/{supplier_order.id}/advance", headers=headers)
    assert advance1.status_code == 200
    assert advance1.json()["status"] == "ACKNOWLEDGED"

    advance2 = await client.post(f"/admin/supplier-orders/{supplier_order.id}/advance", headers=headers)
    assert advance2.json()["status"] == "IN_PRODUCTION"

    advance3 = await client.post(f"/admin/supplier-orders/{supplier_order.id}/advance", headers=headers)
    assert advance3.json()["status"] == "READY"

    # Reaching READY on the only supplier order should auto-advance the
    # parent order out of SUPPLIER_PROCESSING (sync_order_status_from_supplier_orders).
    await db.refresh(order)
    assert order.status.value == "READY_FOR_PICKUP"

    await db.refresh(supplier_order)
    assert supplier_order.confirmed_at is not None

    # No further advance possible from READY.
    advance4 = await client.post(f"/admin/supplier-orders/{supplier_order.id}/advance", headers=headers)
    assert advance4.status_code == 400


async def test_advance_nonexistent_supplier_order_returns_404(client, admin_user):
    token = await _login(client, admin_user.email, "adminpass1")
    resp = await client.post(
        "/admin/supplier-orders/00000000-0000-0000-0000-000000000000/advance",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404

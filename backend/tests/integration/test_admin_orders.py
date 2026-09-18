from sqlalchemy import select

from app.models.enums import OrderStatus, SupplierOrderStatus
from app.models.orders import Order
from app.models.payments import SupplierOrder
from tests.integration.conftest import checkout_payload


async def _login(client, email, password) -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _create_order(client, product, variant) -> str:
    resp = await client.post("/orders", json=checkout_payload(product.id, variant.id))
    assert resp.status_code == 201
    return resp.json()["order_number"]


async def test_non_admin_cannot_list_orders(client, checkout_fixtures):
    resp = await client.get("/admin/orders")
    assert resp.status_code == 401

    register_resp = await client.post(
        "/auth/register", json={"name": "Cust", "email": "cust@example.com", "password": "supersecret1"}
    )
    token = register_resp.json()["access_token"]
    resp = await client.get("/admin/orders", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


async def test_admin_can_list_orders_with_filters(client, db, admin_user, checkout_fixtures):
    order_number = await _create_order(client, checkout_fixtures["product"], checkout_fixtures["variant"])
    token = await _login(client, admin_user.email, "adminpass1")

    list_resp = await client.get("/admin/orders", headers={"Authorization": f"Bearer {token}"})
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1
    assert list_resp.json()["orders"][0]["order_number"] == order_number

    q_resp = await client.get(
        "/admin/orders", params={"q": order_number}, headers={"Authorization": f"Bearer {token}"}
    )
    assert q_resp.json()["total"] == 1

    q_miss_resp = await client.get(
        "/admin/orders", params={"q": "NOTHINGMATCHES"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert q_miss_resp.json()["total"] == 0

    status_resp = await client.get(
        "/admin/orders", params={"status": "PAID"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert status_resp.json()["total"] == 0  # order is PENDING_PAYMENT, not PAID


async def test_admin_can_view_order_detail_with_next_statuses(client, admin_user, checkout_fixtures):
    order_number = await _create_order(client, checkout_fixtures["product"], checkout_fixtures["variant"])
    token = await _login(client, admin_user.email, "adminpass1")

    list_resp = await client.get("/admin/orders", headers={"Authorization": f"Bearer {token}"})
    order_id = None
    # fetch id via detail lookup through DB, since list doesn't return id... actually list DOES return id
    order_id = list_resp.json()["orders"][0]["id"]

    detail_resp = await client.get(f"/admin/orders/{order_id}", headers={"Authorization": f"Bearer {token}"})
    assert detail_resp.status_code == 200
    body = detail_resp.json()
    assert body["order_number"] == order_number
    assert body["status"] == "PENDING_PAYMENT"
    assert set(body["next_statuses"]) == {"PAID", "CANCELLED"}
    assert len(body["items"]) == 1
    assert body["packages"] == []


async def test_admin_can_transition_order_status(client, db, admin_user, checkout_fixtures):
    order_number = await _create_order(client, checkout_fixtures["product"], checkout_fixtures["variant"])
    token = await _login(client, admin_user.email, "adminpass1")

    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()

    resp = await client.post(
        f"/admin/orders/{order.id}/status",
        json={"to_status": "PAID", "note": "manually marked paid"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "PAID"
    assert set(resp.json()["next_statuses"]) == {"SENT_TO_SUPPLIER", "CANCELLED"}

    await db.refresh(order)
    assert order.status == OrderStatus.PAID


async def test_invalid_status_transition_rejected(client, db, admin_user, checkout_fixtures):
    order_number = await _create_order(client, checkout_fixtures["product"], checkout_fixtures["variant"])
    token = await _login(client, admin_user.email, "adminpass1")
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()

    # Cannot skip straight from PENDING_PAYMENT to DELIVERED.
    resp = await client.post(
        f"/admin/orders/{order.id}/status",
        json={"to_status": "DELIVERED"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


async def test_sent_to_supplier_transition_creates_supplier_order(client, db, admin_user, checkout_fixtures):
    order_number = await _create_order(client, checkout_fixtures["product"], checkout_fixtures["variant"])
    token = await _login(client, admin_user.email, "adminpass1")
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()

    await client.post(
        f"/admin/orders/{order.id}/status", json={"to_status": "PAID"}, headers={"Authorization": f"Bearer {token}"}
    )
    resp = await client.post(
        f"/admin/orders/{order.id}/status",
        json={"to_status": "SENT_TO_SUPPLIER"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()["supplier_orders"]) == 1
    assert resp.json()["supplier_orders"][0]["supplier_name"] == checkout_fixtures["supplier"].name

    supplier_orders = (
        (await db.execute(select(SupplierOrder).where(SupplierOrder.order_id == order.id))).scalars().all()
    )
    assert len(supplier_orders) == 1
    assert supplier_orders[0].status == SupplierOrderStatus.SENT


async def test_admin_order_detail_shows_packages_once_received(client, db, admin_user, warehouse_user, vn_warehouse, checkout_fixtures):
    order_number = await _create_order(client, checkout_fixtures["product"], checkout_fixtures["variant"])
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()

    warehouse_resp = await client.post("/auth/login", json={"email": warehouse_user.email, "password": "warehousepass1"})
    warehouse_headers = {"Authorization": f"Bearer {warehouse_resp.json()['access_token']}"}
    package_id = (
        await client.post(
            "/warehouse/packages/receive", json={"tracking_number": order.tracking_number}, headers=warehouse_headers
        )
    ).json()["id"]

    admin_token = await _login(client, admin_user.email, "adminpass1")
    detail_resp = await client.get(f"/admin/orders/{order.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert detail_resp.status_code == 200
    packages = detail_resp.json()["packages"]
    assert len(packages) == 1
    assert packages[0]["id"] == package_id
    assert packages[0]["status"] == "RECEIVED"
    assert packages[0]["consolidation_code"] is None


async def test_staff_role_can_view_and_transition_orders_not_just_strict_admin(client, db, checkout_fixtures):
    from app.core.security import hash_password
    from app.models.enums import UserRole
    from app.models.identity import User

    staff = User(email="staff2@example.com", name="Staff", password_hash=hash_password("staffpass1"), role=UserRole.STAFF)
    db.add(staff)
    await db.commit()

    order_number = await _create_order(client, checkout_fixtures["product"], checkout_fixtures["variant"])
    token = await _login(client, "staff2@example.com", "staffpass1")
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()

    resp = await client.post(
        f"/admin/orders/{order.id}/status",
        json={"to_status": "PAID"},
        headers={"Authorization": f"Bearer {token}"},
    )
    # General order management (not strict-admin-gated) should be usable by STAFF.
    assert resp.status_code == 200

from sqlalchemy import select

from app.models.orders import Order
from tests.integration.conftest import checkout_payload


async def _register(client, email="customer@example.com") -> str:
    resp = await client.post("/auth/register", json={"name": "Cust", "email": email, "password": "supersecret1"})
    assert resp.status_code == 201
    return resp.json()["access_token"]


async def _login_admin(client, admin_user) -> str:
    resp = await client.post("/auth/login", json={"email": admin_user.email, "password": "adminpass1"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def test_list_my_orders_only_returns_own_orders_newest_first(client, checkout_fixtures):
    token = await _register(client)
    headers = {"Authorization": f"Bearer {token}"}

    other_token = await _register(client, email="other@example.com")
    await client.post(
        "/orders",
        json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id),
        headers={"Authorization": f"Bearer {other_token}"},
    )

    for _ in range(2):
        resp = await client.post(
            "/orders",
            json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id),
            headers=headers,
        )
        assert resp.status_code == 201

    list_resp = await client.get("/orders", headers=headers)
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["total"] == 2
    assert len(body["orders"]) == 2


async def test_list_my_orders_requires_auth(client):
    resp = await client.get("/orders")
    assert resp.status_code == 401


async def test_tracking_number_is_immutable_across_status_transitions(client, db, admin_user, checkout_fixtures):
    checkout_resp = await client.post(
        "/orders", json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id)
    )
    order_number = checkout_resp.json()["order_number"]
    tracking_number = checkout_resp.json()["tracking_number"]

    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()
    admin_token = await _login_admin(client, admin_user)
    headers = {"Authorization": f"Bearer {admin_token}"}

    for to_status in ["PAID", "SENT_TO_SUPPLIER", "SUPPLIER_PROCESSING", "READY_FOR_PICKUP", "RECEIVED_AT_OFFICE"]:
        resp = await client.post(f"/admin/orders/{order.id}/status", json={"to_status": to_status}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["tracking_number"] == tracking_number

    await db.refresh(order)
    assert order.tracking_number == tracking_number


async def test_customer_can_cancel_own_pending_order(client, db, checkout_fixtures):
    token = await _register(client)
    headers = {"Authorization": f"Bearer {token}"}

    order_number = (
        await client.post(
            "/orders",
            json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id),
            headers=headers,
        )
    ).json()["order_number"]

    resp = await client.post(f"/orders/{order_number}/cancel", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELLED"

    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()
    assert order.status.value == "CANCELLED"


async def test_cannot_cancel_someone_elses_order(client, checkout_fixtures):
    owner_token = await _register(client, email="owner@example.com")
    order_number = (
        await client.post(
            "/orders",
            json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id),
            headers={"Authorization": f"Bearer {owner_token}"},
        )
    ).json()["order_number"]

    intruder_token = await _register(client, email="intruder@example.com")
    resp = await client.post(
        f"/orders/{order_number}/cancel", headers={"Authorization": f"Bearer {intruder_token}"}
    )
    assert resp.status_code == 404


async def test_cannot_cancel_order_in_invalid_state(client, db, admin_user, checkout_fixtures):
    token = await _register(client)
    headers = {"Authorization": f"Bearer {token}"}

    order_number = (
        await client.post(
            "/orders",
            json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id),
            headers=headers,
        )
    ).json()["order_number"]
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()

    admin_token = await _login_admin(client, admin_user)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    for status in ["PAID", "SENT_TO_SUPPLIER", "SUPPLIER_PROCESSING", "READY_FOR_PICKUP", "RECEIVED_AT_OFFICE", "SHIPPED_INTERNATIONALLY"]:
        await client.post(f"/admin/orders/{order.id}/status", json={"to_status": status}, headers=admin_headers)

    resp = await client.post(f"/orders/{order_number}/cancel", headers=headers)
    assert resp.status_code == 400


async def test_order_detail_has_no_packages_before_receipt(client, checkout_fixtures):
    token = await _register(client)
    headers = {"Authorization": f"Bearer {token}"}

    order_number = (
        await client.post(
            "/orders",
            json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id),
            headers=headers,
        )
    ).json()["order_number"]

    resp = await client.get(f"/orders/{order_number}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["packages"] == []


async def test_order_detail_lists_packages_after_warehouse_receipt(client, warehouse_user, vn_warehouse, checkout_fixtures):
    token = await _register(client)
    headers = {"Authorization": f"Bearer {token}"}

    body = (
        await client.post(
            "/orders",
            json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id),
            headers=headers,
        )
    ).json()
    order_number, tracking_number = body["order_number"], body["tracking_number"]

    login_resp = await client.post(
        "/auth/login", json={"email": warehouse_user.email, "password": "warehousepass1"}
    )
    warehouse_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
    await client.post(
        "/warehouse/packages/receive", json={"tracking_number": tracking_number}, headers=warehouse_headers
    )

    resp = await client.get(f"/orders/{order_number}", headers=headers)
    assert resp.status_code == 200
    packages = resp.json()["packages"]
    assert len(packages) == 1
    assert packages[0]["status"] == "RECEIVED"
    assert packages[0]["package_code"].startswith("PKG-")

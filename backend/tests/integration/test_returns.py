from sqlalchemy import select

from app.models.orders import Order
from tests.integration.conftest import checkout_payload

_DELIVERY_STATUSES = [
    "PAID", "SENT_TO_SUPPLIER", "SUPPLIER_PROCESSING", "READY_FOR_PICKUP", "RECEIVED_AT_OFFICE",
    "SHIPPED_INTERNATIONALLY", "IN_TRANSIT", "DELIVERED",
]


async def _register(client, email="customer@example.com") -> str:
    resp = await client.post("/auth/register", json={"name": "Cust", "email": email, "password": "supersecret1"})
    assert resp.status_code == 201
    return resp.json()["access_token"]


async def _login_admin(client, admin_user) -> str:
    resp = await client.post("/auth/login", json={"email": admin_user.email, "password": "adminpass1"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _create_delivered_order(client, db, admin_user, checkout_fixtures, customer_token) -> Order:
    order_number = (
        await client.post(
            "/orders",
            json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id),
            headers={"Authorization": f"Bearer {customer_token}"},
        )
    ).json()["order_number"]
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()

    admin_token = await _login_admin(client, admin_user)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    for status in _DELIVERY_STATUSES:
        await client.post(f"/admin/orders/{order.id}/status", json={"to_status": status}, headers=admin_headers)

    await db.refresh(order)
    return order


async def test_request_return_on_delivered_order(client, db, admin_user, checkout_fixtures):
    token = await _register(client)
    order = await _create_delivered_order(client, db, admin_user, checkout_fixtures, token)

    resp = await client.post(
        "/returns", json={"order_id": str(order.id), "reason": "Wrong color"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "REQUESTED"


async def test_cannot_request_return_on_non_delivered_order(client, checkout_fixtures):
    token = await _register(client)
    order_number = (
        await client.post(
            "/orders",
            json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id),
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()["order_number"]

    resp_lookup = await client.get(f"/orders/{order_number}", headers={"Authorization": f"Bearer {token}"})
    order_id = resp_lookup.json()["id"]

    resp = await client.post(
        "/returns", json={"order_id": order_id, "reason": "Changed my mind"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 400


async def test_cannot_request_return_on_someone_elses_order(client, db, admin_user, checkout_fixtures):
    owner_token = await _register(client, email="owner@example.com")
    order = await _create_delivered_order(client, db, admin_user, checkout_fixtures, owner_token)

    intruder_token = await _register(client, email="intruder@example.com")
    resp = await client.post(
        "/returns", json={"order_id": str(order.id), "reason": "x"}, headers={"Authorization": f"Bearer {intruder_token}"}
    )
    assert resp.status_code == 404


async def test_cannot_request_second_open_return_for_same_order(client, db, admin_user, checkout_fixtures):
    token = await _register(client)
    order = await _create_delivered_order(client, db, admin_user, checkout_fixtures, token)
    headers = {"Authorization": f"Bearer {token}"}

    first = await client.post("/returns", json={"order_id": str(order.id), "reason": "a"}, headers=headers)
    assert first.status_code == 201
    second = await client.post("/returns", json={"order_id": str(order.id), "reason": "b"}, headers=headers)
    assert second.status_code == 409

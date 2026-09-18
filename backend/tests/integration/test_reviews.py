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


async def test_submit_review_on_delivered_order(client, db, admin_user, checkout_fixtures):
    token = await _register(client)
    order = await _create_delivered_order(client, db, admin_user, checkout_fixtures, token)

    resp = await client.post(
        "/reviews",
        json={"order_id": str(order.id), "product_id": str(checkout_fixtures["product"].id), "rating": 5, "body": "Lovely!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "pending"
    assert body["rating"] == 5


async def test_cannot_review_non_delivered_order(client, db, checkout_fixtures):
    token = await _register(client)
    order_number = (
        await client.post(
            "/orders",
            json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id),
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()["order_number"]
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()

    resp = await client.post(
        "/reviews",
        json={"order_id": str(order.id), "product_id": str(checkout_fixtures["product"].id), "rating": 5, "body": "x"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


async def test_cannot_review_someone_elses_order(client, db, admin_user, checkout_fixtures):
    owner_token = await _register(client, email="owner@example.com")
    order = await _create_delivered_order(client, db, admin_user, checkout_fixtures, owner_token)

    intruder_token = await _register(client, email="intruder@example.com")
    resp = await client.post(
        "/reviews",
        json={"order_id": str(order.id), "product_id": str(checkout_fixtures["product"].id), "rating": 5, "body": "x"},
        headers={"Authorization": f"Bearer {intruder_token}"},
    )
    assert resp.status_code == 404


async def test_cannot_review_product_not_in_order(client, db, admin_user, checkout_fixtures):
    import uuid

    token = await _register(client)
    order = await _create_delivered_order(client, db, admin_user, checkout_fixtures, token)

    resp = await client.post(
        "/reviews",
        json={"order_id": str(order.id), "product_id": str(uuid.uuid4()), "rating": 5, "body": "x"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


async def test_cannot_submit_duplicate_review(client, db, admin_user, checkout_fixtures):
    token = await _register(client)
    order = await _create_delivered_order(client, db, admin_user, checkout_fixtures, token)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"order_id": str(order.id), "product_id": str(checkout_fixtures["product"].id), "rating": 4, "body": "x"}

    first = await client.post("/reviews", json=payload, headers=headers)
    assert first.status_code == 201
    second = await client.post("/reviews", json=payload, headers=headers)
    assert second.status_code == 409

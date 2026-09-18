from sqlalchemy import select

from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.identity import User
from app.models.orders import Order
from app.models.payments import SupplierOrder
from tests.integration.conftest import checkout_payload


async def _login(client, email, password) -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _create_sent_supplier_order(client, db, admin_user, checkout_fixtures) -> SupplierOrder:
    """Drives an order through PAID -> SENT_TO_SUPPLIER -> SUPPLIER_PROCESSING
    via the admin endpoint (mirrors test_admin_suppliers.py), leaving one
    SupplierOrder in SENT status for the supplier-facing tests to act on."""
    admin_token = await _login(client, admin_user.email, "adminpass1")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    order_number = (
        await client.post(
            "/orders", json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id)
        )
    ).json()["order_number"]
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()
    await client.post(f"/admin/orders/{order.id}/status", json={"to_status": "PAID"}, headers=admin_headers)
    await client.post(f"/admin/orders/{order.id}/status", json={"to_status": "SENT_TO_SUPPLIER"}, headers=admin_headers)
    await client.post(f"/admin/orders/{order.id}/status", json={"to_status": "SUPPLIER_PROCESSING"}, headers=admin_headers)

    return (await db.execute(select(SupplierOrder).where(SupplierOrder.order_id == order.id))).scalar_one()


async def _link_supplier_login(db, supplier, *, email: str, password: str) -> User:
    user = User(email=email, name="Supplier User", password_hash=hash_password(password), role=UserRole.SUPPLIER)
    db.add(user)
    await db.flush()
    supplier.user_id = user.id
    await db.commit()
    await db.refresh(user)
    return user


async def test_supplier_can_list_own_orders(client, db, admin_user, checkout_fixtures):
    supplier_order = await _create_sent_supplier_order(client, db, admin_user, checkout_fixtures)
    await _link_supplier_login(db, checkout_fixtures["supplier"], email="supplier-a@example.com", password="supplierpass1")

    token = await _login(client, "supplier-a@example.com", "supplierpass1")
    resp = await client.get("/supplier/orders", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["id"] == str(supplier_order.id)
    assert body[0]["status"] == "SENT"
    assert body[0]["items"][0]["quantity"] == 1


async def test_supplier_without_linked_profile_gets_404(client, db):
    user = User(
        email="unlinked-supplier@example.com", name="Unlinked", password_hash=hash_password("unlinkedpass1"),
        role=UserRole.SUPPLIER,
    )
    db.add(user)
    await db.commit()

    token = await _login(client, "unlinked-supplier@example.com", "unlinkedpass1")
    resp = await client.get("/supplier/orders", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


async def test_supplier_can_acknowledge_and_progress_to_ready(client, db, admin_user, checkout_fixtures):
    supplier_order = await _create_sent_supplier_order(client, db, admin_user, checkout_fixtures)
    await _link_supplier_login(db, checkout_fixtures["supplier"], email="supplier-a@example.com", password="supplierpass1")
    headers = {"Authorization": f"Bearer {await _login(client, 'supplier-a@example.com', 'supplierpass1')}"}

    ack = await client.post(
        f"/supplier/orders/{supplier_order.id}/status", json={"to_status": "ACKNOWLEDGED", "eta_days": 5}, headers=headers
    )
    assert ack.status_code == 200
    assert ack.json()["status"] == "ACKNOWLEDGED"

    production = await client.post(
        f"/supplier/orders/{supplier_order.id}/status", json={"to_status": "IN_PRODUCTION"}, headers=headers
    )
    assert production.json()["status"] == "IN_PRODUCTION"

    ready = await client.post(f"/supplier/orders/{supplier_order.id}/status", json={"to_status": "READY"}, headers=headers)
    assert ready.status_code == 200
    assert ready.json()["status"] == "READY"

    order = await db.get(Order, supplier_order.order_id)
    await db.refresh(order)
    assert order.status.value == "READY_FOR_PICKUP"


async def test_supplier_decline_requires_reason(client, db, admin_user, checkout_fixtures):
    supplier_order = await _create_sent_supplier_order(client, db, admin_user, checkout_fixtures)
    await _link_supplier_login(db, checkout_fixtures["supplier"], email="supplier-a@example.com", password="supplierpass1")
    headers = {"Authorization": f"Bearer {await _login(client, 'supplier-a@example.com', 'supplierpass1')}"}

    missing_reason = await client.post(
        f"/supplier/orders/{supplier_order.id}/status", json={"to_status": "DECLINED"}, headers=headers
    )
    assert missing_reason.status_code == 400

    declined = await client.post(
        f"/supplier/orders/{supplier_order.id}/status",
        json={"to_status": "DECLINED", "decline_reason": "Out of stock"},
        headers=headers,
    )
    assert declined.status_code == 200
    assert declined.json()["status"] == "DECLINED"
    assert declined.json()["decline_reason"] == "Out of stock"


async def test_supplier_cannot_update_another_suppliers_order(client, db, admin_user, checkout_fixtures):
    from decimal import Decimal

    from app.models.catalog import Supplier

    supplier_order = await _create_sent_supplier_order(client, db, admin_user, checkout_fixtures)

    other_supplier = Supplier(
        name="Supplier B", country="VN", email="supplier-b@example.com", whatsapp_number="+84900000000",
        default_margin_pct=Decimal(10),
    )
    db.add(other_supplier)
    await db.flush()
    await _link_supplier_login(db, other_supplier, email="supplier-b@example.com", password="supplierpass2")

    headers = {"Authorization": f"Bearer {await _login(client, 'supplier-b@example.com', 'supplierpass2')}"}
    resp = await client.post(
        f"/supplier/orders/{supplier_order.id}/status", json={"to_status": "ACKNOWLEDGED"}, headers=headers
    )
    assert resp.status_code == 403


async def test_supplier_invalid_transition_returns_400(client, db, admin_user, checkout_fixtures):
    supplier_order = await _create_sent_supplier_order(client, db, admin_user, checkout_fixtures)
    await _link_supplier_login(db, checkout_fixtures["supplier"], email="supplier-a@example.com", password="supplierpass1")
    headers = {"Authorization": f"Bearer {await _login(client, 'supplier-a@example.com', 'supplierpass1')}"}

    resp = await client.post(
        f"/supplier/orders/{supplier_order.id}/status", json={"to_status": "IN_PRODUCTION"}, headers=headers
    )
    assert resp.status_code == 400

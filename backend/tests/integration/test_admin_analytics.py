from decimal import Decimal

from sqlalchemy import select

from app.models.orders import Order
from tests.integration.conftest import checkout_payload

_TO_DELIVERED = [
    "PAID", "SENT_TO_SUPPLIER", "SUPPLIER_PROCESSING", "READY_FOR_PICKUP", "RECEIVED_AT_OFFICE",
    "SHIPPED_INTERNATIONALLY", "IN_TRANSIT", "DELIVERED",
]


async def _login(client, email, password) -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _register(client, email="customer@example.com") -> str:
    resp = await client.post("/auth/register", json={"name": "Cust", "email": email, "password": "supersecret1"})
    assert resp.status_code == 201
    return resp.json()["access_token"]


async def _deliver_order(client, db, admin_headers, checkout_fixtures, customer_token) -> Order:
    order_number = (
        await client.post(
            "/orders",
            json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id),
            headers={"Authorization": f"Bearer {customer_token}"},
        )
    ).json()["order_number"]
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()

    for status in _TO_DELIVERED:
        await client.post(f"/admin/orders/{order.id}/status", json={"to_status": status}, headers=admin_headers)

    await db.refresh(order)
    return order


async def test_analytics_requires_admin(client):
    token = await _register(client, email="notadmin@example.com")
    resp = await client.get("/admin/analytics/revenue", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


async def test_revenue_summary_after_delivered_order(client, db, admin_user, checkout_fixtures):
    admin_headers = {"Authorization": f"Bearer {await _login(client, admin_user.email, 'adminpass1')}"}
    customer_token = await _register(client)
    order = await _deliver_order(client, db, admin_headers, checkout_fixtures, customer_token)

    resp = await client.get("/admin/analytics/revenue", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert Decimal(body["total_revenue_usd"]) == order.total_amount_usd
    assert any(c["country"] == "KE" for c in body["revenue_by_country"])
    assert any(p["product_name"] == checkout_fixtures["product"].name for p in body["revenue_by_product"])


async def _login_warehouse(client, warehouse_user) -> dict:
    resp = await client.post("/auth/login", json={"email": warehouse_user.email, "password": "warehousepass1"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def test_finance_and_operations_summary_after_delivery(
    client, db, admin_user, warehouse_user, vn_warehouse, checkout_fixtures
):
    admin_headers = {"Authorization": f"Bearer {await _login(client, admin_user.email, 'adminpass1')}"}
    warehouse_headers = await _login_warehouse(client, warehouse_user)
    customer_token = await _register(client)

    checkout_resp = await client.post(
        "/orders",
        json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id),
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    order_number = checkout_resp.json()["order_number"]
    tracking_number = checkout_resp.json()["tracking_number"]
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()

    for status in ["PAID", "SENT_TO_SUPPLIER", "SUPPLIER_PROCESSING", "READY_FOR_PICKUP", "RECEIVED_AT_OFFICE"]:
        await client.post(f"/admin/orders/{order.id}/status", json={"to_status": status}, headers=admin_headers)

    # "total_shipments"/"shipments_in_transit" now reflect the real warehouse
    # pipeline (an order counts once it has a received Package; "in transit"
    # counts departed-but-not-yet-arrived Consolidations) rather than the
    # old admin-driven Shipment record - see docs/VNKE_ROADMAP.md Phase 6.
    package_id = (
        await client.post(
            "/warehouse/packages/receive", json={"tracking_number": tracking_number}, headers=warehouse_headers
        )
    ).json()["id"]
    await client.post(f"/warehouse/packages/{package_id}/qc", json={"qc_status": "PASSED"}, headers=warehouse_headers)
    consolidation_id = (
        await client.post("/warehouse/consolidations", json={}, headers=warehouse_headers)
    ).json()["id"]
    await client.post(
        f"/warehouse/consolidations/{consolidation_id}/packages", json={"package_id": package_id}, headers=warehouse_headers
    )
    await client.post(f"/warehouse/consolidations/{consolidation_id}/ready-for-export", headers=warehouse_headers)
    await client.post(f"/warehouse/consolidations/{consolidation_id}/depart", headers=warehouse_headers)

    for status in ["SHIPPED_INTERNATIONALLY", "IN_TRANSIT", "DELIVERED"]:
        await client.post(f"/admin/orders/{order.id}/status", json={"to_status": status}, headers=admin_headers)

    finance_resp = await client.get("/admin/analytics/finance", headers=admin_headers)
    assert finance_resp.status_code == 200
    assert finance_resp.json()["total_shipments"] == 1

    operations_resp = await client.get("/admin/analytics/operations", headers=admin_headers)
    assert operations_resp.status_code == 200
    ops_body = operations_resp.json()
    assert ops_body["shipments_in_transit"] == 1  # consolidation departed but not yet arrived
    assert any(p["product_name"] == checkout_fixtures["product"].name for p in ops_body["best_selling_products"])


async def test_dashboard_kpis(client, db, admin_user, checkout_fixtures):
    admin_headers = {"Authorization": f"Bearer {await _login(client, admin_user.email, 'adminpass1')}"}

    customer_token = await _register(client)
    await client.post(
        "/orders",
        json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id),
        headers={"Authorization": f"Bearer {customer_token}"},
    )

    resp = await client.get("/admin/analytics/dashboard-kpis", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["pending_orders"] >= 1
    assert body["pending_bank_transfer_payments"] >= 1


async def test_analytics_export_csv_variants(client, db, admin_user, checkout_fixtures):
    admin_headers = {"Authorization": f"Bearer {await _login(client, admin_user.email, 'adminpass1')}"}
    customer_token = await _register(client)
    await _deliver_order(client, db, admin_headers, checkout_fixtures, customer_token)

    for report_type in ["revenue", "products", "operations", "monthly", "finance", "logistics", "customs", "suppliers"]:
        resp = await client.get("/admin/analytics/export", params={"type": report_type}, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/csv")
        assert "attachment" in resp.headers["content-disposition"]


async def test_logistics_summary_reflects_package_counts(
    client, db, admin_user, warehouse_user, vn_warehouse, checkout_fixtures
):
    admin_headers = {"Authorization": f"Bearer {await _login(client, admin_user.email, 'adminpass1')}"}
    warehouse_headers = await _login_warehouse(client, warehouse_user)
    customer_token = await _register(client)

    tracking_number = (
        await client.post(
            "/orders",
            json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id),
            headers={"Authorization": f"Bearer {customer_token}"},
        )
    ).json()["tracking_number"]
    await client.post("/warehouse/packages/receive", json={"tracking_number": tracking_number}, headers=warehouse_headers)

    resp = await client.get("/admin/analytics/logistics", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert any(s["status"] == "RECEIVED" and s["count"] >= 1 for s in body["packages_by_status"])
    assert body["avg_warehouse_to_delivery_ready_days"] is None  # no package has reached READY_FOR_DELIVERY yet


async def test_logistics_and_customs_summaries_after_full_pipeline(
    client, db, admin_user, warehouse_user, kenya_ops_user, vn_warehouse, checkout_fixtures
):
    admin_headers = {"Authorization": f"Bearer {await _login(client, admin_user.email, 'adminpass1')}"}
    warehouse_headers = await _login_warehouse(client, warehouse_user)
    kenya_headers = {"Authorization": f"Bearer {await _login(client, kenya_ops_user.email, 'kenyaopspass1')}"}
    customer_token = await _register(client)

    tracking_number = (
        await client.post(
            "/orders",
            json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id),
            headers={"Authorization": f"Bearer {customer_token}"},
        )
    ).json()["tracking_number"]
    package_id = (
        await client.post("/warehouse/packages/receive", json={"tracking_number": tracking_number}, headers=warehouse_headers)
    ).json()["id"]
    await client.post(f"/warehouse/packages/{package_id}/qc", json={"qc_status": "PASSED"}, headers=warehouse_headers)
    consolidation_id = (await client.post("/warehouse/consolidations", json={}, headers=warehouse_headers)).json()["id"]
    await client.post(
        f"/warehouse/consolidations/{consolidation_id}/packages", json={"package_id": package_id}, headers=warehouse_headers
    )
    await client.post(f"/warehouse/consolidations/{consolidation_id}/ready-for-export", headers=warehouse_headers)
    await client.post(f"/warehouse/consolidations/{consolidation_id}/depart", headers=warehouse_headers)
    await client.post(f"/warehouse/consolidations/{consolidation_id}/mark-in-transit", json={}, headers=warehouse_headers)
    await client.post(f"/warehouse/consolidations/{consolidation_id}/arrive-kenya", headers=warehouse_headers)

    declarations = (
        await client.get("/warehouse/customs-declarations", params={"status": "PREPARING"}, headers=warehouse_headers)
    ).json()["declarations"]
    declaration_id = next(d["id"] for d in declarations if d["consolidation_id"] == consolidation_id)
    await client.post(
        f"/warehouse/customs-declarations/{declaration_id}/declare",
        json={"hs_code": "6704.20", "declared_value_usd": "150.00", "duty_usd": "10.00", "vat_usd": "24.00"},
        headers=kenya_headers,
    )
    await client.post(f"/warehouse/customs-declarations/{declaration_id}/clear", headers=kenya_headers)

    logistics_body = (await client.get("/admin/analytics/logistics", headers=admin_headers)).json()
    assert any(s["status"] == "READY_FOR_DELIVERY" and s["count"] >= 1 for s in logistics_body["packages_by_status"])
    assert logistics_body["avg_warehouse_to_delivery_ready_days"] is not None
    assert logistics_body["avg_transit_days"] is not None

    customs_body = (await client.get("/admin/analytics/customs", headers=admin_headers)).json()
    assert any(s["status"] == "CLEARED" and s["count"] >= 1 for s in customs_body["declarations_by_status"])
    assert Decimal(customs_body["total_duty_usd"]) == Decimal("10.00")
    assert Decimal(customs_body["total_vat_usd"]) == Decimal("24.00")
    assert customs_body["queries_raised_count"] == 0


async def test_supplier_performance_summary_after_acknowledged_order(client, db, admin_user, checkout_fixtures):
    from app.core.security import hash_password
    from app.models.enums import UserRole
    from app.models.identity import User
    from app.models.orders import Order
    from app.models.payments import SupplierOrder

    admin_headers = {"Authorization": f"Bearer {await _login(client, admin_user.email, 'adminpass1')}"}

    order_number = (
        await client.post(
            "/orders", json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id)
        )
    ).json()["order_number"]
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()
    await client.post(f"/admin/orders/{order.id}/status", json={"to_status": "PAID"}, headers=admin_headers)
    await client.post(f"/admin/orders/{order.id}/status", json={"to_status": "SENT_TO_SUPPLIER"}, headers=admin_headers)

    supplier_order = (await db.execute(select(SupplierOrder).where(SupplierOrder.order_id == order.id))).scalar_one()
    supplier = checkout_fixtures["supplier"]
    supplier_user = User(
        email="supplier-perf@example.com", name="Supplier Perf", password_hash=hash_password("supplierpass1"),
        role=UserRole.SUPPLIER,
    )
    db.add(supplier_user)
    await db.flush()
    supplier.user_id = supplier_user.id
    await db.commit()

    supplier_headers = {"Authorization": f"Bearer {await _login(client, 'supplier-perf@example.com', 'supplierpass1')}"}
    for to_status in ["ACKNOWLEDGED", "IN_PRODUCTION", "READY"]:
        step = await client.post(
            f"/supplier/orders/{supplier_order.id}/status",
            json={"to_status": to_status, "eta_days": 5} if to_status == "ACKNOWLEDGED" else {"to_status": to_status},
            headers=supplier_headers,
        )
        assert step.status_code == 200

    resp = await client.get("/admin/analytics/suppliers", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    entry = next(s for s in body["suppliers"] if s["supplier_name"] == supplier.name)
    assert entry["total_orders"] == 1
    assert entry["avg_processing_days"] is not None

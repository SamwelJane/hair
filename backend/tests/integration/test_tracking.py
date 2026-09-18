from datetime import UTC, datetime

from sqlalchemy import select

from app.models.enums import PackageQCStatus, PackageStatus
from app.models.orders import Order
from app.models.packages import Package
from tests.integration.conftest import checkout_payload


async def _login(client, email, password) -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _warehouse_headers(client, warehouse_user) -> dict:
    token = await _login(client, warehouse_user.email, "warehousepass1")
    return {"Authorization": f"Bearer {token}"}


async def _checkout(client, checkout_fixtures) -> tuple[str, str]:
    resp = await client.post(
        "/orders", json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id)
    )
    body = resp.json()
    return body["order_number"], body["tracking_number"]


async def test_track_unknown_number_returns_404(client):
    resp = await client.get("/track/VNKE-DOES-NOT-EXIST")
    assert resp.status_code == 404


async def test_track_platform_order_before_warehouse_receipt_shows_order_status(client, checkout_fixtures):
    _order_number, tracking_number = await _checkout(client, checkout_fixtures)

    resp = await client.get(f"/track/{tracking_number}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["tracking_number"] == tracking_number
    assert body["status"] == "PENDING_PAYMENT"
    assert body["packages"] == []
    assert body["events"] == []


async def test_track_platform_order_through_full_pipeline(client, warehouse_user, vn_warehouse, checkout_fixtures):
    headers = await _warehouse_headers(client, warehouse_user)
    _order_number, tracking_number = await _checkout(client, checkout_fixtures)

    package_id = (
        await client.post("/warehouse/packages/receive", json={"tracking_number": tracking_number}, headers=headers)
    ).json()["id"]

    resp = await client.get(f"/track/{tracking_number}")
    body = resp.json()
    assert body["status"] == "RECEIVED"
    assert [p["package_code"] for p in body["packages"]]
    assert body["events"][-1]["label"] == "Received at Cherubim Warehouse"

    await client.post(f"/warehouse/packages/{package_id}/qc", json={"qc_status": "PASSED"}, headers=headers)
    resp = await client.get(f"/track/{tracking_number}")
    assert resp.json()["status"] == "READY_FOR_CONSOLIDATION"
    assert resp.json()["events"][-1]["label"] == "Package Verified"

    consolidation_id = (
        await client.post("/warehouse/consolidations", json={}, headers=headers)
    ).json()["id"]
    await client.post(
        f"/warehouse/consolidations/{consolidation_id}/packages", json={"package_id": package_id}, headers=headers
    )
    resp = await client.get(f"/track/{tracking_number}")
    assert resp.json()["status"] == "CONSOLIDATED"
    assert resp.json()["events"][-1]["label"] == "Consolidated"

    await client.post(f"/warehouse/consolidations/{consolidation_id}/ready-for-export", headers=headers)
    await client.post(f"/warehouse/consolidations/{consolidation_id}/depart", headers=headers)
    resp = await client.get(f"/track/{tracking_number}")
    assert resp.json()["status"] == "IN_TRANSIT"
    assert resp.json()["events"][-1]["label"] == "Departed Vietnam"

    await client.post(
        f"/warehouse/consolidations/{consolidation_id}/mark-in-transit",
        json={"carrier": "DHL", "current_location": "Ho Chi Minh City Airport"},
        headers=headers,
    )
    resp = await client.get(f"/track/{tracking_number}")
    assert resp.json()["status"] == "IN_TRANSIT"
    assert resp.json()["events"][-1]["label"] == "In Transit to Kenya"
    assert resp.json()["events"][-1]["location"] == "Ho Chi Minh City Airport"

    await client.post(f"/warehouse/consolidations/{consolidation_id}/arrive-kenya", headers=headers)
    resp = await client.get(f"/track/{tracking_number}")
    assert resp.json()["status"] == "AT_CUSTOMS_KENYA"
    assert resp.json()["events"][-1]["label"] == "Customs in Kenya"
    assert resp.json()["delivery_estimate"] == {"min_days": 3, "max_days": 7}


async def test_track_platform_order_with_no_shipping_rule_has_no_estimate(client, db, checkout_fixtures):
    from app.models.pricing import CountryShippingRule

    order_number, tracking_number = await _checkout(client, checkout_fixtures)
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()
    await db.execute(
        CountryShippingRule.__table__.delete().where(CountryShippingRule.country_code == order.shipping_country)
    )
    await db.commit()

    resp = await client.get(f"/track/{tracking_number}")
    assert resp.status_code == 200
    assert resp.json()["delivery_estimate"] is None


async def test_track_multi_package_order_shows_least_advanced_combined_status(
    client, db, warehouse_user, vn_warehouse, checkout_fixtures
):
    headers = await _warehouse_headers(client, warehouse_user)
    order_number, tracking_number = await _checkout(client, checkout_fixtures)
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()

    package_id = (
        await client.post("/warehouse/packages/receive", json={"tracking_number": tracking_number}, headers=headers)
    ).json()["id"]
    await client.post(f"/warehouse/packages/{package_id}/qc", json={"qc_status": "PASSED"}, headers=headers)

    # A second physical package for the same order (e.g. a second supplier's
    # portion), inserted directly since the duplicate-receive guard is
    # per (order, supplier_order) and this test only needs two Package rows
    # in different states to verify the combined-status logic.
    db.add(
        Package(
            package_code="PKG-TESTSECOND",
            order_id=order.id,
            warehouse_id=vn_warehouse.id,
            status=PackageStatus.RECEIVED,
            qc_status=PackageQCStatus.PENDING,
            received_at=datetime.now(UTC),
        )
    )
    await db.commit()

    resp = await client.get(f"/track/{tracking_number}")
    body = resp.json()
    assert len(body["packages"]) == 2
    # One package is READY_FOR_CONSOLIDATION, the other is only RECEIVED -
    # the less-advanced one should win the combined status.
    assert body["status"] == "RECEIVED"


async def test_track_package_exception_bubbles_up_as_overall_status(client, warehouse_user, vn_warehouse, checkout_fixtures):
    headers = await _warehouse_headers(client, warehouse_user)
    _order_number, tracking_number = await _checkout(client, checkout_fixtures)
    package_id = (
        await client.post("/warehouse/packages/receive", json={"tracking_number": tracking_number}, headers=headers)
    ).json()["id"]

    await client.post(
        f"/warehouse/packages/{package_id}/qc",
        json={"qc_status": "FAILED", "condition": "DAMAGED", "notes": "Box crushed"},
        headers=headers,
    )

    resp = await client.get(f"/track/{tracking_number}")
    assert resp.json()["status"] == "EXCEPTION"


async def test_track_external_shipment(client, warehouse_user, vn_warehouse):
    headers = await _warehouse_headers(client, warehouse_user)
    create_resp = await client.post(
        "/warehouse/external-shipments",
        json={"customer_name": "Jane Doe", "customer_phone": "+254700000000"},
        headers=headers,
    )
    tracking_number = create_resp.json()["tracking_number"]

    resp = await client.get(f"/track/{tracking_number}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["tracking_number"] == tracking_number
    assert body["status"] == "RECEIVED"
    assert len(body["packages"]) == 1
    assert body["events"][-1]["label"] == "Received at Cherubim Warehouse"
    # No shipping_country on an external shipment - no delivery estimate.
    assert body["delivery_estimate"] is None

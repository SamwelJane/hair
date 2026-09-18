"""End-to-end fulfilment scenarios per the master spec's section 59 test
list. Most of these scenarios already have focused coverage elsewhere in the
suite (duplicate payment callback: test_payments.py, duplicate warehouse
scan: test_warehouse_packages.py, reprint label: test_warehouse_packages.py,
customs query: test_warehouse_customs.py) - this file's job is the
scenarios that specifically require walking an order/shipment across
multiple services in one continuous flow to prove the pieces compose
correctly together, which no single phase's own test file does end-to-end."""

from datetime import UTC, datetime

from sqlalchemy import select

from app.models.enums import OrderStatus, PackageQCStatus, PackageStatus, PaymentStatus
from app.models.orders import Order
from app.models.packages import Package
from app.models.payments import Payment
from app.services import customs as customs_service
from app.services import packages as packages_service
from tests.integration.conftest import checkout_payload


async def _login(client, email, password) -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _register(client, email: str, phone: str = "+254711111111") -> dict:
    resp = await client.post(
        "/auth/register", json={"name": "Cust", "email": email, "password": "supersecret1", "phone": phone}
    )
    assert resp.status_code == 201
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def _warehouse_headers(client, warehouse_user) -> dict:
    return {"Authorization": f"Bearer {await _login(client, warehouse_user.email, 'warehousepass1')}"}


async def _kenya_headers(client, kenya_ops_user) -> dict:
    return {"Authorization": f"Bearer {await _login(client, kenya_ops_user.email, 'kenyaopspass1')}"}


async def _walk_consolidation_to_customs_cleared(client, headers, kenya_headers, package_id: str) -> None:
    """Shared tail end of the platform-order and external-shipment lifecycle
    tests below - both converge on the same warehouse->customs pipeline
    once a Package exists."""
    await client.post(f"/warehouse/packages/{package_id}/qc", json={"qc_status": "PASSED"}, headers=headers)
    consolidation_id = (await client.post("/warehouse/consolidations", json={}, headers=headers)).json()["id"]
    await client.post(
        f"/warehouse/consolidations/{consolidation_id}/packages", json={"package_id": package_id}, headers=headers
    )
    await client.post(f"/warehouse/consolidations/{consolidation_id}/ready-for-export", headers=headers)
    await client.post(f"/warehouse/consolidations/{consolidation_id}/depart", headers=headers)
    await client.post(f"/warehouse/consolidations/{consolidation_id}/mark-in-transit", json={}, headers=headers)
    await client.post(f"/warehouse/consolidations/{consolidation_id}/arrive-kenya", headers=headers)

    declarations = (
        await client.get("/warehouse/customs-declarations", params={"status": "PREPARING"}, headers=headers)
    ).json()["declarations"]
    declaration_id = next(d["id"] for d in declarations if d["consolidation_id"] == consolidation_id)
    await client.post(
        f"/warehouse/customs-declarations/{declaration_id}/declare",
        json={"hs_code": "6704.20", "declared_value_usd": "150.00", "duty_usd": "10.00", "vat_usd": "24.00"},
        headers=kenya_headers,
    )
    clear_resp = await client.post(f"/warehouse/customs-declarations/{declaration_id}/clear", headers=kenya_headers)
    assert clear_resp.status_code == 200


async def test_platform_order_full_lifecycle_from_placement_to_customs_cleared(
    client, db, warehouse_user, kenya_ops_user, vn_warehouse, checkout_fixtures, monkeypatch
):
    sent: list[tuple[str, str]] = []

    async def fake_send_whatsapp(to: str, body: str) -> None:
        sent.append((to, body))

    monkeypatch.setattr(packages_service, "send_whatsapp", fake_send_whatsapp)
    monkeypatch.setattr(customs_service, "send_whatsapp", fake_send_whatsapp)

    customer_headers = await _register(client, "e2e-platform@example.com")
    checkout_resp = await client.post(
        "/orders",
        json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id),
        headers=customer_headers,
    )
    order_number, tracking_number = checkout_resp.json()["order_number"], checkout_resp.json()["tracking_number"]

    warehouse_headers = await _warehouse_headers(client, warehouse_user)
    kenya_headers = await _kenya_headers(client, kenya_ops_user)
    package_id = (
        await client.post(
            "/warehouse/packages/receive", json={"tracking_number": tracking_number}, headers=warehouse_headers
        )
    ).json()["id"]
    await _walk_consolidation_to_customs_cleared(client, warehouse_headers, kenya_headers, package_id)

    # Tracking number is immutable across the whole pipeline.
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()
    assert order.tracking_number == tracking_number

    # The public tracking page reflects the final state.
    track_resp = await client.get(f"/track/{tracking_number}")
    assert track_resp.json()["status"] == "READY_FOR_DELIVERY"

    # The customer's own order-detail page (Phase 9) shows the package.
    order_detail = (await client.get(f"/orders/{order_number}", headers=customer_headers)).json()
    assert len(order_detail["packages"]) == 1
    assert order_detail["packages"][0]["status"] == "READY_FOR_DELIVERY"

    # Both customer notifications fired: package-received (Phase 9) and
    # customs-cleared (Phase 9), to the same customer phone number.
    assert len(sent) == 2
    assert all(to == "+254711111111" for to, _ in sent)
    assert "arrived at our Vietnam warehouse" in sent[0][1]
    assert "cleared customs" in sent[1][1]


async def test_external_shipment_full_lifecycle_reaches_customs_cleared(
    client, db, warehouse_user, kenya_ops_user, vn_warehouse, monkeypatch
):
    sent: list[tuple[str, str]] = []

    async def fake_send_whatsapp(to: str, body: str) -> None:
        sent.append((to, body))

    monkeypatch.setattr(customs_service, "send_whatsapp", fake_send_whatsapp)

    warehouse_headers = await _warehouse_headers(client, warehouse_user)
    kenya_headers = await _kenya_headers(client, kenya_ops_user)

    create_resp = await client.post(
        "/warehouse/external-shipments",
        json={"customer_name": "Jane Doe", "customer_phone": "+254799999999", "supplier_reference": "SUP-E2E-1"},
        headers=warehouse_headers,
    )
    assert create_resp.status_code == 201
    shipment_id = create_resp.json()["id"]
    tracking_number = create_resp.json()["tracking_number"]
    assert tracking_number.startswith("VNKE-EXT-")

    package = (await db.execute(select(Package).where(Package.external_shipment_id == shipment_id))).scalar_one()

    await _walk_consolidation_to_customs_cleared(client, warehouse_headers, kenya_headers, str(package.id))

    track_resp = await client.get(f"/track/{tracking_number}")
    body = track_resp.json()
    assert body["status"] == "READY_FOR_DELIVERY"
    # An external shipment has no shipping_country, so no delivery estimate
    # can be computed - see routers/tracking.py.
    assert body["delivery_estimate"] is None

    # No User/account exists for this customer - the notification goes
    # straight to the phone number captured at intake.
    assert len(sent) == 1
    assert sent[0][0] == "+254799999999"
    assert "cleared customs" in sent[0][1]


async def test_multi_package_order_customer_view_reflects_every_package(
    client, db, warehouse_user, vn_warehouse, checkout_fixtures
):
    """Complements test_tracking.py's combined-status coverage for the same
    scenario by checking the customer-facing order-detail packages list
    (Phase 9) rather than the public tracking page."""
    headers = await _warehouse_headers(client, warehouse_user)
    customer_headers = await _register(client, "e2e-multipackage@example.com")
    checkout_resp = await client.post(
        "/orders",
        json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id),
        headers=customer_headers,
    )
    order_number, tracking_number = checkout_resp.json()["order_number"], checkout_resp.json()["tracking_number"]
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()

    first_package_id = (
        await client.post("/warehouse/packages/receive", json={"tracking_number": tracking_number}, headers=headers)
    ).json()["id"]
    await client.post(f"/warehouse/packages/{first_package_id}/qc", json={"qc_status": "PASSED"}, headers=headers)

    # A second physical package for the same order (e.g. a second
    # supplier's portion) - inserted directly since the duplicate-receive
    # guard is per (order, supplier_order), mirroring
    # test_tracking.py::test_track_multi_package_order_shows_least_advanced_combined_status.
    db.add(
        Package(
            package_code="PKG-E2ESECOND",
            order_id=order.id,
            warehouse_id=vn_warehouse.id,
            status=PackageStatus.RECEIVED,
            qc_status=PackageQCStatus.PENDING,
            received_at=datetime.now(UTC),
        )
    )
    await db.commit()

    order_detail = (await client.get(f"/orders/{order_number}", headers=customer_headers)).json()
    codes_and_statuses = {p["package_code"]: p["status"] for p in order_detail["packages"]}
    assert len(codes_and_statuses) == 2
    assert codes_and_statuses["PKG-E2ESECOND"] == "RECEIVED"
    assert any(status == "READY_FOR_CONSOLIDATION" for code, status in codes_and_statuses.items() if code != "PKG-E2ESECOND")


async def test_failed_mpesa_payment_leaves_order_unpaid_with_no_fulfilment_side_effects(client, db, checkout_fixtures):
    payload = checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id)
    payload["payment_method"] = "MPESA"
    payload["mpesa_phone"] = "+254711111111"
    resp = await client.post("/orders", json=payload)
    order_number = resp.json()["order_number"]
    guest_token = resp.json()["guest_access_token"]
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()
    payment = (await db.execute(select(Payment).where(Payment.order_id == order.id))).scalar_one()

    # M-Pesa isn't configured in tests, so checkout already marked the
    # payment FAILED (no Daraja credentials) - simulate a real pending STK
    # push so the callback lookup below can find it, mirroring
    # test_payments.py's success-path test.
    payment.provider_ref = "ws_CO_test_fail"
    payment.status = PaymentStatus.PENDING
    await db.commit()

    callback_body = {
        "Body": {
            "stkCallback": {
                "MerchantRequestID": "mr-fail-1",
                "CheckoutRequestID": "ws_CO_test_fail",
                "ResultCode": 1032,
                "ResultDesc": "Request cancelled by user.",
            }
        }
    }
    callback_resp = await client.post("/payments/mpesa/callback", json=callback_body)
    assert callback_resp.status_code == 200

    await db.refresh(payment)
    await db.refresh(order)
    assert payment.status == PaymentStatus.FAILED
    assert order.status == OrderStatus.PENDING_PAYMENT

    # No package can exist yet - nothing was ever sent to a supplier or the
    # warehouse for an order that never got paid.
    package_count = (
        await db.execute(select(Package).where(Package.order_id == order.id))
    ).scalars().all()
    assert package_count == []

    order_detail = (await client.get(f"/orders/{order_number}", params={"guest_token": guest_token})).json()
    assert order_detail["packages"] == []

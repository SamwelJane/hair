from app.routers.warehouse import packages as warehouse_packages_router
from app.services import packages as packages_service
from tests.integration.conftest import checkout_payload


async def _login(client, email, password) -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _checkout_and_get_tracking_number(client, checkout_fixtures) -> str:
    resp = await client.post(
        "/orders", json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id)
    )
    return resp.json()["tracking_number"]


async def test_receive_platform_package_by_tracking_number(client, warehouse_user, vn_warehouse, checkout_fixtures):
    tracking_number = await _checkout_and_get_tracking_number(client, checkout_fixtures)
    token = await _login(client, warehouse_user.email, "warehousepass1")
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/warehouse/packages/receive",
        json={"tracking_number": tracking_number, "weight_grams": 450, "condition": "GOOD"},
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["tracking_number"] == tracking_number
    assert body["status"] == "RECEIVED"
    assert body["weight_grams"] == 450


async def test_receiving_a_package_notifies_the_customer(client, warehouse_user, vn_warehouse, checkout_fixtures, monkeypatch):
    sent: list[tuple[str, str]] = []

    async def fake_send_whatsapp(to: str, body: str) -> None:
        sent.append((to, body))

    monkeypatch.setattr(packages_service, "send_whatsapp", fake_send_whatsapp)

    tracking_number = await _checkout_and_get_tracking_number(client, checkout_fixtures)
    token = await _login(client, warehouse_user.email, "warehousepass1")
    resp = await client.post(
        "/warehouse/packages/receive",
        json={"tracking_number": tracking_number},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201

    assert len(sent) == 1
    to, body = sent[0]
    assert to == "+254711111111"
    assert tracking_number in body


async def test_receive_unknown_tracking_number_returns_404(client, warehouse_user, vn_warehouse):
    token = await _login(client, warehouse_user.email, "warehousepass1")
    resp = await client.post(
        "/warehouse/packages/receive",
        json={"tracking_number": "VNKE-DOES-NOT-EXIST"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_duplicate_scan_of_same_tracking_number_is_rejected(client, warehouse_user, vn_warehouse, checkout_fixtures):
    tracking_number = await _checkout_and_get_tracking_number(client, checkout_fixtures)
    token = await _login(client, warehouse_user.email, "warehousepass1")
    headers = {"Authorization": f"Bearer {token}"}

    first = await client.post("/warehouse/packages/receive", json={"tracking_number": tracking_number}, headers=headers)
    assert first.status_code == 201

    second = await client.post("/warehouse/packages/receive", json={"tracking_number": tracking_number}, headers=headers)
    assert second.status_code == 409
    assert "already been received" in second.json()["detail"]


async def test_customer_cannot_receive_packages(client, checkout_fixtures):
    tracking_number = await _checkout_and_get_tracking_number(client, checkout_fixtures)
    resp = await client.post("/auth/register", json={"name": "Cust", "email": "cust2@example.com", "password": "supersecret1"})
    token = resp.json()["access_token"]

    resp = await client.post(
        "/warehouse/packages/receive",
        json={"tracking_number": tracking_number},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_qc_pass_advances_package_to_ready_for_consolidation(client, warehouse_user, vn_warehouse, checkout_fixtures):
    tracking_number = await _checkout_and_get_tracking_number(client, checkout_fixtures)
    token = await _login(client, warehouse_user.email, "warehousepass1")
    headers = {"Authorization": f"Bearer {token}"}

    package_id = (
        await client.post("/warehouse/packages/receive", json={"tracking_number": tracking_number}, headers=headers)
    ).json()["id"]

    resp = await client.post(f"/warehouse/packages/{package_id}/qc", json={"qc_status": "PASSED"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "READY_FOR_CONSOLIDATION"
    assert resp.json()["qc_status"] == "PASSED"


async def test_qc_fail_moves_package_to_exception_and_creates_ops_exception(
    client, db, warehouse_user, vn_warehouse, checkout_fixtures
):
    from sqlalchemy import select

    from app.models.exceptions import OpsException

    tracking_number = await _checkout_and_get_tracking_number(client, checkout_fixtures)
    token = await _login(client, warehouse_user.email, "warehousepass1")
    headers = {"Authorization": f"Bearer {token}"}

    package_id = (
        await client.post("/warehouse/packages/receive", json={"tracking_number": tracking_number}, headers=headers)
    ).json()["id"]

    resp = await client.post(
        f"/warehouse/packages/{package_id}/qc",
        json={"qc_status": "FAILED", "condition": "DAMAGED", "notes": "Box crushed in transit"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "EXCEPTION"

    exception = (
        await db.execute(select(OpsException).where(OpsException.entity_id == package_id))
    ).scalar_one()
    assert exception.type.value == "QC_FAILURE"
    assert exception.status.value == "OPEN"


async def test_weigh_computes_volume_from_dimensions(client, warehouse_user, vn_warehouse, checkout_fixtures):
    tracking_number = await _checkout_and_get_tracking_number(client, checkout_fixtures)
    token = await _login(client, warehouse_user.email, "warehousepass1")
    headers = {"Authorization": f"Bearer {token}"}

    package_id = (
        await client.post("/warehouse/packages/receive", json={"tracking_number": tracking_number}, headers=headers)
    ).json()["id"]

    resp = await client.post(
        f"/warehouse/packages/{package_id}/weigh",
        json={"weight_grams": 1200, "length_cm": "20", "width_cm": "15", "height_cm": "10"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["weight_grams"] == 1200
    # 20*15*10 cm^3 = 3000 cm^3 = 0.003 m^3
    assert body["volume_cbm"] == "0.0030"


async def test_print_then_reprint_label_keeps_same_tracking_number_and_no_new_package(
    client, db, warehouse_user, vn_warehouse, checkout_fixtures
):
    from sqlalchemy import func, select

    from app.models.packages import Package

    tracking_number = await _checkout_and_get_tracking_number(client, checkout_fixtures)
    token = await _login(client, warehouse_user.email, "warehousepass1")
    headers = {"Authorization": f"Bearer {token}"}

    package_id = (
        await client.post("/warehouse/packages/receive", json={"tracking_number": tracking_number}, headers=headers)
    ).json()["id"]

    print_resp = await client.post(f"/warehouse/packages/{package_id}/label", headers=headers)
    assert print_resp.status_code == 201
    printed = print_resp.json()
    assert printed["tracking_number"] == tracking_number
    assert printed["reprint_count"] == 0
    assert "***" not in printed["masked_customer_name"]  # sanity: it's a real masked name, not a placeholder bug

    # Calling print again while already printed must fail - use reprint instead.
    second_print = await client.post(f"/warehouse/packages/{package_id}/label", headers=headers)
    assert second_print.status_code == 409

    reprint_resp = await client.post(f"/warehouse/packages/{package_id}/label/reprint", headers=headers)
    assert reprint_resp.status_code == 200
    reprinted = reprint_resp.json()
    assert reprinted["tracking_number"] == tracking_number
    assert reprinted["reprint_count"] == 1

    reprint_again = await client.post(f"/warehouse/packages/{package_id}/label/reprint", headers=headers)
    assert reprint_again.json()["reprint_count"] == 2

    total_packages = (await db.execute(select(func.count()).select_from(Package))).scalar_one()
    assert total_packages == 1


async def test_reprint_before_first_print_is_rejected(client, warehouse_user, vn_warehouse, checkout_fixtures):
    tracking_number = await _checkout_and_get_tracking_number(client, checkout_fixtures)
    token = await _login(client, warehouse_user.email, "warehousepass1")
    headers = {"Authorization": f"Bearer {token}"}

    package_id = (
        await client.post("/warehouse/packages/receive", json={"tracking_number": tracking_number}, headers=headers)
    ).json()["id"]

    resp = await client.post(f"/warehouse/packages/{package_id}/label/reprint", headers=headers)
    assert resp.status_code == 400


async def test_upload_package_photo(client, warehouse_user, vn_warehouse, checkout_fixtures, monkeypatch):
    monkeypatch.setattr(warehouse_packages_router, "upload_image", lambda file_bytes, folder="x": ("https://img/test.jpg", "public123"))

    tracking_number = await _checkout_and_get_tracking_number(client, checkout_fixtures)
    token = await _login(client, warehouse_user.email, "warehousepass1")
    headers = {"Authorization": f"Bearer {token}"}

    package_id = (
        await client.post("/warehouse/packages/receive", json={"tracking_number": tracking_number}, headers=headers)
    ).json()["id"]

    resp = await client.post(
        f"/warehouse/packages/{package_id}/photos",
        files={"file": ("test.jpg", b"fake-image-bytes", "image/jpeg")},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["photo_urls"] == ["https://img/test.jpg"]


async def test_warehouse_dashboard_counts(client, warehouse_user, vn_warehouse, checkout_fixtures):
    tracking_number = await _checkout_and_get_tracking_number(client, checkout_fixtures)
    token = await _login(client, warehouse_user.email, "warehousepass1")
    headers = {"Authorization": f"Bearer {token}"}

    package_id = (
        await client.post("/warehouse/packages/receive", json={"tracking_number": tracking_number}, headers=headers)
    ).json()["id"]

    resp = await client.get("/warehouse/dashboard", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["received_today"] == 1
    assert body["pending_qc"] == 1
    assert body["pending_weighing"] == 1

    await client.post(f"/warehouse/packages/{package_id}/qc", json={"qc_status": "PASSED"}, headers=headers)
    resp2 = await client.get("/warehouse/dashboard", headers=headers)
    assert resp2.json()["ready_for_consolidation"] == 1
    assert resp2.json()["pending_qc"] == 0

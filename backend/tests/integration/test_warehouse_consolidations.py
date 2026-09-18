from tests.integration.conftest import checkout_payload


async def _login(client, email, password) -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _warehouse_headers(client, warehouse_user) -> dict:
    token = await _login(client, warehouse_user.email, "warehousepass1")
    return {"Authorization": f"Bearer {token}"}


async def _receive_ready_package(client, headers, checkout_fixtures) -> tuple[str, int]:
    """Creates an order, receives its package, passes QC (so it's eligible
    for consolidation), and records a weight/volume so aggregation has
    something real to sum. Returns (package_id, weight_grams)."""
    tracking_number = (
        await client.post(
            "/orders", json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id)
        )
    ).json()["tracking_number"]
    package_id = (
        await client.post("/warehouse/packages/receive", json={"tracking_number": tracking_number}, headers=headers)
    ).json()["id"]
    await client.post(f"/warehouse/packages/{package_id}/qc", json={"qc_status": "PASSED"}, headers=headers)
    await client.post(
        f"/warehouse/packages/{package_id}/weigh",
        json={"weight_grams": 1000, "length_cm": "10", "width_cm": "10", "height_cm": "10"},
        headers=headers,
    )
    return package_id, 1000


async def test_create_consolidation(client, warehouse_user, vn_warehouse):
    headers = await _warehouse_headers(client, warehouse_user)
    resp = await client.post(
        "/warehouse/consolidations", json={"origin_warehouse_id": str(vn_warehouse.id)}, headers=headers
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["consolidation_code"].startswith("CON-VN-")
    assert body["status"] == "OPEN"
    assert body["package_count"] == 0


async def test_create_consolidation_defaults_to_primary_vn_warehouse(client, warehouse_user, vn_warehouse):
    headers = await _warehouse_headers(client, warehouse_user)
    resp = await client.post("/warehouse/consolidations", json={}, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["origin_warehouse_id"] == str(vn_warehouse.id)


async def test_add_package_recomputes_weight_and_volume(client, warehouse_user, vn_warehouse, checkout_fixtures):
    headers = await _warehouse_headers(client, warehouse_user)
    consolidation_id = (
        await client.post("/warehouse/consolidations", json={"origin_warehouse_id": str(vn_warehouse.id)}, headers=headers)
    ).json()["id"]
    package_id, weight = await _receive_ready_package(client, headers, checkout_fixtures)

    resp = await client.post(
        f"/warehouse/consolidations/{consolidation_id}/packages", json={"package_id": package_id}, headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["package_count"] == 1
    assert body["total_weight_grams"] == weight
    # 10*10*10 cm^3 = 1000 cm^3 = 0.001 m^3
    assert body["total_volume_cbm"] == "0.0010"
    assert body["packages"][0]["id"] == package_id


async def test_add_package_marks_it_consolidated(client, db, warehouse_user, vn_warehouse, checkout_fixtures):
    from sqlalchemy import select

    from app.models.packages import Package

    headers = await _warehouse_headers(client, warehouse_user)
    consolidation_id = (
        await client.post("/warehouse/consolidations", json={"origin_warehouse_id": str(vn_warehouse.id)}, headers=headers)
    ).json()["id"]
    package_id, _ = await _receive_ready_package(client, headers, checkout_fixtures)

    await client.post(f"/warehouse/consolidations/{consolidation_id}/packages", json={"package_id": package_id}, headers=headers)

    package = (await db.execute(select(Package).where(Package.id == package_id))).scalar_one()
    assert package.status.value == "CONSOLIDATED"
    assert str(package.consolidation_id) == consolidation_id


async def test_cannot_add_package_not_yet_qc_passed(client, warehouse_user, vn_warehouse, checkout_fixtures):
    headers = await _warehouse_headers(client, warehouse_user)
    consolidation_id = (
        await client.post("/warehouse/consolidations", json={"origin_warehouse_id": str(vn_warehouse.id)}, headers=headers)
    ).json()["id"]

    tracking_number = (
        await client.post(
            "/orders", json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id)
        )
    ).json()["tracking_number"]
    package_id = (
        await client.post("/warehouse/packages/receive", json={"tracking_number": tracking_number}, headers=headers)
    ).json()["id"]

    resp = await client.post(
        f"/warehouse/consolidations/{consolidation_id}/packages", json={"package_id": package_id}, headers=headers
    )
    assert resp.status_code == 400
    assert "READY_FOR_CONSOLIDATION" in resp.json()["detail"]


async def test_cannot_add_same_package_to_two_consolidations(client, warehouse_user, vn_warehouse, checkout_fixtures):
    headers = await _warehouse_headers(client, warehouse_user)
    con1 = (
        await client.post("/warehouse/consolidations", json={"origin_warehouse_id": str(vn_warehouse.id)}, headers=headers)
    ).json()["id"]
    con2 = (
        await client.post("/warehouse/consolidations", json={"origin_warehouse_id": str(vn_warehouse.id)}, headers=headers)
    ).json()["id"]
    package_id, _ = await _receive_ready_package(client, headers, checkout_fixtures)

    first = await client.post(f"/warehouse/consolidations/{con1}/packages", json={"package_id": package_id}, headers=headers)
    assert first.status_code == 200

    second = await client.post(f"/warehouse/consolidations/{con2}/packages", json={"package_id": package_id}, headers=headers)
    assert second.status_code == 400
    assert "already assigned" in second.json()["detail"]


async def test_remove_package_restores_ready_for_consolidation_and_recomputes_totals(
    client, db, warehouse_user, vn_warehouse, checkout_fixtures
):
    from sqlalchemy import select

    from app.models.packages import Package

    headers = await _warehouse_headers(client, warehouse_user)
    consolidation_id = (
        await client.post("/warehouse/consolidations", json={"origin_warehouse_id": str(vn_warehouse.id)}, headers=headers)
    ).json()["id"]
    package_id, _ = await _receive_ready_package(client, headers, checkout_fixtures)
    await client.post(f"/warehouse/consolidations/{consolidation_id}/packages", json={"package_id": package_id}, headers=headers)

    resp = await client.delete(f"/warehouse/consolidations/{consolidation_id}/packages/{package_id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["package_count"] == 0
    assert body["total_weight_grams"] == 0

    package = (await db.execute(select(Package).where(Package.id == package_id))).scalar_one()
    assert package.status.value == "READY_FOR_CONSOLIDATION"
    assert package.consolidation_id is None


async def test_cannot_mark_empty_consolidation_ready_for_export(client, warehouse_user, vn_warehouse):
    headers = await _warehouse_headers(client, warehouse_user)
    consolidation_id = (
        await client.post("/warehouse/consolidations", json={"origin_warehouse_id": str(vn_warehouse.id)}, headers=headers)
    ).json()["id"]

    resp = await client.post(f"/warehouse/consolidations/{consolidation_id}/ready-for-export", headers=headers)
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()


async def test_lock_on_departure_blocks_further_package_changes(client, warehouse_user, vn_warehouse, checkout_fixtures):
    headers = await _warehouse_headers(client, warehouse_user)
    consolidation_id = (
        await client.post("/warehouse/consolidations", json={"origin_warehouse_id": str(vn_warehouse.id)}, headers=headers)
    ).json()["id"]
    package_id, _ = await _receive_ready_package(client, headers, checkout_fixtures)
    await client.post(f"/warehouse/consolidations/{consolidation_id}/packages", json={"package_id": package_id}, headers=headers)

    ready_resp = await client.post(f"/warehouse/consolidations/{consolidation_id}/ready-for-export", headers=headers)
    assert ready_resp.status_code == 200
    assert ready_resp.json()["status"] == "READY_FOR_EXPORT"

    # Spec section 16: a package in a departed/closed consolidation must not
    # accidentally be re-addable elsewhere - verified here by confirming the
    # *source* consolidation itself refuses further mutation once locked.
    another_package_id, _ = await _receive_ready_package(client, headers, checkout_fixtures)
    blocked_add = await client.post(
        f"/warehouse/consolidations/{consolidation_id}/packages", json={"package_id": another_package_id}, headers=headers
    )
    assert blocked_add.status_code == 400

    blocked_remove = await client.delete(f"/warehouse/consolidations/{consolidation_id}/packages/{package_id}", headers=headers)
    assert blocked_remove.status_code == 400

    depart_resp = await client.post(f"/warehouse/consolidations/{consolidation_id}/depart", headers=headers)
    assert depart_resp.status_code == 200
    assert depart_resp.json()["status"] == "DEPARTED"
    assert depart_resp.json()["departure_date"] is not None

    # Package.status must have advanced with the consolidation.
    detail = await client.get(f"/warehouse/packages/{package_id}", headers=headers)
    assert detail.json()["status"] == "IN_TRANSIT"

    # Cannot depart twice.
    double_depart = await client.post(f"/warehouse/consolidations/{consolidation_id}/depart", headers=headers)
    assert double_depart.status_code == 400


async def test_kenya_ops_can_confirm_arrival_and_report_exceptions(
    client, kenya_ops_user, warehouse_user, vn_warehouse, checkout_fixtures
):
    """Kenya-side staff are the ones physically receiving the batch, so they
    must be able to confirm arrival and flag a problem even though only VN
    warehouse staff can create/depart the consolidation itself - see the
    Phase 11 RBAC audit note in docs/VNKE_ROADMAP.md."""
    warehouse_headers = await _warehouse_headers(client, warehouse_user)
    consolidation_id = await _departed_consolidation(client, warehouse_headers, checkout_fixtures)
    await client.post(f"/warehouse/consolidations/{consolidation_id}/mark-in-transit", json={}, headers=warehouse_headers)

    kenya_headers = {"Authorization": f"Bearer {await _login(client, kenya_ops_user.email, 'kenyaopspass1')}"}
    arrive_resp = await client.post(f"/warehouse/consolidations/{consolidation_id}/arrive-kenya", headers=kenya_headers)
    assert arrive_resp.status_code == 200
    assert arrive_resp.json()["status"] == "ARRIVED"

    exception_resp = await client.post(
        f"/warehouse/consolidations/{consolidation_id}/exceptions",
        json={"exception_type": "CUSTOMS_HOLD", "severity": "HIGH", "description": "Missing one carton"},
        headers=kenya_headers,
    )
    assert exception_resp.status_code == 201


async def test_kenya_ops_can_read_but_not_create_consolidations(client, kenya_ops_user, warehouse_user, vn_warehouse):
    warehouse_headers = await _warehouse_headers(client, warehouse_user)
    await client.post("/warehouse/consolidations", json={"origin_warehouse_id": str(vn_warehouse.id)}, headers=warehouse_headers)

    kenya_token = await _login(client, kenya_ops_user.email, "kenyaopspass1")
    kenya_headers = {"Authorization": f"Bearer {kenya_token}"}

    list_resp = await client.get("/warehouse/consolidations", headers=kenya_headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    create_resp = await client.post(
        "/warehouse/consolidations", json={"origin_warehouse_id": str(vn_warehouse.id)}, headers=kenya_headers
    )
    assert create_resp.status_code == 403


async def test_create_consolidation_with_unknown_warehouse_returns_404(client, warehouse_user):
    headers = await _warehouse_headers(client, warehouse_user)
    resp = await client.post(
        "/warehouse/consolidations",
        json={"origin_warehouse_id": "00000000-0000-0000-0000-000000000000"},
        headers=headers,
    )
    assert resp.status_code == 404


async def _departed_consolidation(client, headers, checkout_fixtures) -> str:
    consolidation_id = (
        await client.post("/warehouse/consolidations", json={}, headers=headers)
    ).json()["id"]
    package_id, _ = await _receive_ready_package(client, headers, checkout_fixtures)
    await client.post(f"/warehouse/consolidations/{consolidation_id}/packages", json={"package_id": package_id}, headers=headers)
    await client.post(f"/warehouse/consolidations/{consolidation_id}/ready-for-export", headers=headers)
    await client.post(f"/warehouse/consolidations/{consolidation_id}/depart", headers=headers)
    return consolidation_id


async def test_mark_in_transit_generates_shipment_code_and_sets_carrier(client, warehouse_user, vn_warehouse, checkout_fixtures):
    headers = await _warehouse_headers(client, warehouse_user)
    consolidation_id = await _departed_consolidation(client, headers, checkout_fixtures)

    resp = await client.post(
        f"/warehouse/consolidations/{consolidation_id}/mark-in-transit",
        json={"carrier": "DHL", "carrier_tracking_reference": "AWB-123", "current_location": "HCMC Airport"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "IN_TRANSIT"
    assert body["shipment_code"].startswith("SHP-VNKE-")
    assert body["carrier"] == "DHL"
    assert body["carrier_tracking_reference"] == "AWB-123"
    assert body["current_location"] == "HCMC Airport"


async def test_cannot_mark_in_transit_before_departure(client, warehouse_user, vn_warehouse):
    headers = await _warehouse_headers(client, warehouse_user)
    consolidation_id = (
        await client.post("/warehouse/consolidations", json={}, headers=headers)
    ).json()["id"]

    resp = await client.post(f"/warehouse/consolidations/{consolidation_id}/mark-in-transit", json={}, headers=headers)
    assert resp.status_code == 400


async def test_transit_update_requires_in_transit_status(client, warehouse_user, vn_warehouse, checkout_fixtures):
    headers = await _warehouse_headers(client, warehouse_user)
    consolidation_id = await _departed_consolidation(client, headers, checkout_fixtures)

    # Still DEPARTED, not yet IN_TRANSIT.
    blocked = await client.post(
        f"/warehouse/consolidations/{consolidation_id}/transit-update", json={"current_location": "Nowhere"}, headers=headers
    )
    assert blocked.status_code == 400

    await client.post(f"/warehouse/consolidations/{consolidation_id}/mark-in-transit", json={}, headers=headers)
    ok = await client.post(
        f"/warehouse/consolidations/{consolidation_id}/transit-update",
        json={"current_location": "Bangkok"},
        headers=headers,
    )
    assert ok.status_code == 200
    assert ok.json()["current_location"] == "Bangkok"


async def test_arrive_kenya_transitions_consolidation_and_packages(client, warehouse_user, vn_warehouse, checkout_fixtures):
    headers = await _warehouse_headers(client, warehouse_user)
    consolidation_id = await _departed_consolidation(client, headers, checkout_fixtures)
    await client.post(f"/warehouse/consolidations/{consolidation_id}/mark-in-transit", json={}, headers=headers)

    resp = await client.post(f"/warehouse/consolidations/{consolidation_id}/arrive-kenya", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ARRIVED"
    assert body["arrival_date"] is not None
    assert body["current_location"] == "Kenya"
    assert body["packages"][0]["status"] == "AT_CUSTOMS_KENYA"


async def test_cannot_arrive_before_in_transit(client, warehouse_user, vn_warehouse, checkout_fixtures):
    headers = await _warehouse_headers(client, warehouse_user)
    consolidation_id = await _departed_consolidation(client, headers, checkout_fixtures)

    resp = await client.post(f"/warehouse/consolidations/{consolidation_id}/arrive-kenya", headers=headers)
    assert resp.status_code == 400


async def test_report_exception_creates_ops_exception(client, db, warehouse_user, vn_warehouse, checkout_fixtures):
    from sqlalchemy import select

    from app.models.exceptions import OpsException

    headers = await _warehouse_headers(client, warehouse_user)
    consolidation_id = await _departed_consolidation(client, headers, checkout_fixtures)

    resp = await client.post(
        f"/warehouse/consolidations/{consolidation_id}/exceptions",
        json={"exception_type": "CUSTOMS_HOLD", "severity": "HIGH", "description": "Manifest count mismatch"},
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["type"] == "CUSTOMS_HOLD"
    assert body["severity"] == "HIGH"
    assert body["status"] == "OPEN"

    exception = (
        await db.execute(select(OpsException).where(OpsException.entity_id == consolidation_id))
    ).scalar_one()
    assert exception.description == "Manifest count mismatch"

from app.services import customs as customs_service
from tests.integration.conftest import checkout_payload


async def _login(client, email, password) -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _warehouse_headers(client, warehouse_user) -> dict:
    token = await _login(client, warehouse_user.email, "warehousepass1")
    return {"Authorization": f"Bearer {token}"}


async def _kenya_ops_headers(client, kenya_ops_user) -> dict:
    token = await _login(client, kenya_ops_user.email, "kenyaopspass1")
    return {"Authorization": f"Bearer {token}"}


async def _arrived_consolidation_and_declaration(client, headers, checkout_fixtures) -> tuple[str, str]:
    """Walks a package all the way through receive -> QC -> consolidate ->
    ready-for-export -> depart -> in-transit -> arrive-kenya, which
    auto-creates a PREPARING CustomsDeclaration for the consolidation.
    Returns (consolidation_id, declaration_id)."""
    tracking_number = (
        await client.post(
            "/orders", json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id)
        )
    ).json()["tracking_number"]
    package_id = (
        await client.post("/warehouse/packages/receive", json={"tracking_number": tracking_number}, headers=headers)
    ).json()["id"]
    await client.post(f"/warehouse/packages/{package_id}/qc", json={"qc_status": "PASSED"}, headers=headers)

    consolidation_id = (await client.post("/warehouse/consolidations", json={}, headers=headers)).json()["id"]
    await client.post(f"/warehouse/consolidations/{consolidation_id}/packages", json={"package_id": package_id}, headers=headers)
    await client.post(f"/warehouse/consolidations/{consolidation_id}/ready-for-export", headers=headers)
    await client.post(f"/warehouse/consolidations/{consolidation_id}/depart", headers=headers)
    await client.post(f"/warehouse/consolidations/{consolidation_id}/mark-in-transit", json={}, headers=headers)
    await client.post(f"/warehouse/consolidations/{consolidation_id}/arrive-kenya", headers=headers)

    list_resp = await client.get(
        "/warehouse/customs-declarations", params={"status": "PREPARING"}, headers=headers
    )
    declarations = [d for d in list_resp.json()["declarations"] if d["consolidation_id"] == consolidation_id]
    assert len(declarations) == 1
    return consolidation_id, declarations[0]["id"]


async def test_customs_declaration_auto_created_on_arrival(client, warehouse_user, vn_warehouse, checkout_fixtures):
    headers = await _warehouse_headers(client, warehouse_user)
    consolidation_id, declaration_id = await _arrived_consolidation_and_declaration(client, headers, checkout_fixtures)

    resp = await client.get(f"/warehouse/customs-declarations/{declaration_id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "PREPARING"
    assert body["consolidation_id"] == consolidation_id
    assert body["hs_code"] is None


async def test_declare_customs_sets_fields_and_status(client, warehouse_user, kenya_ops_user, vn_warehouse, checkout_fixtures):
    headers = await _warehouse_headers(client, warehouse_user)
    _consolidation_id, declaration_id = await _arrived_consolidation_and_declaration(client, headers, checkout_fixtures)
    action_headers = await _kenya_ops_headers(client, kenya_ops_user)

    resp = await client.post(
        f"/warehouse/customs-declarations/{declaration_id}/declare",
        json={"hs_code": "6704.20", "declared_value_usd": "150.00", "duty_usd": "10.00", "vat_usd": "24.00"},
        headers=action_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "DECLARED"
    assert body["hs_code"] == "6704.20"
    assert body["declared_value_usd"] == "150.00"
    assert body["duty_usd"] == "10.00"
    assert body["vat_usd"] == "24.00"


async def test_cannot_declare_twice(client, warehouse_user, kenya_ops_user, vn_warehouse, checkout_fixtures):
    headers = await _warehouse_headers(client, warehouse_user)
    _consolidation_id, declaration_id = await _arrived_consolidation_and_declaration(client, headers, checkout_fixtures)
    action_headers = await _kenya_ops_headers(client, kenya_ops_user)

    payload = {"hs_code": "6704.20", "declared_value_usd": "150.00"}
    first = await client.post(f"/warehouse/customs-declarations/{declaration_id}/declare", json=payload, headers=action_headers)
    assert first.status_code == 200
    second = await client.post(f"/warehouse/customs-declarations/{declaration_id}/declare", json=payload, headers=action_headers)
    assert second.status_code == 400


async def test_query_requires_declared_status_and_creates_exception(
    client, db, warehouse_user, kenya_ops_user, vn_warehouse, checkout_fixtures
):
    from sqlalchemy import select

    from app.models.exceptions import OpsException

    headers = await _warehouse_headers(client, warehouse_user)
    _consolidation_id, declaration_id = await _arrived_consolidation_and_declaration(client, headers, checkout_fixtures)
    action_headers = await _kenya_ops_headers(client, kenya_ops_user)

    too_early = await client.post(
        f"/warehouse/customs-declarations/{declaration_id}/query", json={"note": "Missing invoice"}, headers=action_headers
    )
    assert too_early.status_code == 400

    await client.post(
        f"/warehouse/customs-declarations/{declaration_id}/declare",
        json={"hs_code": "6704.20", "declared_value_usd": "150.00"},
        headers=action_headers,
    )
    resp = await client.post(
        f"/warehouse/customs-declarations/{declaration_id}/query", json={"note": "Missing invoice"}, headers=action_headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "QUERY_RAISED"

    exception = (
        await db.execute(select(OpsException).where(OpsException.entity_id == declaration_id))
    ).scalar_one()
    assert exception.type.value == "CUSTOMS_QUERY"
    assert exception.description == "Missing invoice"


async def test_cannot_clear_while_still_preparing(client, warehouse_user, kenya_ops_user, vn_warehouse, checkout_fixtures):
    headers = await _warehouse_headers(client, warehouse_user)
    _consolidation_id, declaration_id = await _arrived_consolidation_and_declaration(client, headers, checkout_fixtures)
    action_headers = await _kenya_ops_headers(client, kenya_ops_user)

    resp = await client.post(f"/warehouse/customs-declarations/{declaration_id}/clear", headers=action_headers)
    assert resp.status_code == 400


async def test_clear_from_declared_closes_consolidation_and_advances_packages(
    client, db, warehouse_user, kenya_ops_user, vn_warehouse, checkout_fixtures
):
    from sqlalchemy import select

    from app.models.consolidation import Consolidation
    from app.models.packages import Package
    from app.models.tracking_events import TrackingEvent

    headers = await _warehouse_headers(client, warehouse_user)
    consolidation_id, declaration_id = await _arrived_consolidation_and_declaration(client, headers, checkout_fixtures)
    action_headers = await _kenya_ops_headers(client, kenya_ops_user)
    await client.post(
        f"/warehouse/customs-declarations/{declaration_id}/declare",
        json={"hs_code": "6704.20", "declared_value_usd": "150.00"},
        headers=action_headers,
    )

    resp = await client.post(f"/warehouse/customs-declarations/{declaration_id}/clear", headers=action_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "CLEARED"

    consolidation = (await db.execute(select(Consolidation).where(Consolidation.id == consolidation_id))).scalar_one()
    assert consolidation.status.value == "CLOSED"

    packages = (await db.execute(select(Package).where(Package.consolidation_id == consolidation_id))).scalars().all()
    assert all(p.status.value == "READY_FOR_DELIVERY" for p in packages)

    events = (
        await db.execute(select(TrackingEvent).where(TrackingEvent.package_id == packages[0].id))
    ).scalars().all()
    assert any(e.label == "Ready for Delivery" for e in events)


async def test_clear_notifies_the_customer(
    client, warehouse_user, kenya_ops_user, vn_warehouse, checkout_fixtures, monkeypatch
):
    sent: list[tuple[str, str]] = []

    async def fake_send_whatsapp(to: str, body: str) -> None:
        sent.append((to, body))

    monkeypatch.setattr(customs_service, "send_whatsapp", fake_send_whatsapp)

    headers = await _warehouse_headers(client, warehouse_user)
    _consolidation_id, declaration_id = await _arrived_consolidation_and_declaration(client, headers, checkout_fixtures)
    action_headers = await _kenya_ops_headers(client, kenya_ops_user)
    await client.post(
        f"/warehouse/customs-declarations/{declaration_id}/declare",
        json={"hs_code": "6704.20", "declared_value_usd": "150.00"},
        headers=action_headers,
    )

    resp = await client.post(f"/warehouse/customs-declarations/{declaration_id}/clear", headers=action_headers)
    assert resp.status_code == 200

    assert len(sent) == 1
    to, body = sent[0]
    assert to == "+254711111111"
    assert "cleared customs" in body


async def test_clear_from_query_raised_also_closes_out(client, warehouse_user, kenya_ops_user, vn_warehouse, checkout_fixtures):
    headers = await _warehouse_headers(client, warehouse_user)
    _consolidation_id, declaration_id = await _arrived_consolidation_and_declaration(client, headers, checkout_fixtures)
    action_headers = await _kenya_ops_headers(client, kenya_ops_user)
    await client.post(
        f"/warehouse/customs-declarations/{declaration_id}/declare",
        json={"hs_code": "6704.20", "declared_value_usd": "150.00"},
        headers=action_headers,
    )
    await client.post(f"/warehouse/customs-declarations/{declaration_id}/query", json={"note": "hold"}, headers=action_headers)

    resp = await client.post(f"/warehouse/customs-declarations/{declaration_id}/clear", headers=action_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "CLEARED"


async def test_kenya_ops_can_manage_customs(client, kenya_ops_user, warehouse_user, vn_warehouse, checkout_fixtures):
    warehouse_headers = await _warehouse_headers(client, warehouse_user)
    _consolidation_id, declaration_id = await _arrived_consolidation_and_declaration(client, warehouse_headers, checkout_fixtures)

    kenya_headers = await _kenya_ops_headers(client, kenya_ops_user)
    resp = await client.post(
        f"/warehouse/customs-declarations/{declaration_id}/declare",
        json={"hs_code": "6704.20", "declared_value_usd": "150.00"},
        headers=kenya_headers,
    )
    assert resp.status_code == 200


async def test_vn_warehouse_role_cannot_update_customs(client, warehouse_user, vn_warehouse, checkout_fixtures):
    headers = await _warehouse_headers(client, warehouse_user)
    _consolidation_id, declaration_id = await _arrived_consolidation_and_declaration(client, headers, checkout_fixtures)

    resp = await client.post(
        f"/warehouse/customs-declarations/{declaration_id}/declare",
        json={"hs_code": "6704.20", "declared_value_usd": "150.00"},
        headers=headers,
    )
    assert resp.status_code == 403


async def test_unknown_declaration_returns_404(client, warehouse_user):
    headers = await _warehouse_headers(client, warehouse_user)
    resp = await client.get(
        "/warehouse/customs-declarations/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert resp.status_code == 404

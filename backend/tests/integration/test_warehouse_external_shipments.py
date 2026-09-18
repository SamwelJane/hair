async def _login(client, email, password) -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def test_warehouse_staff_can_create_external_shipment(client, warehouse_user, vn_warehouse):
    token = await _login(client, warehouse_user.email, "warehousepass1")
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/warehouse/external-shipments",
        json={"customer_name": "Jane Doe", "customer_phone": "+254700000000", "supplier_reference": "SUP-001"},
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["tracking_number"].startswith("VNKE-EXT-")
    assert body["status"] == "ACTIVE"


async def test_create_external_shipment_creates_its_first_package(client, db, warehouse_user, vn_warehouse):
    from sqlalchemy import select

    from app.models.packages import Package

    token = await _login(client, warehouse_user.email, "warehousepass1")
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/warehouse/external-shipments",
        json={"customer_name": "Jane Doe", "customer_phone": "+254700000000", "weight_grams": 500},
        headers=headers,
    )
    shipment_id = resp.json()["id"]

    package = (await db.execute(select(Package).where(Package.external_shipment_id == shipment_id))).scalar_one()
    assert package.status.value == "RECEIVED"
    assert package.weight_grams == 500


async def test_customer_cannot_create_external_shipment(client):
    resp = await client.post(
        "/auth/register", json={"name": "Cust", "email": "cust@example.com", "password": "supersecret1"}
    )
    token = resp.json()["access_token"]

    resp = await client.post(
        "/warehouse/external-shipments",
        json={"customer_name": "Jane Doe", "customer_phone": "+254700000000"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_kenya_ops_can_read_but_not_create_external_shipments(client, kenya_ops_user, warehouse_user, vn_warehouse):
    warehouse_token = await _login(client, warehouse_user.email, "warehousepass1")
    await client.post(
        "/warehouse/external-shipments",
        json={"customer_name": "Jane Doe", "customer_phone": "+254700000000"},
        headers={"Authorization": f"Bearer {warehouse_token}"},
    )

    kenya_token = await _login(client, kenya_ops_user.email, "kenyaopspass1")
    kenya_headers = {"Authorization": f"Bearer {kenya_token}"}

    list_resp = await client.get("/warehouse/external-shipments", headers=kenya_headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    create_resp = await client.post(
        "/warehouse/external-shipments",
        json={"customer_name": "Other", "customer_phone": "+254700000001"},
        headers=kenya_headers,
    )
    assert create_resp.status_code == 403


async def test_get_unknown_external_shipment_returns_404(client, warehouse_user):
    token = await _login(client, warehouse_user.email, "warehousepass1")
    resp = await client.get(
        "/warehouse/external-shipments/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404

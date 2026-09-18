async def _login(client, email, password) -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def test_audit_logs_require_admin(client, checkout_fixtures):
    register_resp = await client.post(
        "/auth/register", json={"name": "Cust", "email": "cust-audit@example.com", "password": "supersecret1"}
    )
    token = register_resp.json()["access_token"]
    resp = await client.get("/admin/audit-logs", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


async def test_list_audit_logs_includes_actor_email_and_entity_types(client, admin_user, checkout_fixtures):
    token = await _login(client, admin_user.email, "adminpass1")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post(
        "/admin/suppliers",
        json={"name": "Supplier Audit", "country": "KE", "email": "supplier-audit@example.com", "whatsapp_number": "+254700000099"},
        headers=headers,
    )
    assert create_resp.status_code == 201

    resp = await client.get("/admin/audit-logs", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    create_supplier_entries = [e for e in body["items"] if e["action"] == "CREATE_SUPPLIER"]
    assert len(create_supplier_entries) == 1
    assert create_supplier_entries[0]["user_email"] == admin_user.email
    assert "Supplier" in body["entity_types"]


async def test_filter_by_action_and_entity_type(client, admin_user, checkout_fixtures):
    token = await _login(client, admin_user.email, "adminpass1")
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/admin/suppliers",
        json={"name": "Supplier Filter", "country": "KE", "email": "supplier-filter@example.com", "whatsapp_number": "+254700000098"},
        headers=headers,
    )

    resp = await client.get("/admin/audit-logs", params={"action": "create_supplier", "entity_type": "Supplier"}, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert all(e["entity_type"] == "Supplier" for e in body["items"])

    empty_resp = await client.get("/admin/audit-logs", params={"entity_type": "NoSuchEntity"}, headers=headers)
    assert empty_resp.json()["total"] == 0


async def test_export_audit_logs_returns_csv(client, admin_user, checkout_fixtures):
    token = await _login(client, admin_user.email, "adminpass1")
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/admin/suppliers",
        json={"name": "Supplier CSV", "country": "KE", "email": "supplier-csv@example.com", "whatsapp_number": "+254700000097"},
        headers=headers,
    )

    resp = await client.get("/admin/audit-logs/export", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert resp.headers["content-disposition"] == 'attachment; filename="audit-logs.csv"'
    lines = resp.text.splitlines()
    assert lines[0] == "when,actor,action,entityType,entityId,metadata"
    assert any("CREATE_SUPPLIER" in line for line in lines[1:])

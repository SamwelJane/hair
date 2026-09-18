from tests.integration.conftest import checkout_payload


async def _register(client, email="customer@example.com") -> str:
    resp = await client.post("/auth/register", json={"name": "Cust", "email": email, "password": "supersecret1"})
    assert resp.status_code == 201
    return resp.json()["access_token"]


async def test_export_requires_auth(client):
    resp = await client.get("/account/export")
    assert resp.status_code == 401


async def test_export_includes_own_orders_addresses_reviews(client, checkout_fixtures):
    token = await _register(client)
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/orders",
        json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id),
        headers=headers,
    )
    await client.post(
        "/addresses",
        json={"full_name": "Cust", "line1": "1 Main St", "city": "Nairobi", "country_code": "KE", "phone": "+254700000000"},
        headers=headers,
    )

    resp = await client.get("/account/export", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-disposition"] == 'attachment; filename="my-hiar-business-data.json"'
    body = resp.json()
    assert body["user"]["email"] == "customer@example.com"
    assert len(body["orders"]) == 1
    assert len(body["orders"][0]["items"]) == 1
    assert len(body["orders"][0]["payments"]) == 1
    assert len(body["addresses"]) == 1
    assert body["reviews"] == []


async def test_deactivate_own_account_locks_out_subsequent_requests(client):
    token = await _register(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/account/deactivate", headers=headers)
    assert resp.status_code == 204

    me_resp = await client.get("/auth/me", headers=headers)
    assert me_resp.status_code == 401

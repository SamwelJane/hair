from tests.integration.conftest import checkout_payload


async def _login(client, email, password) -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def test_list_payments_requires_admin(client, checkout_fixtures):
    register_resp = await client.post(
        "/auth/register", json={"name": "Cust", "email": "cust-pay@example.com", "password": "supersecret1"}
    )
    token = register_resp.json()["access_token"]
    resp = await client.get("/admin/payments", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


async def test_list_payments_buckets_by_provider_and_status(client, admin_user, checkout_fixtures):
    token = await _login(client, admin_user.email, "adminpass1")
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/orders",
        json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id),
        headers=headers,
    )

    resp = await client.get("/admin/payments", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["pending_bank_transfers"]) == 1
    assert body["pending_bank_transfers"][0]["provider"] == "BANK_TRANSFER"
    assert body["mpesa_payments"] == []
    assert body["resolved_bank_transfers"] == []


async def test_confirmed_payment_moves_to_resolved_bucket(client, db, admin_user, checkout_fixtures):
    token = await _login(client, admin_user.email, "adminpass1")
    headers = {"Authorization": f"Bearer {token}"}

    order_number = (
        await client.post(
            "/orders",
            json=checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id),
            headers=headers,
        )
    ).json()["order_number"]

    payments_resp = await client.get("/admin/payments", headers=headers)
    payment_id = payments_resp.json()["pending_bank_transfers"][0]["id"]

    confirm_resp = await client.post("/payments/bank-transfer/confirm", json={"payment_id": payment_id}, headers=headers)
    assert confirm_resp.status_code == 200

    resp = await client.get("/admin/payments", headers=headers)
    body = resp.json()
    assert body["pending_bank_transfers"] == []
    assert len(body["resolved_bank_transfers"]) == 1
    assert body["resolved_bank_transfers"][0]["confirmed_by_name"] == admin_user.name
    assert body["resolved_bank_transfers"][0]["order_number"] == order_number

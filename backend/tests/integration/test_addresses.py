async def _register(client, email="customer@example.com") -> str:
    resp = await client.post("/auth/register", json={"name": "Cust", "email": email, "password": "supersecret1"})
    assert resp.status_code == 201
    return resp.json()["access_token"]


def _address_payload(**overrides) -> dict:
    payload = {
        "label": "Home",
        "full_name": "Jane Doe",
        "line1": "123 Main St",
        "city": "Nairobi",
        "country_code": "KE",
        "phone": "+254700000000",
        "is_default": False,
    }
    payload.update(overrides)
    return payload


async def test_addresses_require_auth(client):
    resp = await client.get("/addresses")
    assert resp.status_code == 401


async def test_create_and_list_addresses(client):
    headers = {"Authorization": f"Bearer {await _register(client)}"}

    resp = await client.post("/addresses", json=_address_payload(), headers=headers)
    assert resp.status_code == 201
    assert resp.json()["is_default"] is False

    list_resp = await client.get("/addresses", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


async def test_creating_default_address_unsets_previous_default(client):
    headers = {"Authorization": f"Bearer {await _register(client)}"}

    first = await client.post("/addresses", json=_address_payload(label="Home", is_default=True), headers=headers)
    second = await client.post("/addresses", json=_address_payload(label="Office", is_default=True), headers=headers)
    assert first.status_code == 201
    assert second.status_code == 201

    addresses = (await client.get("/addresses", headers=headers)).json()
    defaults = [a for a in addresses if a["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["label"] == "Office"


async def test_set_default_address(client):
    headers = {"Authorization": f"Bearer {await _register(client)}"}
    first = (await client.post("/addresses", json=_address_payload(label="Home"), headers=headers)).json()
    (await client.post("/addresses", json=_address_payload(label="Office", is_default=True), headers=headers)).json()

    resp = await client.post(f"/addresses/{first['id']}/set-default", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["is_default"] is True

    addresses = (await client.get("/addresses", headers=headers)).json()
    defaults = [a for a in addresses if a["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["id"] == first["id"]


async def test_delete_own_address(client):
    headers = {"Authorization": f"Bearer {await _register(client)}"}
    created = (await client.post("/addresses", json=_address_payload(), headers=headers)).json()

    resp = await client.delete(f"/addresses/{created['id']}", headers=headers)
    assert resp.status_code == 204
    assert (await client.get("/addresses", headers=headers)).json() == []


async def test_cannot_delete_or_set_default_on_someone_elses_address(client):
    owner_headers = {"Authorization": f"Bearer {await _register(client, email='owner@example.com')}"}
    created = (await client.post("/addresses", json=_address_payload(), headers=owner_headers)).json()

    intruder_headers = {"Authorization": f"Bearer {await _register(client, email='intruder@example.com')}"}
    delete_resp = await client.delete(f"/addresses/{created['id']}", headers=intruder_headers)
    assert delete_resp.status_code == 404

    set_default_resp = await client.post(f"/addresses/{created['id']}/set-default", headers=intruder_headers)
    assert set_default_resp.status_code == 404

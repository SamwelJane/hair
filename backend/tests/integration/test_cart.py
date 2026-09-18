async def test_get_cart_creates_empty_guest_cart_and_returns_token_header(client, checkout_fixtures):
    resp = await client.get("/cart")
    assert resp.status_code == 200
    assert resp.json()["items"] == []
    assert resp.headers.get("x-guest-cart-token")


async def test_add_item_persists_and_shows_in_subsequent_get(client, checkout_fixtures):
    product, variant = checkout_fixtures["product"], checkout_fixtures["variant"]

    add_resp = await client.post(
        "/cart/items", json={"product_id": str(product.id), "variant_id": str(variant.id), "quantity": 2}
    )
    assert add_resp.status_code == 201
    guest_token = add_resp.headers["x-guest-cart-token"]
    assert len(add_resp.json()["items"]) == 1
    assert add_resp.json()["items"][0]["quantity"] == 2

    get_resp = await client.get("/cart", headers={"X-Guest-Cart-Token": guest_token})
    assert get_resp.status_code == 200
    assert len(get_resp.json()["items"]) == 1
    assert get_resp.json()["items"][0]["unit_price_usd"] == "120.00"


async def test_adding_same_product_variant_twice_merges_quantity(client, checkout_fixtures):
    product, variant = checkout_fixtures["product"], checkout_fixtures["variant"]
    body = {"product_id": str(product.id), "variant_id": str(variant.id), "quantity": 1}

    first = await client.post("/cart/items", json=body)
    guest_token = first.headers["x-guest-cart-token"]
    second = await client.post("/cart/items", json=body, headers={"X-Guest-Cart-Token": guest_token})

    assert len(second.json()["items"]) == 1
    assert second.json()["items"][0]["quantity"] == 2


async def test_update_item_quantity(client, checkout_fixtures):
    product, variant = checkout_fixtures["product"], checkout_fixtures["variant"]
    add_resp = await client.post(
        "/cart/items", json={"product_id": str(product.id), "variant_id": str(variant.id), "quantity": 1}
    )
    guest_token = add_resp.headers["x-guest-cart-token"]
    item_id = add_resp.json()["items"][0]["id"]

    patch_resp = await client.patch(
        f"/cart/items/{item_id}", json={"quantity": 5}, headers={"X-Guest-Cart-Token": guest_token}
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["items"][0]["quantity"] == 5


async def test_remove_item(client, checkout_fixtures):
    product, variant = checkout_fixtures["product"], checkout_fixtures["variant"]
    add_resp = await client.post(
        "/cart/items", json={"product_id": str(product.id), "variant_id": str(variant.id), "quantity": 1}
    )
    guest_token = add_resp.headers["x-guest-cart-token"]
    item_id = add_resp.json()["items"][0]["id"]

    delete_resp = await client.delete(f"/cart/items/{item_id}", headers={"X-Guest-Cart-Token": guest_token})
    assert delete_resp.status_code == 200
    assert delete_resp.json()["items"] == []


async def test_merge_guest_cart_into_user_cart_on_login(client, checkout_fixtures):
    product, variant = checkout_fixtures["product"], checkout_fixtures["variant"]

    add_resp = await client.post(
        "/cart/items", json={"product_id": str(product.id), "variant_id": str(variant.id), "quantity": 3}
    )
    guest_token = add_resp.headers["x-guest-cart-token"]

    register_resp = await client.post(
        "/auth/register", json={"name": "Cart User", "email": "cartuser@example.com", "password": "supersecret1"}
    )
    access_token = register_resp.json()["access_token"]

    merge_resp = await client.post(
        "/cart/merge", json={"guest_token": guest_token}, headers={"Authorization": f"Bearer {access_token}"}
    )
    assert merge_resp.status_code == 200
    assert len(merge_resp.json()["items"]) == 1
    assert merge_resp.json()["items"][0]["quantity"] == 3

    # The now-authenticated user's cart persists without needing the guest token anymore.
    get_resp = await client.get("/cart", headers={"Authorization": f"Bearer {access_token}"})
    assert len(get_resp.json()["items"]) == 1


async def test_merge_requires_authentication(client, checkout_fixtures):
    resp = await client.post("/cart/merge", json={"guest_token": "whatever"})
    assert resp.status_code == 401

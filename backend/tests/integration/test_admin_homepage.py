from app.routers.admin import homepage as admin_homepage_router


async def _login_admin(client, admin_user) -> str:
    resp = await client.post("/auth/login", json={"email": admin_user.email, "password": "adminpass1"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _register_customer(client) -> str:
    resp = await client.post("/auth/register", json={"name": "Cust", "email": "cust-homepage@example.com", "password": "supersecret1"})
    assert resp.status_code == 201
    return resp.json()["access_token"]


async def test_non_admin_cannot_manage_banners(client):
    token = await _register_customer(client)
    resp = await client.post(
        "/admin/homepage/banners", json={"headline": "Sale"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403


async def test_create_update_and_delete_banner(client, admin_user):
    headers = {"Authorization": f"Bearer {await _login_admin(client, admin_user)}"}

    create_resp = await client.post(
        "/admin/homepage/banners",
        json={"headline": "Grand Opening", "subheadline": "Welcome", "sort_order": 1, "is_active": True},
        headers=headers,
    )
    assert create_resp.status_code == 201
    banner = create_resp.json()
    assert banner["headline"] == "Grand Opening"
    assert banner["image_url"] is None

    update_resp = await client.patch(
        f"/admin/homepage/banners/{banner['id']}",
        json={"headline": "Updated Headline", "sort_order": 2, "is_active": False},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["headline"] == "Updated Headline"
    assert update_resp.json()["is_active"] is False

    delete_resp = await client.delete(f"/admin/homepage/banners/{banner['id']}", headers=headers)
    assert delete_resp.status_code == 204

    list_resp = await client.get("/admin/homepage/banners", headers=headers)
    assert list_resp.json() == []


async def test_upload_banner_image(client, admin_user, monkeypatch):
    monkeypatch.setattr(
        admin_homepage_router, "upload_image", lambda file_bytes, folder="x": ("https://img/banner.jpg", "public123")
    )
    headers = {"Authorization": f"Bearer {await _login_admin(client, admin_user)}"}

    banner_id = (
        await client.post("/admin/homepage/banners", json={"headline": "Sale"}, headers=headers)
    ).json()["id"]

    resp = await client.post(
        f"/admin/homepage/banners/{banner_id}/image", files={"file": ("banner.jpg", b"fake-bytes", "image/jpeg")},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["image_url"] == "https://img/banner.jpg"


async def test_uploading_image_for_unknown_banner_returns_404(client, admin_user, monkeypatch):
    monkeypatch.setattr(
        admin_homepage_router, "upload_image", lambda file_bytes, folder="x": ("https://img/banner.jpg", "public123")
    )
    headers = {"Authorization": f"Bearer {await _login_admin(client, admin_user)}"}
    resp = await client.post(
        "/admin/homepage/banners/00000000-0000-0000-0000-000000000000/image",
        files={"file": ("banner.jpg", b"fake-bytes", "image/jpeg")},
        headers=headers,
    )
    assert resp.status_code == 404


async def test_create_featured_placement_and_list(client, admin_user, checkout_fixtures):
    headers = {"Authorization": f"Bearer {await _login_admin(client, admin_user)}"}
    product = checkout_fixtures["product"]

    resp = await client.post(
        "/admin/homepage/product-placements",
        json={"product_id": str(product.id), "section": "FEATURED", "sort_order": 0, "is_active": True},
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["product_slug"] == product.slug
    assert body["section"] == "FEATURED"
    assert body["sale_price_usd"] is None

    list_resp = await client.get("/admin/homepage/product-placements", headers=headers)
    assert len(list_resp.json()) == 1


async def test_create_deal_placement_with_sale_price_and_update_it(client, admin_user, checkout_fixtures):
    headers = {"Authorization": f"Bearer {await _login_admin(client, admin_user)}"}
    product = checkout_fixtures["product"]

    create_resp = await client.post(
        "/admin/homepage/product-placements",
        json={
            "product_id": str(product.id), "section": "DEAL", "sale_price_usd": "45.00",
            "ends_at": "2099-01-01T00:00:00Z", "sort_order": 0, "is_active": True,
        },
        headers=headers,
    )
    assert create_resp.status_code == 201
    placement_id = create_resp.json()["id"]
    assert create_resp.json()["sale_price_usd"] == "45.00"

    update_resp = await client.patch(
        f"/admin/homepage/product-placements/{placement_id}",
        json={"section": "DEAL", "sale_price_usd": "39.99", "sort_order": 0, "is_active": True},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["sale_price_usd"] == "39.99"

    delete_resp = await client.delete(f"/admin/homepage/product-placements/{placement_id}", headers=headers)
    assert delete_resp.status_code == 204


async def test_update_unknown_placement_returns_404(client, admin_user):
    headers = {"Authorization": f"Bearer {await _login_admin(client, admin_user)}"}
    resp = await client.patch(
        "/admin/homepage/product-placements/00000000-0000-0000-0000-000000000000",
        json={"section": "FEATURED", "sort_order": 0, "is_active": True},
        headers=headers,
    )
    assert resp.status_code == 404

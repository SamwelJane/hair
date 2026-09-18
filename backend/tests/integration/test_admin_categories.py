from app.routers.admin import categories as admin_categories_router


async def _login_admin(client, admin_user) -> str:
    resp = await client.post("/auth/login", json={"email": admin_user.email, "password": "adminpass1"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def test_create_and_list_categories(client, admin_user):
    headers = {"Authorization": f"Bearer {await _login_admin(client, admin_user)}"}
    resp = await client.post("/admin/categories", json={"name": "Closures"}, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["slug"] == "closures"
    assert resp.json()["is_featured"] is False

    list_resp = await client.get("/admin/categories", headers=headers)
    assert any(c["name"] == "Closures" for c in list_resp.json())


async def test_update_category_sets_featured_and_sort_order(client, admin_user, checkout_fixtures):
    headers = {"Authorization": f"Bearer {await _login_admin(client, admin_user)}"}
    category = checkout_fixtures["category"]

    resp = await client.patch(
        f"/admin/categories/{category.id}",
        json={"name": category.name, "is_featured": True, "sort_order": 5},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_featured"] is True
    assert body["sort_order"] == 5


async def test_update_unknown_category_returns_404(client, admin_user):
    headers = {"Authorization": f"Bearer {await _login_admin(client, admin_user)}"}
    resp = await client.patch(
        "/admin/categories/00000000-0000-0000-0000-000000000000",
        json={"name": "x", "is_featured": False, "sort_order": 0},
        headers=headers,
    )
    assert resp.status_code == 404


async def test_upload_category_image(client, admin_user, checkout_fixtures, monkeypatch):
    monkeypatch.setattr(
        admin_categories_router.categories_service, "upload_image",
        lambda file_bytes, folder="x": ("https://img/category.jpg", "public123"),
    )
    headers = {"Authorization": f"Bearer {await _login_admin(client, admin_user)}"}
    category = checkout_fixtures["category"]

    resp = await client.post(
        f"/admin/categories/{category.id}/image", files={"file": ("cat.jpg", b"fake-bytes", "image/jpeg")},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["image_url"] == "https://img/category.jpg"

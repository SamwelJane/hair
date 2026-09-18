from sqlalchemy import select

from app.models.catalog import Category, ProductImage
from app.services import products as products_service


async def _login_admin(client, admin_user) -> str:
    resp = await client.post("/auth/login", json={"email": admin_user.email, "password": "adminpass1"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _product_payload(category_id, supplier_id, **overrides) -> dict:
    payload = {
        "name": "Curly Bundle 18in",
        "category_id": str(category_id),
        "supplier_id": str(supplier_id),
        "description": "A curly bundle.",
        "country_of_origin": "KE",
        "base_price_usd": "80.00",
        "hair_category": "BULK_HAIR",
    }
    payload.update(overrides)
    return payload


async def test_create_product_slugifies_name_and_defaults_to_published(client, admin_user, checkout_fixtures):
    token = await _login_admin(client, admin_user)
    payload = _product_payload(checkout_fixtures["category"].id, checkout_fixtures["supplier"].id)

    resp = await client.post("/admin/products", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["slug"] == "curly-bundle-18in"
    assert body["status"] == "published"
    assert body["variants"] == []
    assert body["images"] == []


async def test_non_admin_cannot_create_product(client, checkout_fixtures):
    register_resp = await client.post(
        "/auth/register", json={"name": "Cust", "email": "custp@example.com", "password": "supersecret1"}
    )
    token = register_resp.json()["access_token"]
    payload = _product_payload(checkout_fixtures["category"].id, checkout_fixtures["supplier"].id)
    resp = await client.post("/admin/products", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


async def test_update_product_changes_fields(client, db, admin_user, checkout_fixtures):
    token = await _login_admin(client, admin_user)
    product = checkout_fixtures["product"]

    payload = _product_payload(
        checkout_fixtures["category"].id, checkout_fixtures["supplier"].id, name="Renamed Wig", status="draft"
    )
    resp = await client.patch(
        f"/admin/products/{product.id}", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed Wig"
    assert resp.json()["status"] == "draft"

    await db.refresh(product)
    assert product.name == "Renamed Wig"


async def test_variant_crud_lifecycle(client, admin_user, checkout_fixtures):
    token = await _login_admin(client, admin_user)
    product = checkout_fixtures["product"]
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post(
        f"/admin/products/{product.id}/variants",
        json={"sku": "CB-18-BLK", "length": "18 inches", "price_delta_usd": "5.00", "stock_qty": 10},
        headers=headers,
    )
    assert create_resp.status_code == 201
    variants = create_resp.json()["variants"]
    new_variant = next(v for v in variants if v["sku"] == "CB-18-BLK")
    assert new_variant["length_inches"] == 18

    update_resp = await client.patch(
        f"/admin/products/{product.id}/variants/{new_variant['id']}",
        json={"sku": "CB-18-BLK", "stock_qty": 3},
        headers=headers,
    )
    assert update_resp.status_code == 200
    updated_variant = next(v for v in update_resp.json()["variants"] if v["id"] == new_variant["id"])
    assert updated_variant["stock_qty"] == 3

    delete_resp = await client.delete(
        f"/admin/products/{product.id}/variants/{new_variant['id']}", headers=headers
    )
    assert delete_resp.status_code == 200
    assert all(v["id"] != new_variant["id"] for v in delete_resp.json()["variants"])


async def test_upload_and_delete_product_image(client, db, admin_user, checkout_fixtures, monkeypatch):
    monkeypatch.setattr(products_service, "upload_image", lambda file_bytes, folder="x": ("https://img/test.jpg", "public123"))
    monkeypatch.setattr(products_service, "delete_image", lambda public_id: None)

    token = await _login_admin(client, admin_user)
    product = checkout_fixtures["product"]
    headers = {"Authorization": f"Bearer {token}"}

    upload_resp = await client.post(
        f"/admin/products/{product.id}/images",
        files={"file": ("test.jpg", b"fake-image-bytes", "image/jpeg")},
        headers=headers,
    )
    assert upload_resp.status_code == 201
    images = upload_resp.json()["images"]
    assert len(images) == 1
    assert images[0]["url"] == "https://img/test.jpg"

    stored_image = (await db.execute(select(ProductImage).where(ProductImage.product_id == product.id))).scalar_one()
    assert stored_image.cloudinary_public_id == "public123"

    image_id = images[0]["id"]
    delete_resp = await client.delete(f"/admin/products/{product.id}/images/{image_id}", headers=headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["images"] == []


async def test_upload_image_rejects_beyond_max(client, admin_user, checkout_fixtures, monkeypatch):
    monkeypatch.setattr(products_service, "upload_image", lambda file_bytes, folder="x": ("https://img/x.jpg", "pub"))

    token = await _login_admin(client, admin_user)
    product = checkout_fixtures["product"]
    headers = {"Authorization": f"Bearer {token}"}

    for _ in range(3):
        resp = await client.post(
            f"/admin/products/{product.id}/images",
            files={"file": ("test.jpg", b"bytes", "image/jpeg")},
            headers=headers,
        )
        assert resp.status_code == 201

    over_limit_resp = await client.post(
        f"/admin/products/{product.id}/images",
        files={"file": ("test.jpg", b"bytes", "image/jpeg")},
        headers=headers,
    )
    assert over_limit_resp.status_code == 400


async def test_create_and_delete_category(client, admin_user):
    token = await _login_admin(client, admin_user)
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post("/admin/categories", json={"name": "Closures"}, headers=headers)
    assert create_resp.status_code == 201
    assert create_resp.json()["slug"] == "closures"

    category_id = create_resp.json()["id"]
    delete_resp = await client.delete(f"/admin/categories/{category_id}", headers=headers)
    assert delete_resp.status_code == 204


async def test_delete_category_in_use_by_product_rejected(client, admin_user, checkout_fixtures):
    token = await _login_admin(client, admin_user)
    resp = await client.delete(
        f"/admin/categories/{checkout_fixtures['category'].id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 409


async def test_delete_category_with_children_rejected(client, db, admin_user):
    token = await _login_admin(client, admin_user)
    headers = {"Authorization": f"Bearer {token}"}

    parent = Category(name="Parent Cat", slug="parent-cat")
    db.add(parent)
    await db.commit()
    await db.refresh(parent)

    child_resp = await client.post("/admin/categories", json={"name": "Child Cat"}, headers=headers)
    assert child_resp.status_code == 201

    from app.models.catalog import Category as CategoryModel

    child = (await db.execute(select(CategoryModel).where(CategoryModel.slug == "child-cat"))).scalar_one()
    child.parent_id = parent.id
    await db.commit()

    resp = await client.delete(f"/admin/categories/{parent.id}", headers=headers)
    assert resp.status_code == 409


async def test_list_products_filters_by_query_and_status(client, admin_user, checkout_fixtures):
    token = await _login_admin(client, admin_user)
    headers = {"Authorization": f"Bearer {token}"}
    payload = _product_payload(checkout_fixtures["category"].id, checkout_fixtures["supplier"].id, name="Draft Wig", status="draft")
    await client.post("/admin/products", json=payload, headers=headers)

    all_resp = await client.get("/admin/products", headers=headers)
    assert all_resp.status_code == 200
    assert all_resp.json()["total"] == 2

    published_resp = await client.get("/admin/products", params={"status": "published"}, headers=headers)
    assert published_resp.json()["total"] == 1
    assert published_resp.json()["items"][0]["variant_count"] == 1

    search_resp = await client.get("/admin/products", params={"q": "Draft"}, headers=headers)
    assert search_resp.json()["total"] == 1
    assert search_resp.json()["items"][0]["name"] == "Draft Wig"

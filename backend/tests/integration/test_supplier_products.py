from decimal import Decimal

from app.core.security import hash_password
from app.models.catalog import Supplier
from app.models.enums import UserRole
from app.models.identity import User
from app.services import products as products_service


async def _login(client, email, password) -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _link_supplier_login(db, supplier, *, email: str, password: str) -> User:
    user = User(email=email, name="Supplier User", password_hash=hash_password(password), role=UserRole.SUPPLIER)
    db.add(user)
    await db.flush()
    supplier.user_id = user.id
    await db.commit()
    await db.refresh(user)
    return user


async def _supplier_headers(client, db, supplier, *, email="supplier-a@example.com", password="supplierpass1") -> dict:
    await _link_supplier_login(db, supplier, email=email, password=password)
    token = await _login(client, email, password)
    return {"Authorization": f"Bearer {token}"}


def _product_payload(category_id, **overrides) -> dict:
    payload = {
        "name": "Curly Bundle 18in",
        "category_id": str(category_id),
        "description": "A curly bundle.",
        "base_price_usd": "80.00",
        "hair_category": "BULK_HAIR",
    }
    payload.update(overrides)
    return payload


async def test_supplier_can_create_product_scoped_to_own_supplier_and_country(client, db, checkout_fixtures):
    supplier = checkout_fixtures["supplier"]
    headers = await _supplier_headers(client, db, supplier)

    resp = await client.post(
        "/supplier/products", json=_product_payload(checkout_fixtures["category"].id), headers=headers
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["slug"] == "curly-bundle-18in"
    assert body["status"] == "published"
    assert body["country_of_origin"] == supplier.country
    assert "supplier_id" not in body


async def test_supplier_can_list_and_get_own_products_only(client, db, checkout_fixtures):
    supplier = checkout_fixtures["supplier"]
    headers = await _supplier_headers(client, db, supplier)

    list_resp = await client.get("/supplier/products", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    own_product = checkout_fixtures["product"]
    assert list_resp.json()[0]["id"] == str(own_product.id)

    get_resp = await client.get(f"/supplier/products/{own_product.id}", headers=headers)
    assert get_resp.status_code == 200


async def test_supplier_cannot_view_or_edit_another_suppliers_product(client, db, checkout_fixtures):
    other_supplier = Supplier(
        name="Supplier B", country="VN", email="supplier-b@example.com", whatsapp_number="+84900000000",
        default_margin_pct=Decimal(10),
    )
    db.add(other_supplier)
    await db.commit()
    headers = await _supplier_headers(client, db, other_supplier, email="supplier-b@example.com", password="supplierpass2")

    own_product = checkout_fixtures["product"]
    get_resp = await client.get(f"/supplier/products/{own_product.id}", headers=headers)
    assert get_resp.status_code == 404

    update_resp = await client.patch(
        f"/supplier/products/{own_product.id}",
        json=_product_payload(checkout_fixtures["category"].id),
        headers=headers,
    )
    assert update_resp.status_code == 404


async def test_supplier_update_preserves_country_of_origin_and_ownership(client, db, checkout_fixtures):
    supplier = checkout_fixtures["supplier"]
    headers = await _supplier_headers(client, db, supplier)
    product = checkout_fixtures["product"]

    resp = await client.patch(
        f"/supplier/products/{product.id}",
        json=_product_payload(checkout_fixtures["category"].id, name="Renamed Bundle", status="draft"),
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed Bundle"
    assert resp.json()["status"] == "draft"
    assert resp.json()["country_of_origin"] == supplier.country

    await db.refresh(product)
    assert product.supplier_id == supplier.id


async def test_supplier_variant_crud_scoped_to_own_product(client, db, checkout_fixtures):
    supplier = checkout_fixtures["supplier"]
    headers = await _supplier_headers(client, db, supplier)
    product = checkout_fixtures["product"]

    create_resp = await client.post(
        f"/supplier/products/{product.id}/variants",
        json={"sku": "CB-18-BLK", "length": "18 inches", "price_delta_usd": "5.00", "stock_qty": 10},
        headers=headers,
    )
    assert create_resp.status_code == 201
    new_variant = next(v for v in create_resp.json()["variants"] if v["sku"] == "CB-18-BLK")
    assert new_variant["length_inches"] == 18

    update_resp = await client.patch(
        f"/supplier/products/{product.id}/variants/{new_variant['id']}",
        json={"sku": "CB-18-BLK", "stock_qty": 3},
        headers=headers,
    )
    assert update_resp.status_code == 200
    updated = next(v for v in update_resp.json()["variants"] if v["id"] == new_variant["id"])
    assert updated["stock_qty"] == 3

    delete_resp = await client.delete(
        f"/supplier/products/{product.id}/variants/{new_variant['id']}", headers=headers
    )
    assert delete_resp.status_code == 200
    assert all(v["id"] != new_variant["id"] for v in delete_resp.json()["variants"])


async def test_supplier_cannot_touch_variant_on_another_suppliers_product(client, db, checkout_fixtures):
    other_supplier = Supplier(
        name="Supplier B", country="VN", email="supplier-b@example.com", whatsapp_number="+84900000000",
        default_margin_pct=Decimal(10),
    )
    db.add(other_supplier)
    await db.commit()
    headers = await _supplier_headers(client, db, other_supplier, email="supplier-b@example.com", password="supplierpass2")

    variant = checkout_fixtures["variant"]
    product = checkout_fixtures["product"]
    resp = await client.patch(
        f"/supplier/products/{product.id}/variants/{variant.id}",
        json={"sku": variant.sku, "stock_qty": 999},
        headers=headers,
    )
    assert resp.status_code == 404


async def test_supplier_upload_and_delete_product_image(client, db, checkout_fixtures, monkeypatch):
    monkeypatch.setattr(products_service, "upload_image", lambda file_bytes, folder="x": ("https://img/test.jpg", "public123"))
    monkeypatch.setattr(products_service, "delete_image", lambda public_id: None)

    supplier = checkout_fixtures["supplier"]
    headers = await _supplier_headers(client, db, supplier)
    product = checkout_fixtures["product"]

    upload_resp = await client.post(
        f"/supplier/products/{product.id}/images",
        files={"file": ("test.jpg", b"fake-image-bytes", "image/jpeg")},
        headers=headers,
    )
    assert upload_resp.status_code == 201
    images = upload_resp.json()["images"]
    assert len(images) == 1
    assert images[0]["url"] == "https://img/test.jpg"

    image_id = images[0]["id"]
    delete_resp = await client.delete(f"/supplier/products/{product.id}/images/{image_id}", headers=headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["images"] == []

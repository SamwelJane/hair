import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.catalog import Category, HairCategory, Product, ProductVariant, Supplier
from app.models.identity import User
from app.models.pricing import CountryShippingRule, ExchangeRate, PricingSetting


@pytest.fixture
async def admin_user(db: AsyncSession) -> User:
    from app.models.enums import UserRole

    user = User(email="admin@example.com", name="Admin", password_hash=hash_password("adminpass1"), role=UserRole.ADMIN)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def warehouse_user(db: AsyncSession) -> User:
    from app.models.enums import UserRole

    user = User(
        email="warehouse@example.com", name="Warehouse Staff", password_hash=hash_password("warehousepass1"),
        role=UserRole.WAREHOUSE,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def kenya_ops_user(db: AsyncSession) -> User:
    from app.models.enums import UserRole

    user = User(
        email="kenyaops@example.com", name="Kenya Ops Staff", password_hash=hash_password("kenyaopspass1"),
        role=UserRole.KENYA_OPS,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def vn_warehouse(db: AsyncSession):
    from app.models.enums import WarehouseType
    from app.models.warehouse import Warehouse

    warehouse = Warehouse(code="CHERUBIM-VN", name="Cherubim Express", type=WarehouseType.VN, country="VN")
    db.add(warehouse)
    await db.commit()
    await db.refresh(warehouse)
    return warehouse


@pytest.fixture
async def checkout_fixtures(db: AsyncSession, admin_user: User) -> dict:
    """Sets up the minimum catalog/pricing state a checkout needs: a
    category, a supplier with a margin, a published product with one
    variant in stock, a shipping rule for KE, global pricing settings, and a
    USD->KES exchange rate."""
    category = Category(name="Wigs", slug="wigs")
    supplier = Supplier(name="Supplier A", country="KE", email="supplier-a@example.com", whatsapp_number="+254700000000", default_margin_pct=Decimal(15))
    db.add_all([category, supplier])
    await db.flush()

    product = Product(
        name="Luxury Body Wave Wig",
        slug="luxury-body-wave-wig",
        category_id=category.id,
        supplier_id=supplier.id,
        description="A wig.",
        country_of_origin="KE",
        base_price_usd=Decimal("100.00"),
        base_weight_grams=300,
        hair_category=HairCategory.WIG,
        status="published",
    )
    db.add(product)
    await db.flush()

    variant = ProductVariant(product_id=product.id, sku="LBW-16-BLK", price_delta_usd=Decimal("20.00"), stock_qty=5)
    db.add(variant)

    shipping_rule = CountryShippingRule(
        country_code="KE",
        country_name="Kenya",
        base_fee_usd=Decimal("10.00"),
        per_kg_fee_usd=Decimal("5.00"),
        customs_rate_pct=Decimal(0),
        estimated_days_min=3,
        estimated_days_max=7,
    )
    db.add(shipping_rule)

    db.add(PricingSetting(id="global"))
    db.add(
        ExchangeRate(
            base_currency="USD",
            target_currency="KES",
            rate=Decimal("130.0000"),
            updated_by_id=admin_user.id,
        )
    )
    await db.commit()
    await db.refresh(product)
    await db.refresh(variant)

    return {"category": category, "supplier": supplier, "product": product, "variant": variant, "shipping_rule": shipping_rule}


def checkout_payload(product_id: uuid.UUID, variant_id: uuid.UUID, *, quantity: int = 1, email: str = "guest@example.com") -> dict:
    return {
        "items": [{"product_id": str(product_id), "variant_id": str(variant_id), "quantity": quantity}],
        "shipping_address": {
            "full_name": "Guest Buyer",
            "email": email,
            "line1": "123 Main St",
            "city": "Nairobi",
            "country_code": "KE",
            "phone": "+254711111111",
        },
        "payment_method": "BANK_TRANSFER",
    }

"""One-time local demo seed. Safe to re-run - checks for existing rows by
their natural key (email/slug/code) before inserting, so it never creates
duplicates.

Usage (from backend):
    .venv/Scripts/python.exe -m scripts.seed_demo_data
"""

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import async_session_factory
from app.models.catalog import Category, Product, ProductVariant, Supplier
from app.models.enums import (
    DiscountType,
    HairCategory,
    ProductStatus,
    ReviewStatus,
    UserRole,
)
from app.models.identity import User
from app.models.orders import Review
from app.models.pricing import CountryShippingRule, DiscountCode, ExchangeRate, PricingSetting

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "AdminPass123!"
STAFF_EMAIL = "staff@example.com"
STAFF_PASSWORD = "StaffPass123!"
SUPPLIER_LOGIN_EMAIL = "supplier@example.com"
SUPPLIER_PASSWORD = "SupplierPass123!"
WAREHOUSE_EMAIL = "warehouse@example.com"
WAREHOUSE_PASSWORD = "WarehousePass123!"
KENYA_OPS_EMAIL = "kenyaops@example.com"
KENYA_OPS_PASSWORD = "KenyaOpsPass123!"


async def get_or_create_user(db, *, email: str, name: str, role: UserRole, password: str) -> User:
    existing = await db.scalar(select(User).where(User.email == email))
    if existing:
        return existing
    user = User(email=email, name=name, role=role, password_hash=hash_password(password))
    db.add(user)
    await db.flush()
    return user


async def get_or_create_category(db, name: str, slug: str) -> Category:
    existing = await db.scalar(select(Category).where(Category.slug == slug))
    if existing:
        return existing
    category = Category(name=name, slug=slug)
    db.add(category)
    await db.flush()
    return category


async def get_or_create_product(db, *, slug: str, **fields: Any) -> tuple[Product, bool]:
    existing = await db.scalar(select(Product).where(Product.slug == slug))
    if existing:
        return existing, False
    product = Product(slug=slug, **fields)
    db.add(product)
    await db.flush()
    return product, True


async def main() -> None:
    async with async_session_factory() as db:
        admin = await get_or_create_user(db, email=ADMIN_EMAIL, name="Demo Admin", role=UserRole.ADMIN, password=ADMIN_PASSWORD)
        await get_or_create_user(db, email=STAFF_EMAIL, name="Demo Staff", role=UserRole.STAFF, password=STAFF_PASSWORD)
        await get_or_create_user(
            db, email=WAREHOUSE_EMAIL, name="Demo Vietnam Warehouse", role=UserRole.WAREHOUSE, password=WAREHOUSE_PASSWORD
        )
        await get_or_create_user(
            db, email=KENYA_OPS_EMAIL, name="Demo Kenya Ops", role=UserRole.KENYA_OPS, password=KENYA_OPS_PASSWORD
        )
        await db.commit()

        supplier = await db.scalar(select(Supplier).where(Supplier.email == SUPPLIER_LOGIN_EMAIL))
        if supplier is None:
            supplier_user = await get_or_create_user(
                db, email=SUPPLIER_LOGIN_EMAIL, name="Demo Supplier Co", role=UserRole.SUPPLIER, password=SUPPLIER_PASSWORD
            )
            supplier = Supplier(
                name="Luxe Hair Co", country="KE", email=SUPPLIER_LOGIN_EMAIL, whatsapp_number="+254700000001",
                default_margin_pct=Decimal("15.00"), user_id=supplier_user.id,
            )
            db.add(supplier)
            await db.flush()
        await db.commit()

        wigs = await get_or_create_category(db, "Wigs", "wigs")
        bundles = await get_or_create_category(db, "Bundles", "bundles")
        closures = await get_or_create_category(db, "Closures", "closures")
        await db.commit()

        products_spec: list[dict[str, Any]] = [
            {
                "slug": "luxury-body-wave-wig", "name": "Luxury Body Wave Wig", "category_id": wigs.id,
                "description": "A soft, bouncy body wave wig cut and styled from 100% virgin human hair.",
                "country_of_origin": "KE", "base_price_usd": Decimal("189.00"), "base_weight_grams": 320,
                "hair_category": HairCategory.WIG, "status": ProductStatus.PUBLISHED,
                "variants": [("LBW-16", "16 inches", Decimal("0.00"), 12), ("LBW-20", "20 inches", Decimal("35.00"), 6)],
            },
            {
                "slug": "straight-bundle-deal", "name": "Straight Bundle Deal (3pc)", "category_id": bundles.id,
                "description": "Three bundles of silky straight hair, double-wefted for extra durability.",
                "country_of_origin": "KE", "base_price_usd": Decimal("120.00"), "base_weight_grams": 280,
                "hair_category": HairCategory.BULK_HAIR, "status": ProductStatus.PUBLISHED,
                "variants": [("SBD-18", "18 inches", Decimal("0.00"), 20), ("SBD-22", "22 inches", Decimal("18.00"), 14)],
            },
            {
                "slug": "curly-hd-lace-closure", "name": "Curly HD Lace Closure", "category_id": closures.id,
                "description": "4x4 HD lace closure with natural-looking curls and a pre-plucked hairline.",
                "country_of_origin": "KE", "base_price_usd": Decimal("75.00"), "base_weight_grams": 90,
                "hair_category": HairCategory.CLOSURE, "status": ProductStatus.PUBLISHED,
                "variants": [("CHL-14", "14 inches", Decimal("0.00"), 25)],
            },
            {
                "slug": "deep-wave-frontal", "name": "Deep Wave 13x4 Frontal", "category_id": closures.id,
                "description": "Full-width deep wave frontal for a seamless, natural-looking install.",
                "country_of_origin": "KE", "base_price_usd": Decimal("140.00"), "base_weight_grams": 110,
                "hair_category": HairCategory.FRONTAL, "status": ProductStatus.PUBLISHED,
                "variants": [("DWF-16", "16 inches", Decimal("0.00"), 9)],
            },
            {
                "slug": "kinky-curly-extension-set", "name": "Kinky Curly Clip-In Set", "category_id": bundles.id,
                "description": "An 8-piece clip-in set matched to natural kinky-curly texture.",
                "country_of_origin": "KE", "base_price_usd": Decimal("95.00"), "base_weight_grams": 200,
                "hair_category": HairCategory.EXTENSION, "status": ProductStatus.PUBLISHED,
                "variants": [("KCS-16", "16 inches", Decimal("0.00"), 15)],
            },
        ]

        for spec in products_spec:
            variants = spec.pop("variants")
            product, created = await get_or_create_product(db, supplier_id=supplier.id, **spec)
            if created:
                for sku, length, price_delta, stock in variants:
                    db.add(ProductVariant(product_id=product.id, sku=sku, length=length, price_delta_usd=price_delta, stock_qty=stock))
        await db.commit()

        first_product = await db.scalar(select(Product).where(Product.slug == "luxury-body-wave-wig"))
        if first_product is not None:
            existing_review = await db.scalar(
                select(Review).where(Review.product_id == first_product.id, Review.user_id == admin.id)
            )
            if existing_review is None:
                db.add(
                    Review(
                        product_id=first_product.id, user_id=admin.id, rating=5,
                        body="Beautiful texture, arrived well packaged. Highly recommend!", status=ReviewStatus.APPROVED,
                    )
                )
                await db.commit()

        existing_rate = await db.scalar(
            select(ExchangeRate).where(ExchangeRate.base_currency == "USD", ExchangeRate.target_currency == "KES")
        )
        if existing_rate is None:
            db.add(ExchangeRate(base_currency="USD", target_currency="KES", rate=Decimal("130.0000"), updated_by_id=admin.id))

        existing_pricing = await db.get(PricingSetting, "global")
        if existing_pricing is None:
            db.add(PricingSetting(id="global"))
        await db.commit()

        for code, name, min_days, max_days in [("KE", "Kenya", 3, 7), ("US", "United States", 7, 14)]:
            existing_rule = await db.scalar(select(CountryShippingRule).where(CountryShippingRule.country_code == code))
            if existing_rule is None:
                db.add(
                    CountryShippingRule(
                        country_code=code, country_name=name, base_fee_usd=Decimal("10.00"),
                        per_kg_fee_usd=Decimal("5.00"), customs_rate_pct=Decimal("0.00"),
                        estimated_days_min=min_days, estimated_days_max=max_days,
                    )
                )
        await db.commit()

        existing_discount = await db.scalar(select(DiscountCode).where(DiscountCode.code == "WELCOME10"))
        if existing_discount is None:
            db.add(
                DiscountCode(
                    code="WELCOME10", type=DiscountType.PERCENT, value=Decimal("10.00"),
                    expires_at=datetime.now(UTC).date() + timedelta(days=365),
                )
            )
        await db.commit()

    print("Seed complete.\n")
    print("Admin login:      ", ADMIN_EMAIL, "/", ADMIN_PASSWORD)
    print("Staff login:      ", STAFF_EMAIL, "/", STAFF_PASSWORD)
    print("Supplier login:   ", SUPPLIER_LOGIN_EMAIL, "/", SUPPLIER_PASSWORD)
    print("VN Warehouse login:", WAREHOUSE_EMAIL, "/", WAREHOUSE_PASSWORD)
    print("Kenya Ops login:  ", KENYA_OPS_EMAIL, "/", KENYA_OPS_PASSWORD)
    print("Discount code:    WELCOME10 (10% off)")


if __name__ == "__main__":
    asyncio.run(main())

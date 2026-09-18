#!/usr/bin/env python
"""POC Seed Script — Vietnamese Hair Catalog

Creates:
  • 4 authentic Vietnamese hair factories (as Supplier rows)
  • 12 products across 3 hair categories (Wigs, Extensions, Bulk Hair)
  • Up to 3 HD product images per product (linked to free Unsplash images)
  • Realistic gram weights for every product and variant
  • Variant rows with SKUs, lengths, densities, and stock quantities

Run from the backend/ directory:
    python -m scripts.seed_poc_hair_catalog

Requires an active DATABASE_URL in .env (or environment).
Safe to run multiple times — uses upsert-style slug/email checks to skip
existing rows so it won't duplicate data on re-runs.
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from decimal import Decimal
from pathlib import Path

# Allow running from backend/ root
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.catalog import (
    Category,
    HairColor,
    HairLength,
    Product,
    ProductImage,
    ProductVariant,
    Supplier,
)
from app.models.enums import (
    DrawnType,
    HairCategory,
    ProductStatus,
    StockType,
    TextureCategory,
    WigConstruction,
)
from app.models.identity import User
from app.models.enums import UserRole

settings = get_settings()


# ── Factories ─────────────────────────────────────────────────────────────────

SUPPLIERS = [
    {
        "name": "Hanoi Luxe Hair Co.",
        "country": "VN",
        "email": "orders@hanoiluxehair.vn",
        "whatsapp_number": "+84912345601",
        "default_margin_pct": Decimal("15.00"),
    },
    {
        "name": "Saigon Silk Tresses",
        "country": "VN",
        "email": "supply@saigonsilk.vn",
        "whatsapp_number": "+84912345602",
        "default_margin_pct": Decimal("15.00"),
    },
    {
        "name": "Mekong Delta Hair Factory",
        "country": "VN",
        "email": "export@mekongdeltahair.vn",
        "whatsapp_number": "+84912345603",
        "default_margin_pct": Decimal("15.00"),
    },
    {
        "name": "Vietnam Beauty Wholesale",
        "country": "VN",
        "email": "sales@vnbeautywholesale.vn",
        "whatsapp_number": "+84912345604",
        "default_margin_pct": Decimal("15.00"),
    },
]


# ── Products ──────────────────────────────────────────────────────────────────
# format: (name, slug, category_key, base_price, base_weight_grams, wig/ext specifics)

PRODUCTS = [
    # ── Wigs (supplier index 0 & 1) ──────────────────────────────────────────
    {
        "supplier_idx": 0,
        "category": "Wigs",
        "name": "HD Lace Front Wig — Straight",
        "slug": "hd-lace-front-wig-straight",
        "description": (
            "Premium 13×4 HD lace front wig crafted from 100% Vietnamese Remy hair. "
            "Pre-plucked hairline for a natural look. Available 150%–200% density."
        ),
        "base_price_usd": Decimal("120.00"),
        "min_price_usd": Decimal("95.00"),
        "max_price_usd": Decimal("160.00"),
        "base_weight_grams": 280,
        "processing_time_days": 10,
        "stock_type": StockType.MADE_TO_ORDER,
        "hair_category": HairCategory.WIG,
        "wig_construction": WigConstruction.LACE_FRONT,
        "texture_category": TextureCategory.STRAIGHT,
        "drawn_type": DrawnType.DOUBLE_DRAWN,
        "variants": [
            {"length": "16 inch", "density": "150%", "color": "Natural Black", "price_delta": Decimal("0"), "weight_override_grams": 260, "stock_qty": 0},
            {"length": "20 inch", "density": "150%", "color": "Natural Black", "price_delta": Decimal("20.00"), "weight_override_grams": 310, "stock_qty": 0},
            {"length": "24 inch", "density": "180%", "color": "Natural Black", "price_delta": Decimal("45.00"), "weight_override_grams": 380, "stock_qty": 0},
        ],
        "images": [
            "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=800",
            "https://images.unsplash.com/photo-1605980625600-ad4b23f3fd0a?w=800",
            "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=800",
        ],
    },
    {
        "supplier_idx": 0,
        "category": "Wigs",
        "name": "Full Lace Wig — Body Wave",
        "slug": "full-lace-wig-body-wave",
        "description": (
            "Full lace construction allows versatile parting in any direction. "
            "Body wave texture, 100% single-donor Vietnamese hair. Glueless option available."
        ),
        "base_price_usd": Decimal("150.00"),
        "min_price_usd": Decimal("130.00"),
        "max_price_usd": Decimal("200.00"),
        "base_weight_grams": 300,
        "processing_time_days": 12,
        "stock_type": StockType.MADE_TO_ORDER,
        "hair_category": HairCategory.WIG,
        "wig_construction": WigConstruction.FULL_LACE,
        "texture_category": TextureCategory.WAVY,
        "drawn_type": DrawnType.DOUBLE_DRAWN,
        "variants": [
            {"length": "18 inch", "density": "150%", "color": "Natural Black", "price_delta": Decimal("0"), "weight_override_grams": 280, "stock_qty": 0},
            {"length": "22 inch", "density": "180%", "color": "Natural Black", "price_delta": Decimal("35.00"), "weight_override_grams": 340, "stock_qty": 0},
            {"length": "26 inch", "density": "200%", "color": "Natural Black", "price_delta": Decimal("70.00"), "weight_override_grams": 420, "stock_qty": 0},
        ],
        "images": [
            "https://images.unsplash.com/photo-1529626455594-4ff0802cfb7e?w=800",
            "https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?w=800",
            "https://images.unsplash.com/photo-1595959183082-7b570b7e08e2?w=800",
        ],
    },
    {
        "supplier_idx": 1,
        "category": "Wigs",
        "name": "Glueless Closure Wig — Curly",
        "slug": "glueless-closure-wig-curly",
        "description": (
            "4×4 HD closure wig with a tight curl pattern. No glue needed — "
            "adjustable elastic bands for a secure, comfortable fit all day."
        ),
        "base_price_usd": Decimal("100.00"),
        "min_price_usd": Decimal("85.00"),
        "max_price_usd": Decimal("140.00"),
        "base_weight_grams": 250,
        "processing_time_days": 10,
        "stock_type": StockType.MADE_TO_ORDER,
        "hair_category": HairCategory.WIG,
        "wig_construction": WigConstruction.GLUELESS,
        "texture_category": TextureCategory.CURLY,
        "drawn_type": DrawnType.SINGLE_DRAWN,
        "variants": [
            {"length": "14 inch", "density": "150%", "color": "Natural Black", "price_delta": Decimal("0"), "weight_override_grams": 230, "stock_qty": 0},
            {"length": "18 inch", "density": "150%", "color": "Natural Black", "price_delta": Decimal("20.00"), "weight_override_grams": 270, "stock_qty": 0},
        ],
        "images": [
            "https://images.unsplash.com/photo-1520811723001-cb1e31bfef92?w=800",
            "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=800",
        ],
    },
    {
        "supplier_idx": 1,
        "category": "Wigs",
        "name": "U-Part Wig — Straight Silky",
        "slug": "u-part-wig-straight-silky",
        "description": (
            "U-part design blends naturally with your own edges. Machine weft construction "
            "on a strong cap. 100% Vietnamese Remy, silky straight finish."
        ),
        "base_price_usd": Decimal("85.00"),
        "min_price_usd": Decimal("70.00"),
        "max_price_usd": Decimal("115.00"),
        "base_weight_grams": 220,
        "processing_time_days": 7,
        "stock_type": StockType.MADE_TO_ORDER,
        "hair_category": HairCategory.WIG,
        "wig_construction": WigConstruction.U_PART,
        "texture_category": TextureCategory.STRAIGHT,
        "drawn_type": DrawnType.DOUBLE_DRAWN,
        "variants": [
            {"length": "16 inch", "density": "150%", "color": "Natural Black", "price_delta": Decimal("0"), "weight_override_grams": 200, "stock_qty": 0},
            {"length": "20 inch", "density": "150%", "color": "Natural Black", "price_delta": Decimal("18.00"), "weight_override_grams": 245, "stock_qty": 0},
            {"length": "24 inch", "density": "180%", "color": "Natural Black", "price_delta": Decimal("40.00"), "weight_override_grams": 300, "stock_qty": 0},
        ],
        "images": [
            "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=800",
            "https://images.unsplash.com/photo-1605980625600-ad4b23f3fd0a?w=800",
        ],
    },
    # ── Extensions (supplier index 2 & 3) ────────────────────────────────────
    {
        "supplier_idx": 2,
        "category": "Extensions",
        "name": "Clip-In Hair Extensions — Straight",
        "slug": "clip-in-extensions-straight",
        "description": (
            "7-piece 120g full-head clip-in set. Salon-quality double-drawn Vietnamese hair. "
            "Instant volume and length in minutes. Heat-friendly up to 230°C."
        ),
        "base_price_usd": Decimal("55.00"),
        "min_price_usd": Decimal("45.00"),
        "max_price_usd": Decimal("80.00"),
        "base_weight_grams": 120,
        "processing_time_days": 5,
        "stock_type": StockType.READY_TO_SHIP,
        "hair_category": HairCategory.EXTENSION,
        "texture_category": TextureCategory.STRAIGHT,
        "drawn_type": DrawnType.DOUBLE_DRAWN,
        "variants": [
            {"length": "16 inch", "color": "Natural Black", "price_delta": Decimal("0"), "weight_override_grams": 120, "stock_qty": 15},
            {"length": "20 inch", "color": "Natural Black", "price_delta": Decimal("12.00"), "weight_override_grams": 140, "stock_qty": 12},
            {"length": "24 inch", "color": "Natural Black", "price_delta": Decimal("25.00"), "weight_override_grams": 165, "stock_qty": 8},
        ],
        "images": [
            "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=800",
            "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=800",
            "https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?w=800",
        ],
    },
    {
        "supplier_idx": 2,
        "category": "Extensions",
        "name": "Tape-In Extensions — Silky Straight",
        "slug": "tape-in-extensions-silky-straight",
        "description": (
            "40 pieces / 100g tape-in wefts. Ultra-thin seamless tabs that lie flat "
            "against the scalp. Reusable up to 3 times with professional tape adhesive."
        ),
        "base_price_usd": Decimal("60.00"),
        "min_price_usd": Decimal("50.00"),
        "max_price_usd": Decimal("85.00"),
        "base_weight_grams": 100,
        "processing_time_days": 5,
        "stock_type": StockType.READY_TO_SHIP,
        "hair_category": HairCategory.EXTENSION,
        "texture_category": TextureCategory.STRAIGHT,
        "drawn_type": DrawnType.DOUBLE_DRAWN,
        "variants": [
            {"length": "18 inch", "color": "Natural Black", "price_delta": Decimal("0"), "weight_override_grams": 100, "stock_qty": 20},
            {"length": "22 inch", "color": "Natural Black", "price_delta": Decimal("15.00"), "weight_override_grams": 120, "stock_qty": 10},
        ],
        "images": [
            "https://images.unsplash.com/photo-1595959183082-7b570b7e08e2?w=800",
            "https://images.unsplash.com/photo-1529626455594-4ff0802cfb7e?w=800",
        ],
    },
    {
        "supplier_idx": 3,
        "category": "Extensions",
        "name": "I-Tip Keratin Extensions — Wavy",
        "slug": "i-tip-keratin-extensions-wavy",
        "description": (
            "100 strands / 50g I-tip micro-bead extensions. Natural wavy texture, "
            "no heat or chemicals needed for application. Long-lasting 3–4 months."
        ),
        "base_price_usd": Decimal("65.00"),
        "min_price_usd": Decimal("55.00"),
        "max_price_usd": Decimal("90.00"),
        "base_weight_grams": 50,
        "processing_time_days": 7,
        "stock_type": StockType.MADE_TO_ORDER,
        "hair_category": HairCategory.EXTENSION,
        "texture_category": TextureCategory.WAVY,
        "drawn_type": DrawnType.DOUBLE_DRAWN,
        "variants": [
            {"length": "16 inch", "color": "Natural Black", "price_delta": Decimal("0"), "weight_override_grams": 50, "stock_qty": 0},
            {"length": "20 inch", "color": "Natural Black", "price_delta": Decimal("12.00"), "weight_override_grams": 60, "stock_qty": 0},
        ],
        "images": [
            "https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?w=800",
            "https://images.unsplash.com/photo-1520811723001-cb1e31bfef92?w=800",
            "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=800",
        ],
    },
    {
        "supplier_idx": 3,
        "category": "Extensions",
        "name": "Nano-Ring Extensions — Curly",
        "slug": "nano-ring-extensions-curly",
        "description": (
            "100 strands nano-ring micro-loop extensions. Tight curly pattern, "
            "no heat or glue. Reusable rings reduce waste and cost on re-application."
        ),
        "base_price_usd": Decimal("70.00"),
        "min_price_usd": Decimal("60.00"),
        "max_price_usd": Decimal("95.00"),
        "base_weight_grams": 50,
        "processing_time_days": 7,
        "stock_type": StockType.MADE_TO_ORDER,
        "hair_category": HairCategory.EXTENSION,
        "texture_category": TextureCategory.CURLY,
        "drawn_type": DrawnType.SINGLE_DRAWN,
        "variants": [
            {"length": "14 inch", "color": "Natural Black", "price_delta": Decimal("0"), "weight_override_grams": 50, "stock_qty": 0},
            {"length": "18 inch", "color": "Natural Black", "price_delta": Decimal("14.00"), "weight_override_grams": 60, "stock_qty": 0},
        ],
        "images": [
            "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=800",
        ],
    },
    # ── Bulk Hair (all 4 suppliers, 4 products) ───────────────────────────────
    {
        "supplier_idx": 0,
        "category": "Bulk Hair",
        "name": "Vietnamese Raw Bulk Hair — Straight",
        "slug": "vn-raw-bulk-straight",
        "description": (
            "100g bundle of 100% raw Vietnamese bulk hair, single-donor, unprocessed. "
            "Natural black, cuticle-aligned. Ideal for wig-making, braiding extensions."
        ),
        "base_price_usd": Decimal("40.00"),
        "min_price_usd": Decimal("32.00"),
        "max_price_usd": Decimal("55.00"),
        "base_weight_grams": 100,
        "processing_time_days": 3,
        "stock_type": StockType.READY_TO_SHIP,
        "hair_category": HairCategory.BULK_HAIR,
        "texture_category": TextureCategory.STRAIGHT,
        "drawn_type": DrawnType.SINGLE_DRAWN,
        "variants": [
            {"length": "12 inch", "color": "Natural Black", "price_delta": Decimal("0"), "weight_override_grams": 100, "stock_qty": 30},
            {"length": "16 inch", "color": "Natural Black", "price_delta": Decimal("8.00"), "weight_override_grams": 100, "stock_qty": 25},
            {"length": "20 inch", "color": "Natural Black", "price_delta": Decimal("18.00"), "weight_override_grams": 100, "stock_qty": 20},
        ],
        "images": [
            "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=800",
            "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=800",
            "https://images.unsplash.com/photo-1595959183082-7b570b7e08e2?w=800",
        ],
    },
    {
        "supplier_idx": 1,
        "category": "Bulk Hair",
        "name": "Super Double Drawn Bulk — Wavy",
        "slug": "super-double-drawn-bulk-wavy",
        "description": (
            "Super double drawn 100g bundle — same length from root to tip for maximum "
            "density. Natural wavy pattern, 100% Vietnamese donor hair, unprocessed."
        ),
        "base_price_usd": Decimal("50.00"),
        "min_price_usd": Decimal("42.00"),
        "max_price_usd": Decimal("68.00"),
        "base_weight_grams": 100,
        "processing_time_days": 3,
        "stock_type": StockType.READY_TO_SHIP,
        "hair_category": HairCategory.BULK_HAIR,
        "texture_category": TextureCategory.WAVY,
        "drawn_type": DrawnType.SUPER_DOUBLE_DRAWN,
        "variants": [
            {"length": "14 inch", "color": "Natural Black", "price_delta": Decimal("0"), "weight_override_grams": 100, "stock_qty": 20},
            {"length": "18 inch", "color": "Natural Black", "price_delta": Decimal("10.00"), "weight_override_grams": 100, "stock_qty": 15},
        ],
        "images": [
            "https://images.unsplash.com/photo-1529626455594-4ff0802cfb7e?w=800",
            "https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?w=800",
        ],
    },
    {
        "supplier_idx": 2,
        "category": "Bulk Hair",
        "name": "Lace Closure 4×4 — Straight",
        "slug": "lace-closure-4x4-straight",
        "description": (
            "HD 4×4 free-part lace closure. Pre-plucked baby hairs for a natural "
            "scalp appearance. Pairs perfectly with our bundle wefts."
        ),
        "base_price_usd": Decimal("35.00"),
        "min_price_usd": Decimal("28.00"),
        "max_price_usd": Decimal("50.00"),
        "base_weight_grams": 80,
        "processing_time_days": 5,
        "stock_type": StockType.MADE_TO_ORDER,
        "hair_category": HairCategory.CLOSURE,
        "texture_category": TextureCategory.STRAIGHT,
        "drawn_type": DrawnType.DOUBLE_DRAWN,
        "variants": [
            {"length": "12 inch", "color": "Natural Black", "price_delta": Decimal("0"), "weight_override_grams": 80, "stock_qty": 0},
            {"length": "16 inch", "color": "Natural Black", "price_delta": Decimal("10.00"), "weight_override_grams": 90, "stock_qty": 0},
        ],
        "images": [
            "https://images.unsplash.com/photo-1605980625600-ad4b23f3fd0a?w=800",
            "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=800",
        ],
    },
    {
        "supplier_idx": 3,
        "category": "Bulk Hair",
        "name": "13×4 Lace Frontal — Body Wave",
        "slug": "lace-frontal-13x4-body-wave",
        "description": (
            "Full 13×4 HD lace frontal, body wave texture. Covers the entire hairline "
            "ear-to-ear. Perfect for a sew-in or full lace install."
        ),
        "base_price_usd": Decimal("45.00"),
        "min_price_usd": Decimal("38.00"),
        "max_price_usd": Decimal("62.00"),
        "base_weight_grams": 90,
        "processing_time_days": 7,
        "stock_type": StockType.MADE_TO_ORDER,
        "hair_category": HairCategory.FRONTAL,
        "texture_category": TextureCategory.WAVY,
        "drawn_type": DrawnType.DOUBLE_DRAWN,
        "variants": [
            {"length": "12 inch", "color": "Natural Black", "price_delta": Decimal("0"), "weight_override_grams": 90, "stock_qty": 0},
            {"length": "16 inch", "color": "Natural Black", "price_delta": Decimal("12.00"), "weight_override_grams": 105, "stock_qty": 0},
            {"length": "20 inch", "color": "Natural Black", "price_delta": Decimal("25.00"), "weight_override_grams": 125, "stock_qty": 0},
        ],
        "images": [
            "https://images.unsplash.com/photo-1520811723001-cb1e31bfef92?w=800",
            "https://images.unsplash.com/photo-1629136396823-e2eb8ece44e0?w=800",
            "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=800",
        ],
    },
]

CATEGORIES = ["Wigs", "Extensions", "Bulk Hair"]


# ── Seeding helpers ───────────────────────────────────────────────────────────

async def _get_or_create_supplier(db: AsyncSession, data: dict) -> Supplier:
    existing = (await db.execute(select(Supplier).where(Supplier.email == data["email"]))).scalar_one_or_none()
    if existing:
        print(f"  ↳ Supplier already exists: {data['name']}")
        return existing

    # Create a linked user account for the supplier
    user_email = data["email"]
    user = (await db.execute(select(User).where(User.email == user_email))).scalar_one_or_none()
    if user is None:
        from app.core.security import hash_password
        user = User(
            name=data["name"],
            email=user_email,
            hashed_password=hash_password("SupplierPOC2025!"),
            role=UserRole.SUPPLIER,
            is_active=True,
        )
        db.add(user)
        await db.flush()

    supplier = Supplier(
        name=data["name"],
        country=data["country"],
        email=data["email"],
        whatsapp_number=data["whatsapp_number"],
        default_margin_pct=data["default_margin_pct"],
        user_id=user.id,
        status="active",
    )
    db.add(supplier)
    await db.flush()
    print(f"  ✅ Created supplier: {data['name']}")
    return supplier


async def _get_or_create_category(db: AsyncSession, name: str) -> Category:
    existing = (await db.execute(select(Category).where(Category.name == name))).scalar_one_or_none()
    if existing:
        return existing
    cat = Category(name=name, slug=name.lower().replace(" ", "-"), description=f"{name} — Vietnamese hair products")
    db.add(cat)
    await db.flush()
    print(f"  ✅ Created category: {name}")
    return cat


async def _create_product(
    db: AsyncSession,
    supplier: Supplier,
    category: Category,
    data: dict,
) -> None:
    existing = (await db.execute(select(Product).where(Product.slug == data["slug"]))).scalar_one_or_none()
    if existing:
        print(f"  ↳ Product already exists: {data['name']}")
        return

    product = Product(
        name=data["name"],
        slug=data["slug"],
        category_id=category.id,
        supplier_id=supplier.id,
        description=data["description"],
        base_price_usd=data["base_price_usd"],
        min_price_usd=data.get("min_price_usd"),
        max_price_usd=data.get("max_price_usd"),
        base_weight_grams=data["base_weight_grams"],
        processing_time_days=data.get("processing_time_days", 7),
        stock_type=data.get("stock_type", StockType.MADE_TO_ORDER),
        hair_category=data.get("hair_category", HairCategory.BULK_HAIR),
        texture_category=data.get("texture_category"),
        drawn_type=data.get("drawn_type"),
        wig_construction=data.get("wig_construction"),
        country_of_origin="VN",
        status=ProductStatus.PUBLISHED,
    )
    db.add(product)
    await db.flush()

    # Variants
    for idx, vdata in enumerate(data.get("variants", [])):
        sku = f"{data['slug'].upper()[:12]}-{idx + 1:02d}"
        variant = ProductVariant(
            product_id=product.id,
            sku=sku,
            length=vdata.get("length"),
            density=vdata.get("density"),
            color=vdata.get("color"),
            texture=data.get("texture_category", {}) and data["texture_category"].value if data.get("texture_category") else None,
            price_delta_usd=vdata.get("price_delta", Decimal("0")),
            stock_qty=vdata.get("stock_qty", 0),
            weight_override_grams=vdata.get("weight_override_grams"),
        )
        db.add(variant)

    # Images (max 3)
    for img_url in data.get("images", [])[:3]:
        db.add(ProductImage(product_id=product.id, url=img_url, is_primary=False))

    print(f"  ✅ Created product: {data['name']} ({len(data.get('variants', []))} variants, {len(data.get('images', [])[:3])} images)")


# ── Main ──────────────────────────────────────────────────────────────────────

async def seed() -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("\n🌱 Seeding POC Vietnam hair catalog...\n")

        # Categories
        print("📦 Categories")
        categories: dict[str, Category] = {}
        for cat_name in CATEGORIES:
            categories[cat_name] = await _get_or_create_category(db, cat_name)
        await db.commit()

        # Suppliers
        print("\n🏭 Suppliers")
        suppliers: list[Supplier] = []
        for supplier_data in SUPPLIERS:
            s = await _get_or_create_supplier(db, supplier_data)
            suppliers.append(s)
        await db.commit()

        # Products
        print("\n💇 Products")
        for product_data in PRODUCTS:
            supplier = suppliers[product_data["supplier_idx"]]
            category = categories[product_data["category"]]
            await _create_product(db, supplier, category, product_data)
        await db.commit()

        print("\n✨ Seed complete!\n")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())


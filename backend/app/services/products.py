import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.integrations.cloudinary_client import MAX_PRODUCT_IMAGES, delete_image, upload_image
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
    AttachmentType,
    DrawnType,
    HairCategory,
    ProductStatus,
    TextureCategory,
    TipType,
    WigConstruction,
)
from app.services.audit import log_audit
from app.services.product_taxonomy import parse_length_inches, slugify


class ProductNotFoundError(Exception):
    pass


class VariantNotFoundError(Exception):
    pass


class TooManyImagesError(Exception):
    pass


class ProductInput:
    """Plain field bag shared by create/update - avoids two near-identical
    ~20-argument function signatures."""

    def __init__(
        self,
        *,
        name: str,
        category_id: uuid.UUID,
        supplier_id: uuid.UUID,
        description: str,
        country_of_origin: str,
        base_price_usd: Decimal,
        hair_category: HairCategory,
        hair_length: str | None = None,
        texture: str | None = None,
        color: str | None = None,
        quality: str | None = None,
        accessory_type: str | None = None,
        processing_time_days: int = 7,
        base_weight_grams: int = 200,
        status: ProductStatus = ProductStatus.PUBLISHED,
        drawn_type: DrawnType | None = None,
        texture_category: TextureCategory | None = None,
        attachment_type: AttachmentType | None = None,
        tip_type: TipType | None = None,
        wig_construction: WigConstruction | None = None,
        wig_cap_size: str | None = None,
        wig_features: list[str] | None = None,
    ) -> None:
        self.name = name
        self.category_id = category_id
        self.supplier_id = supplier_id
        self.description = description
        self.country_of_origin = country_of_origin
        self.base_price_usd = base_price_usd
        self.hair_category = hair_category
        self.hair_length = hair_length
        self.texture = texture
        self.color = color
        self.quality = quality
        self.accessory_type = accessory_type
        self.processing_time_days = processing_time_days
        self.base_weight_grams = base_weight_grams
        self.status = status
        self.drawn_type = drawn_type
        self.texture_category = texture_category
        self.attachment_type = attachment_type
        self.tip_type = tip_type
        self.wig_construction = wig_construction
        self.wig_cap_size = wig_cap_size
        self.wig_features = wig_features or []


async def list_products_admin(
    db: AsyncSession, *, q: str | None, status: ProductStatus | None, page: int, page_size: int
) -> tuple[list[Product], int]:
    """Admin product list - unlike the public catalog router, this is not
    filtered to PUBLISHED only (drafts must be visible/editable here), and
    exposes supplier/category by name for the admin table, matching the old
    app's src/app/admin/products/page.tsx."""
    stmt = select(Product).options(selectinload(Product.supplier), selectinload(Product.category), selectinload(Product.variants))
    count_stmt = select(func.count()).select_from(Product)

    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(Product.name.ilike(pattern))
        count_stmt = count_stmt.where(Product.name.ilike(pattern))
    if status is not None:
        stmt = stmt.where(Product.status == status)
        count_stmt = count_stmt.where(Product.status == status)

    total = await db.scalar(count_stmt) or 0
    stmt = stmt.order_by(Product.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    products = list((await db.execute(stmt)).scalars().all())
    return products, total


async def create_product(db: AsyncSession, data: ProductInput, *, actor_user_id: uuid.UUID) -> Product:
    product = Product(
        name=data.name,
        slug=slugify(data.name),
        category_id=data.category_id,
        supplier_id=data.supplier_id,
        description=data.description,
        hair_length=data.hair_length,
        texture=data.texture,
        color=data.color,
        quality=data.quality,
        accessory_type=data.accessory_type,
        country_of_origin=data.country_of_origin,
        processing_time_days=data.processing_time_days,
        base_price_usd=data.base_price_usd,
        base_weight_grams=data.base_weight_grams,
        status=data.status,
        hair_category=data.hair_category,
        drawn_type=data.drawn_type,
        texture_category=data.texture_category,
        attachment_type=data.attachment_type,
        tip_type=data.tip_type,
        wig_construction=data.wig_construction,
        wig_cap_size=data.wig_cap_size,
        wig_features=data.wig_features,
    )
    db.add(product)
    await db.flush()

    await log_audit(
        db, user_id=actor_user_id, action="CREATE_PRODUCT", entity_type="Product", entity_id=str(product.id),
        metadata={"name": product.name},
    )
    await db.commit()
    await db.refresh(product)
    return product


async def update_product(
    db: AsyncSession, product_id: uuid.UUID, data: ProductInput, *, actor_user_id: uuid.UUID
) -> Product:
    product = await db.get(Product, product_id)
    if product is None:
        raise ProductNotFoundError(f"Product {product_id} not found")

    product.name = data.name
    product.category_id = data.category_id
    product.supplier_id = data.supplier_id
    product.description = data.description
    product.hair_length = data.hair_length
    product.texture = data.texture
    product.color = data.color
    product.quality = data.quality
    product.accessory_type = data.accessory_type
    product.country_of_origin = data.country_of_origin
    product.processing_time_days = data.processing_time_days
    product.base_price_usd = data.base_price_usd
    product.base_weight_grams = data.base_weight_grams
    product.status = data.status
    product.hair_category = data.hair_category
    product.drawn_type = data.drawn_type
    product.texture_category = data.texture_category
    product.attachment_type = data.attachment_type
    product.tip_type = data.tip_type
    product.wig_construction = data.wig_construction
    product.wig_cap_size = data.wig_cap_size
    product.wig_features = data.wig_features

    await log_audit(
        db, user_id=actor_user_id, action="UPDATE_PRODUCT", entity_type="Product", entity_id=str(product_id),
        metadata={"name": data.name},
    )
    await db.commit()
    await db.refresh(product)
    return product


class VariantInput:
    def __init__(
        self,
        *,
        sku: str,
        length: str | None = None,
        density: str | None = None,
        texture: str | None = None,
        color: str | None = None,
        price_delta_usd: Decimal = Decimal(0),
        stock_qty: int = 0,
        weight_override_grams: int | None = None,
    ) -> None:
        self.sku = sku
        self.length = length
        self.density = density
        self.texture = texture
        self.color = color
        self.price_delta_usd = price_delta_usd
        self.stock_qty = stock_qty
        self.weight_override_grams = weight_override_grams


async def create_variant(
    db: AsyncSession, product_id: uuid.UUID, data: VariantInput, *, actor_user_id: uuid.UUID
) -> ProductVariant:
    variant = ProductVariant(
        product_id=product_id,
        sku=data.sku,
        length=data.length,
        length_inches=parse_length_inches(data.length),
        density=data.density,
        texture=data.texture,
        color=data.color,
        price_delta_usd=data.price_delta_usd,
        stock_qty=data.stock_qty,
        weight_override_grams=data.weight_override_grams,
    )
    db.add(variant)
    await db.flush()

    await log_audit(
        db, user_id=actor_user_id, action="CREATE_PRODUCT_VARIANT", entity_type="ProductVariant",
        entity_id=str(variant.id), metadata={"productId": str(product_id), "sku": variant.sku},
    )
    await db.commit()
    await db.refresh(variant)
    return variant


async def update_variant(
    db: AsyncSession, variant_id: uuid.UUID, data: VariantInput, *, actor_user_id: uuid.UUID
) -> ProductVariant:
    variant = await db.get(ProductVariant, variant_id)
    if variant is None:
        raise VariantNotFoundError(f"Variant {variant_id} not found")

    variant.length = data.length
    variant.length_inches = parse_length_inches(data.length)
    variant.density = data.density
    variant.texture = data.texture
    variant.color = data.color
    variant.price_delta_usd = data.price_delta_usd
    variant.stock_qty = data.stock_qty
    variant.weight_override_grams = data.weight_override_grams

    await log_audit(
        db, user_id=actor_user_id, action="UPDATE_PRODUCT_VARIANT", entity_type="ProductVariant",
        entity_id=str(variant_id), metadata={"productId": str(variant.product_id)},
    )
    await db.commit()
    await db.refresh(variant)
    return variant


async def delete_variant(db: AsyncSession, variant_id: uuid.UUID, *, actor_user_id: uuid.UUID) -> None:
    variant = await db.get(ProductVariant, variant_id)
    if variant is None:
        raise VariantNotFoundError(f"Variant {variant_id} not found")

    product_id = variant.product_id
    await db.delete(variant)
    await log_audit(
        db, user_id=actor_user_id, action="DELETE_PRODUCT_VARIANT", entity_type="ProductVariant",
        entity_id=str(variant_id), metadata={"productId": str(product_id)},
    )
    await db.commit()


async def upload_product_image(
    db: AsyncSession,
    product_id: uuid.UUID,
    file_bytes: bytes,
    *,
    variant_id: uuid.UUID | None,
    actor_user_id: uuid.UUID,
) -> ProductImage:
    existing_count = await db.scalar(
        select(func.count()).select_from(ProductImage).where(ProductImage.product_id == product_id)
    )
    if (existing_count or 0) >= MAX_PRODUCT_IMAGES:
        raise TooManyImagesError(
            f"Maximum of {MAX_PRODUCT_IMAGES} images per product. Remove one before uploading another."
        )

    url, public_id = upload_image(file_bytes)

    max_sort_order = await db.scalar(
        select(func.max(ProductImage.sort_order)).where(ProductImage.product_id == product_id)
    )
    image = ProductImage(
        product_id=product_id,
        variant_id=variant_id,
        url=url,
        cloudinary_public_id=public_id,
        sort_order=(max_sort_order if max_sort_order is not None else -1) + 1,
    )
    db.add(image)
    await db.flush()

    await log_audit(
        db, user_id=actor_user_id, action="UPLOAD_PRODUCT_IMAGE", entity_type="ProductImage",
        entity_id=str(image.id), metadata={"productId": str(product_id), "publicId": public_id},
    )
    await db.commit()
    await db.refresh(image)
    return image


async def delete_product_image(db: AsyncSession, image_id: uuid.UUID, *, actor_user_id: uuid.UUID) -> None:
    """New vs. the old app: also destroys the Cloudinary asset (wart #2 fix)
    - the old app only deleted the DB row, leaving the actual image
    orphaned in Cloudinary storage."""
    image = await db.get(ProductImage, image_id)
    if image is None:
        return

    product_id = image.product_id
    public_id = image.cloudinary_public_id
    await db.delete(image)
    await log_audit(
        db, user_id=actor_user_id, action="DELETE_PRODUCT_IMAGE", entity_type="ProductImage",
        entity_id=str(image_id), metadata={"productId": str(product_id)},
    )
    await db.commit()

    if public_id:
        delete_image(public_id)


async def list_taxonomy_reference_data(
    db: AsyncSession,
) -> tuple[list[Category], list[Supplier], list[HairColor], list[HairLength]]:
    categories = (await db.execute(select(Category).order_by(Category.name))).scalars().all()
    suppliers = (await db.execute(select(Supplier).order_by(Supplier.name))).scalars().all()
    colors = (await db.execute(select(HairColor).order_by(HairColor.sort_order))).scalars().all()
    lengths = (await db.execute(select(HairLength).order_by(HairLength.sort_order))).scalars().all()
    return list(categories), list(suppliers), list(colors), list(lengths)

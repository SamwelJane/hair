import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_supplier, get_db, require_supplier
from app.models.catalog import Product, Supplier
from app.models.identity import User
from app.schemas.supplier_products import (
    SupplierProductImageOut,
    SupplierProductOut,
    SupplierProductVariantOut,
    SupplierVariantRequest,
)
from app.schemas.supplier_products import SupplierProductRequest as ProductRequestSchema
from app.services import products as products_service

router = APIRouter(prefix="/supplier/products", tags=["supplier-products"], dependencies=[Depends(require_supplier)])


def _to_out(product: Product) -> SupplierProductOut:
    return SupplierProductOut(
        id=product.id,
        name=product.name,
        slug=product.slug,
        category_id=product.category_id,
        description=product.description,
        country_of_origin=product.country_of_origin,
        base_price_usd=product.base_price_usd,
        hair_category=product.hair_category,
        hair_length=product.hair_length,
        texture=product.texture,
        color=product.color,
        quality=product.quality,
        accessory_type=product.accessory_type,
        processing_time_days=product.processing_time_days,
        base_weight_grams=product.base_weight_grams,
        status=product.status,
        drawn_type=product.drawn_type,
        texture_category=product.texture_category,
        attachment_type=product.attachment_type,
        tip_type=product.tip_type,
        wig_construction=product.wig_construction,
        wig_cap_size=product.wig_cap_size,
        wig_features=product.wig_features,
        variants=[
            SupplierProductVariantOut(
                id=v.id, sku=v.sku, length=v.length, length_inches=v.length_inches, density=v.density,
                texture=v.texture, color=v.color, price_delta_usd=v.price_delta_usd, stock_qty=v.stock_qty,
                weight_override_grams=v.weight_override_grams,
            )
            for v in product.variants
        ],
        images=[
            SupplierProductImageOut(
                id=i.id, variant_id=i.variant_id, url=i.url, alt_text=i.alt_text, sort_order=i.sort_order
            )
            for i in product.images
        ],
    )


def _to_input(payload: ProductRequestSchema, *, supplier: Supplier, country_of_origin: str) -> products_service.ProductInput:
    # supplier_id and country_of_origin are never taken from the request body -
    # see SupplierProductRequest's docstring.
    return products_service.ProductInput(
        name=payload.name,
        category_id=payload.category_id,
        supplier_id=supplier.id,
        description=payload.description,
        country_of_origin=country_of_origin,
        base_price_usd=payload.base_price_usd,
        hair_category=payload.hair_category,
        hair_length=payload.hair_length,
        texture=payload.texture,
        color=payload.color,
        quality=payload.quality,
        accessory_type=payload.accessory_type,
        processing_time_days=payload.processing_time_days,
        base_weight_grams=payload.base_weight_grams,
        status=payload.status,
        drawn_type=payload.drawn_type,
        texture_category=payload.texture_category,
        attachment_type=payload.attachment_type,
        tip_type=payload.tip_type,
        wig_construction=payload.wig_construction,
        wig_cap_size=payload.wig_cap_size,
        wig_features=payload.wig_features,
    )


async def _load_own_product(db: AsyncSession, product_id: uuid.UUID, supplier_id: uuid.UUID) -> Product:
    """404 (not 403) whether the product doesn't exist or belongs to another
    supplier - collapsing both into one response, same as the old app's
    assertOwnsProduct, avoids confirming to a caller that a given product id
    exists at all."""
    product = await db.get(
        Product, product_id, populate_existing=True,
        options=[selectinload(Product.variants), selectinload(Product.images)],
    )
    if product is None or product.supplier_id != supplier_id:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("", response_model=list[SupplierProductOut])
async def list_my_products(
    db: AsyncSession = Depends(get_db),
    supplier: Supplier = Depends(get_current_supplier),
) -> list[SupplierProductOut]:
    products = (
        (
            await db.execute(
                select(Product)
                .where(Product.supplier_id == supplier.id)
                .options(selectinload(Product.variants), selectinload(Product.images))
                .order_by(Product.updated_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return [_to_out(p) for p in products]


@router.post("", response_model=SupplierProductOut, status_code=201)
async def create_my_product(
    payload: ProductRequestSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_supplier),
    supplier: Supplier = Depends(get_current_supplier),
) -> SupplierProductOut:
    product = await products_service.create_product(
        db, _to_input(payload, supplier=supplier, country_of_origin=supplier.country), actor_user_id=user.id
    )
    product = await _load_own_product(db, product.id, supplier.id)
    return _to_out(product)


@router.get("/{product_id}", response_model=SupplierProductOut)
async def get_my_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    supplier: Supplier = Depends(get_current_supplier),
) -> SupplierProductOut:
    product = await _load_own_product(db, product_id, supplier.id)
    return _to_out(product)


@router.patch("/{product_id}", response_model=SupplierProductOut)
async def update_my_product(
    product_id: uuid.UUID,
    payload: ProductRequestSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_supplier),
    supplier: Supplier = Depends(get_current_supplier),
) -> SupplierProductOut:
    existing = await _load_own_product(db, product_id, supplier.id)
    await products_service.update_product(
        db, product_id, _to_input(payload, supplier=supplier, country_of_origin=existing.country_of_origin),
        actor_user_id=user.id,
    )
    product = await _load_own_product(db, product_id, supplier.id)
    return _to_out(product)


@router.post("/{product_id}/variants", response_model=SupplierProductOut, status_code=201)
async def create_my_variant(
    product_id: uuid.UUID,
    payload: SupplierVariantRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_supplier),
    supplier: Supplier = Depends(get_current_supplier),
) -> SupplierProductOut:
    await _load_own_product(db, product_id, supplier.id)
    await products_service.create_variant(
        db, product_id,
        products_service.VariantInput(
            sku=payload.sku, length=payload.length, density=payload.density, texture=payload.texture,
            color=payload.color, price_delta_usd=payload.price_delta_usd, stock_qty=payload.stock_qty,
            weight_override_grams=payload.weight_override_grams,
        ),
        actor_user_id=user.id,
    )
    product = await _load_own_product(db, product_id, supplier.id)
    return _to_out(product)


@router.patch("/{product_id}/variants/{variant_id}", response_model=SupplierProductOut)
async def update_my_variant(
    product_id: uuid.UUID,
    variant_id: uuid.UUID,
    payload: SupplierVariantRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_supplier),
    supplier: Supplier = Depends(get_current_supplier),
) -> SupplierProductOut:
    product = await _load_own_product(db, product_id, supplier.id)
    if variant_id not in {v.id for v in product.variants}:
        raise HTTPException(status_code=404, detail="Variant not found")

    await products_service.update_variant(
        db, variant_id,
        products_service.VariantInput(
            sku=payload.sku, length=payload.length, density=payload.density, texture=payload.texture,
            color=payload.color, price_delta_usd=payload.price_delta_usd, stock_qty=payload.stock_qty,
            weight_override_grams=payload.weight_override_grams,
        ),
        actor_user_id=user.id,
    )
    product = await _load_own_product(db, product_id, supplier.id)
    return _to_out(product)


@router.delete("/{product_id}/variants/{variant_id}", response_model=SupplierProductOut)
async def delete_my_variant(
    product_id: uuid.UUID,
    variant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_supplier),
    supplier: Supplier = Depends(get_current_supplier),
) -> SupplierProductOut:
    product = await _load_own_product(db, product_id, supplier.id)
    if variant_id not in {v.id for v in product.variants}:
        raise HTTPException(status_code=404, detail="Variant not found")

    await products_service.delete_variant(db, variant_id, actor_user_id=user.id)
    product = await _load_own_product(db, product_id, supplier.id)
    return _to_out(product)


@router.post("/{product_id}/images", response_model=SupplierProductOut, status_code=201)
async def upload_my_image(
    product_id: uuid.UUID,
    file: UploadFile = File(...),
    variant_id: uuid.UUID | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_supplier),
    supplier: Supplier = Depends(get_current_supplier),
) -> SupplierProductOut:
    product = await _load_own_product(db, product_id, supplier.id)
    if variant_id is not None and variant_id not in {v.id for v in product.variants}:
        raise HTTPException(status_code=404, detail="Variant not found")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        await products_service.upload_product_image(
            db, product_id, file_bytes, variant_id=variant_id, actor_user_id=user.id
        )
    except products_service.TooManyImagesError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    product = await _load_own_product(db, product_id, supplier.id)
    return _to_out(product)


@router.delete("/{product_id}/images/{image_id}", response_model=SupplierProductOut)
async def delete_my_image(
    product_id: uuid.UUID,
    image_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_supplier),
    supplier: Supplier = Depends(get_current_supplier),
) -> SupplierProductOut:
    product = await _load_own_product(db, product_id, supplier.id)
    if image_id not in {i.id for i in product.images}:
        raise HTTPException(status_code=404, detail="Image not found")

    await products_service.delete_product_image(db, image_id, actor_user_id=user.id)
    product = await _load_own_product(db, product_id, supplier.id)
    return _to_out(product)

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_db, require_admin
from app.models.catalog import Product
from app.models.enums import ProductStatus
from app.models.identity import User
from app.schemas.admin_products import (
    AdminProductListItemOut,
    AdminProductListOut,
    ProductImageOut,
    ProductOut,
    ProductRequest,
    ProductVariantOut,
    VariantRequest,
)
from app.services import products as products_service

router = APIRouter(prefix="/admin/products", tags=["admin-products"], dependencies=[Depends(require_admin)])

PAGE_SIZE = 20


def _product_to_out(product: Product) -> ProductOut:
    return ProductOut(
        id=product.id,
        name=product.name,
        slug=product.slug,
        category_id=product.category_id,
        supplier_id=product.supplier_id,
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
            ProductVariantOut(
                id=v.id,
                sku=v.sku,
                length=v.length,
                length_inches=v.length_inches,
                density=v.density,
                texture=v.texture,
                color=v.color,
                price_delta_usd=v.price_delta_usd,
                stock_qty=v.stock_qty,
                weight_override_grams=v.weight_override_grams,
            )
            for v in product.variants
        ],
        images=[
            ProductImageOut(id=i.id, variant_id=i.variant_id, url=i.url, alt_text=i.alt_text, sort_order=i.sort_order)
            for i in product.images
        ],
    )


def _to_input(payload: ProductRequest) -> products_service.ProductInput:
    return products_service.ProductInput(
        name=payload.name,
        category_id=payload.category_id,
        supplier_id=payload.supplier_id,
        description=payload.description,
        country_of_origin=payload.country_of_origin,
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


async def _load_product(db: AsyncSession, product_id: uuid.UUID) -> Product:
    product = await db.get(
        Product,
        product_id,
        populate_existing=True,
        options=[selectinload(Product.variants), selectinload(Product.images)],
    )
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("", response_model=AdminProductListOut)
async def list_products(
    q: str | None = None,
    status: ProductStatus | None = None,
    page: int = Query(default=1, ge=1),
    db: AsyncSession = Depends(get_db),
) -> AdminProductListOut:
    products, total = await products_service.list_products_admin(db, q=q, status=status, page=page, page_size=PAGE_SIZE)
    return AdminProductListOut(
        items=[
            AdminProductListItemOut(
                id=p.id, name=p.name, category_name=p.category.name, supplier_name=p.supplier.name,
                base_price_usd=p.base_price_usd, variant_count=len(p.variants), status=p.status,
            )
            for p in products
        ],
        total=total,
        page=page,
        page_size=PAGE_SIZE,
    )


@router.post("", response_model=ProductOut, status_code=201)
async def create_product(
    payload: ProductRequest, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)
) -> ProductOut:
    product = await products_service.create_product(db, _to_input(payload), actor_user_id=admin.id)
    product = await _load_product(db, product.id)
    return _product_to_out(product)


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> ProductOut:
    product = await _load_product(db, product_id)
    return _product_to_out(product)


@router.patch("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: uuid.UUID,
    payload: ProductRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ProductOut:
    try:
        await products_service.update_product(db, product_id, _to_input(payload), actor_user_id=admin.id)
    except products_service.ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    product = await _load_product(db, product_id)
    return _product_to_out(product)


@router.post("/{product_id}/variants", response_model=ProductOut, status_code=201)
async def create_variant(
    product_id: uuid.UUID,
    payload: VariantRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ProductOut:
    await products_service.create_variant(
        db,
        product_id,
        products_service.VariantInput(
            sku=payload.sku,
            length=payload.length,
            density=payload.density,
            texture=payload.texture,
            color=payload.color,
            price_delta_usd=payload.price_delta_usd,
            stock_qty=payload.stock_qty,
            weight_override_grams=payload.weight_override_grams,
        ),
        actor_user_id=admin.id,
    )
    product = await _load_product(db, product_id)
    return _product_to_out(product)


@router.patch("/{product_id}/variants/{variant_id}", response_model=ProductOut)
async def update_variant(
    product_id: uuid.UUID,
    variant_id: uuid.UUID,
    payload: VariantRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ProductOut:
    try:
        await products_service.update_variant(
            db,
            variant_id,
            products_service.VariantInput(
                sku=payload.sku,
                length=payload.length,
                density=payload.density,
                texture=payload.texture,
                color=payload.color,
                price_delta_usd=payload.price_delta_usd,
                stock_qty=payload.stock_qty,
                weight_override_grams=payload.weight_override_grams,
            ),
            actor_user_id=admin.id,
        )
    except products_service.VariantNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    product = await _load_product(db, product_id)
    return _product_to_out(product)


@router.delete("/{product_id}/variants/{variant_id}", response_model=ProductOut)
async def delete_variant(
    product_id: uuid.UUID,
    variant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ProductOut:
    try:
        await products_service.delete_variant(db, variant_id, actor_user_id=admin.id)
    except products_service.VariantNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    product = await _load_product(db, product_id)
    return _product_to_out(product)


@router.post("/{product_id}/images", response_model=ProductOut, status_code=201)
async def upload_image(
    product_id: uuid.UUID,
    file: UploadFile = File(...),
    variant_id: uuid.UUID | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ProductOut:
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        await products_service.upload_product_image(
            db, product_id, file_bytes, variant_id=variant_id, actor_user_id=admin.id
        )
    except products_service.TooManyImagesError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    product = await _load_product(db, product_id)
    return _product_to_out(product)


@router.delete("/{product_id}/images/{image_id}", response_model=ProductOut)
async def delete_image(
    product_id: uuid.UUID,
    image_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ProductOut:
    await products_service.delete_product_image(db, image_id, actor_user_id=admin.id)
    product = await _load_product(db, product_id)
    return _product_to_out(product)

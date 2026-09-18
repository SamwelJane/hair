import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.cloudinary_client import upload_image
from app.models.catalog import Category, Product
from app.services.product_taxonomy import slugify


class CategoryInUseError(Exception):
    pass


class CategoryNotFoundError(Exception):
    pass


async def create_category(db: AsyncSession, name: str) -> Category:
    category = Category(name=name, slug=slugify(name))
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def delete_category(db: AsyncSession, category_id: uuid.UUID) -> None:
    """New vs. the old app: an explicit pre-check instead of relying on the
    FK constraint to fail (and swallowing that error, silently no-op'ing).
    Raises CategoryInUseError with a clear reason instead."""
    category = await db.get(Category, category_id)
    if category is None:
        return

    child_count = await db.scalar(select(func.count()).select_from(Category).where(Category.parent_id == category_id))
    if child_count:
        raise CategoryInUseError(f"Category has {child_count} child categor{'y' if child_count == 1 else 'ies'} - move or delete them first.")

    product_count = await db.scalar(select(func.count()).select_from(Product).where(Product.category_id == category_id))
    if product_count:
        raise CategoryInUseError(f"Category has {product_count} product(s) assigned - reassign them first.")

    await db.delete(category)
    await db.commit()


async def update_category(db: AsyncSession, category_id: uuid.UUID, *, name: str, is_featured: bool, sort_order: int) -> Category:
    category = await db.get(Category, category_id)
    if category is None:
        raise CategoryNotFoundError(f"Category {category_id} not found.")

    category.name = name
    category.is_featured = is_featured
    category.sort_order = sort_order

    await db.commit()
    await db.refresh(category)
    return category


async def upload_category_image(db: AsyncSession, category_id: uuid.UUID, file_bytes: bytes) -> Category:
    category = await db.get(Category, category_id)
    if category is None:
        raise CategoryNotFoundError(f"Category {category_id} not found.")

    url, public_id = upload_image(file_bytes, folder="hiar-business/categories")
    category.image_url = url
    category.cloudinary_public_id = public_id

    await db.commit()
    await db.refresh(category)
    return category

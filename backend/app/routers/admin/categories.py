import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_admin
from app.models.catalog import Category
from app.schemas.admin_products import CategoryOut, CategoryRequest, CategoryUpdateRequest
from app.services import categories as categories_service

router = APIRouter(prefix="/admin/categories", tags=["admin-categories"], dependencies=[Depends(require_admin)])


def _to_out(category: Category) -> CategoryOut:
    return CategoryOut(
        id=category.id, name=category.name, slug=category.slug, parent_id=category.parent_id,
        image_url=category.image_url, is_featured=category.is_featured, sort_order=category.sort_order,
    )


@router.get("", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)) -> list[CategoryOut]:
    categories = (await db.execute(select(Category).order_by(Category.name))).scalars().all()
    return [_to_out(c) for c in categories]


@router.post("", response_model=CategoryOut, status_code=201)
async def create_category(payload: CategoryRequest, db: AsyncSession = Depends(get_db)) -> CategoryOut:
    category = await categories_service.create_category(db, payload.name)
    return _to_out(category)


@router.patch("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: uuid.UUID, payload: CategoryUpdateRequest, db: AsyncSession = Depends(get_db)
) -> CategoryOut:
    try:
        category = await categories_service.update_category(
            db, category_id, name=payload.name, is_featured=payload.is_featured, sort_order=payload.sort_order
        )
    except categories_service.CategoryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_out(category)


@router.post("/{category_id}/image", response_model=CategoryOut, status_code=201)
async def upload_category_image(
    category_id: uuid.UUID, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
) -> CategoryOut:
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")
    try:
        category = await categories_service.upload_category_image(db, category_id, file_bytes)
    except categories_service.CategoryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_out(category)


@router.delete("/{category_id}", status_code=204)
async def delete_category(category_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    try:
        await categories_service.delete_category(db, category_id)
    except categories_service.CategoryInUseError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

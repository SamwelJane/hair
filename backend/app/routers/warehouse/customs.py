import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_permission
from app.models.consolidation import Consolidation
from app.models.customs import CustomsDeclaration
from app.models.identity import User
from app.schemas.customs import (
    CustomsDeclarationListOut,
    CustomsDeclarationOut,
    DeclareCustomsRequest,
    RaiseCustomsQueryRequest,
)
from app.services import customs as customs_service

router = APIRouter(prefix="/warehouse/customs-declarations", tags=["warehouse-customs"])

PAGE_SIZE = 20


async def _to_out(db: AsyncSession, declaration: CustomsDeclaration) -> CustomsDeclarationOut:
    consolidation_code = None
    if declaration.consolidation_id is not None:
        consolidation = await db.get(Consolidation, declaration.consolidation_id)
        consolidation_code = consolidation.consolidation_code if consolidation else None
    return CustomsDeclarationOut(
        id=declaration.id,
        consolidation_id=declaration.consolidation_id,
        package_id=declaration.package_id,
        consolidation_code=consolidation_code,
        hs_code=declaration.hs_code,
        declared_value_usd=declaration.declared_value_usd,
        duty_usd=declaration.duty_usd,
        vat_usd=declaration.vat_usd,
        status=declaration.status,
        notes=declaration.notes,
        created_at=declaration.created_at,
    )


@router.get("", response_model=CustomsDeclarationListOut)
async def list_declarations(
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("packages.read")),
) -> CustomsDeclarationListOut:
    stmt = select(CustomsDeclaration)
    count_stmt = select(func.count()).select_from(CustomsDeclaration)
    if status:
        stmt = stmt.where(CustomsDeclaration.status == status)
        count_stmt = count_stmt.where(CustomsDeclaration.status == status)
    stmt = stmt.order_by(CustomsDeclaration.created_at.desc()).limit(PAGE_SIZE).offset((page - 1) * PAGE_SIZE)

    declarations = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(count_stmt)).scalar_one()
    return CustomsDeclarationListOut(
        declarations=[await _to_out(db, d) for d in declarations], total=total, page=page, page_size=PAGE_SIZE
    )


@router.get("/{declaration_id}", response_model=CustomsDeclarationOut)
async def get_declaration(
    declaration_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("packages.read")),
) -> CustomsDeclarationOut:
    declaration = await db.get(CustomsDeclaration, declaration_id)
    if declaration is None:
        raise HTTPException(status_code=404, detail="Customs declaration not found")
    return await _to_out(db, declaration)


@router.post("/{declaration_id}/declare", response_model=CustomsDeclarationOut)
async def declare_customs(
    declaration_id: uuid.UUID,
    payload: DeclareCustomsRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("customs.update")),
) -> CustomsDeclarationOut:
    try:
        declaration = await customs_service.declare(
            db,
            declaration_id=declaration_id,
            hs_code=payload.hs_code,
            declared_value_usd=payload.declared_value_usd,
            duty_usd=payload.duty_usd,
            vat_usd=payload.vat_usd,
            actor_user_id=user.id,
        )
    except customs_service.CustomsDeclarationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except customs_service.InvalidCustomsTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await _to_out(db, declaration)


@router.post("/{declaration_id}/query", response_model=CustomsDeclarationOut)
async def query_customs(
    declaration_id: uuid.UUID,
    payload: RaiseCustomsQueryRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("customs.update")),
) -> CustomsDeclarationOut:
    try:
        declaration = await customs_service.raise_query(
            db, declaration_id=declaration_id, note=payload.note, actor_user_id=user.id
        )
    except customs_service.CustomsDeclarationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except customs_service.InvalidCustomsTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await _to_out(db, declaration)


@router.post("/{declaration_id}/clear", response_model=CustomsDeclarationOut)
async def clear_customs(
    declaration_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("customs.update")),
) -> CustomsDeclarationOut:
    try:
        declaration = await customs_service.clear(db, declaration_id=declaration_id, actor_user_id=user.id)
    except customs_service.CustomsDeclarationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except customs_service.InvalidCustomsTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await _to_out(db, declaration)

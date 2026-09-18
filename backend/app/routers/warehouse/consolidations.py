import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_permission
from app.models.consolidation import Consolidation
from app.models.identity import User
from app.models.packages import Package
from app.schemas.consolidation import (
    AddPackageToConsolidationRequest,
    ConsolidationCreateRequest,
    ConsolidationListItemOut,
    ConsolidationListOut,
    ConsolidationOut,
    ConsolidationPackageOut,
    MarkInTransitRequest,
    OpsExceptionOut,
    ReportExceptionRequest,
    TransitUpdateRequest,
)
from app.services import consolidation as consolidation_service
from app.services.packages import resolve_tracking_numbers_batch

router = APIRouter(prefix="/warehouse/consolidations", tags=["warehouse-consolidations"])

PAGE_SIZE = 20


async def _package_count(db: AsyncSession, consolidation_id: uuid.UUID) -> int:
    return (
        await db.execute(select(func.count()).select_from(Package).where(Package.consolidation_id == consolidation_id))
    ).scalar_one()


async def _consolidation_to_out(db: AsyncSession, consolidation: Consolidation) -> ConsolidationOut:
    packages = list(
        (await db.execute(select(Package).where(Package.consolidation_id == consolidation.id))).scalars().all()
    )
    tracking_numbers = await resolve_tracking_numbers_batch(db, packages)
    package_outs = [
        ConsolidationPackageOut(
            id=p.id,
            package_code=p.package_code,
            tracking_number=tracking_numbers[p.id],
            weight_grams=p.weight_grams,
            volume_cbm=p.volume_cbm,
            status=p.status.value,
        )
        for p in packages
    ]
    return ConsolidationOut(
        id=consolidation.id,
        consolidation_code=consolidation.consolidation_code,
        shipment_code=consolidation.shipment_code,
        origin_warehouse_id=consolidation.origin_warehouse_id,
        destination_warehouse_id=consolidation.destination_warehouse_id,
        freight_method=consolidation.freight_method,
        freight_provider=consolidation.freight_provider,
        carrier=consolidation.carrier,
        carrier_tracking_reference=consolidation.carrier_tracking_reference,
        current_location=consolidation.current_location,
        total_weight_grams=consolidation.total_weight_grams,
        total_volume_cbm=consolidation.total_volume_cbm,
        declared_value_usd=consolidation.declared_value_usd,
        departure_date=consolidation.departure_date,
        estimated_arrival=consolidation.estimated_arrival,
        arrival_date=consolidation.arrival_date,
        status=consolidation.status,
        package_count=len(package_outs),
        packages=package_outs,
        created_at=consolidation.created_at,
    )


@router.post("", response_model=ConsolidationOut, status_code=201)
async def create_consolidation(
    payload: ConsolidationCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("consolidation.create")),
) -> ConsolidationOut:
    try:
        consolidation = await consolidation_service.create_consolidation(
            db,
            origin_warehouse_id=payload.origin_warehouse_id,
            destination_warehouse_id=payload.destination_warehouse_id,
            freight_method=payload.freight_method,
            freight_provider=payload.freight_provider,
            actor_user_id=user.id,
        )
    except consolidation_service.WarehouseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return await _consolidation_to_out(db, consolidation)


@router.get("", response_model=ConsolidationListOut)
async def list_consolidations(
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("packages.read")),
) -> ConsolidationListOut:
    stmt = select(Consolidation)
    count_stmt = select(func.count()).select_from(Consolidation)
    if status:
        stmt = stmt.where(Consolidation.status == status)
        count_stmt = count_stmt.where(Consolidation.status == status)
    stmt = stmt.order_by(Consolidation.created_at.desc()).limit(PAGE_SIZE).offset((page - 1) * PAGE_SIZE)

    consolidations = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(count_stmt)).scalar_one()

    items = [
        ConsolidationListItemOut(
            id=c.id,
            consolidation_code=c.consolidation_code,
            status=c.status,
            total_weight_grams=c.total_weight_grams,
            total_volume_cbm=c.total_volume_cbm,
            package_count=await _package_count(db, c.id),
            created_at=c.created_at,
        )
        for c in consolidations
    ]
    return ConsolidationListOut(consolidations=items, total=total, page=page, page_size=PAGE_SIZE)


@router.get("/{consolidation_id}", response_model=ConsolidationOut)
async def get_consolidation(
    consolidation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("packages.read")),
) -> ConsolidationOut:
    consolidation = await db.get(Consolidation, consolidation_id)
    if consolidation is None:
        raise HTTPException(status_code=404, detail="Consolidation not found")
    return await _consolidation_to_out(db, consolidation)


@router.post("/{consolidation_id}/packages", response_model=ConsolidationOut)
async def add_package(
    consolidation_id: uuid.UUID,
    payload: AddPackageToConsolidationRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("consolidation.create")),
) -> ConsolidationOut:
    try:
        consolidation = await consolidation_service.add_package(
            db, consolidation_id=consolidation_id, package_id=payload.package_id, actor_user_id=user.id
        )
    except (consolidation_service.ConsolidationNotFoundError, consolidation_service.PackageNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (
        consolidation_service.ConsolidationNotOpenError,
        consolidation_service.PackageAlreadyAssignedError,
        consolidation_service.PackageNotEligibleError,
    ) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await _consolidation_to_out(db, consolidation)


@router.delete("/{consolidation_id}/packages/{package_id}", response_model=ConsolidationOut)
async def remove_package(
    consolidation_id: uuid.UUID,
    package_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("consolidation.create")),
) -> ConsolidationOut:
    try:
        consolidation = await consolidation_service.remove_package(
            db, consolidation_id=consolidation_id, package_id=package_id, actor_user_id=user.id
        )
    except (consolidation_service.ConsolidationNotFoundError, consolidation_service.PackageNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except consolidation_service.ConsolidationNotOpenError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await _consolidation_to_out(db, consolidation)


@router.post("/{consolidation_id}/ready-for-export", response_model=ConsolidationOut)
async def ready_for_export(
    consolidation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("consolidation.close")),
) -> ConsolidationOut:
    try:
        consolidation = await consolidation_service.mark_ready_for_export(
            db, consolidation_id=consolidation_id, actor_user_id=user.id
        )
    except consolidation_service.ConsolidationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (consolidation_service.EmptyConsolidationError, consolidation_service.InvalidConsolidationTransitionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await _consolidation_to_out(db, consolidation)


@router.post("/{consolidation_id}/depart", response_model=ConsolidationOut)
async def depart(
    consolidation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("consolidation.close")),
) -> ConsolidationOut:
    try:
        consolidation = await consolidation_service.mark_departed(db, consolidation_id=consolidation_id, actor_user_id=user.id)
    except consolidation_service.ConsolidationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except consolidation_service.InvalidConsolidationTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await _consolidation_to_out(db, consolidation)


@router.post("/{consolidation_id}/mark-in-transit", response_model=ConsolidationOut)
async def mark_in_transit(
    consolidation_id: uuid.UUID,
    payload: MarkInTransitRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("consolidation.close")),
) -> ConsolidationOut:
    try:
        consolidation = await consolidation_service.mark_in_transit(
            db,
            consolidation_id=consolidation_id,
            carrier=payload.carrier,
            carrier_tracking_reference=payload.carrier_tracking_reference,
            current_location=payload.current_location,
            actor_user_id=user.id,
        )
    except consolidation_service.ConsolidationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except consolidation_service.InvalidConsolidationTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await _consolidation_to_out(db, consolidation)


@router.post("/{consolidation_id}/transit-update", response_model=ConsolidationOut)
async def transit_update(
    consolidation_id: uuid.UUID,
    payload: TransitUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("consolidation.close")),
) -> ConsolidationOut:
    try:
        consolidation = await consolidation_service.record_transit_update(
            db,
            consolidation_id=consolidation_id,
            current_location=payload.current_location,
            estimated_arrival=payload.estimated_arrival,
            actor_user_id=user.id,
        )
    except consolidation_service.ConsolidationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except consolidation_service.InvalidConsolidationTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await _consolidation_to_out(db, consolidation)


@router.post("/{consolidation_id}/arrive-kenya", response_model=ConsolidationOut)
async def arrive_kenya(
    consolidation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("consolidation.receive")),
) -> ConsolidationOut:
    try:
        consolidation = await consolidation_service.mark_arrived_kenya(
            db, consolidation_id=consolidation_id, actor_user_id=user.id
        )
    except consolidation_service.ConsolidationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except consolidation_service.InvalidConsolidationTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await _consolidation_to_out(db, consolidation)


@router.post("/{consolidation_id}/exceptions", response_model=OpsExceptionOut, status_code=201)
async def report_exception(
    consolidation_id: uuid.UUID,
    payload: ReportExceptionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("consolidation.receive")),
) -> OpsExceptionOut:
    try:
        exception = await consolidation_service.report_exception(
            db,
            consolidation_id=consolidation_id,
            exception_type=payload.exception_type,
            severity=payload.severity,
            description=payload.description,
            actor_user_id=user.id,
        )
    except consolidation_service.ConsolidationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return OpsExceptionOut(
        id=exception.id,
        type=exception.type,
        severity=exception.severity,
        entity_type=exception.entity_type,
        entity_id=exception.entity_id,
        description=exception.description,
        status=exception.status.value,
        created_at=exception.created_at,
    )

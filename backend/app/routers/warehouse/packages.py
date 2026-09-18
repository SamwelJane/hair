import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_permission
from app.integrations.cloudinary_client import upload_image
from app.models.identity import User
from app.models.packages import Package
from app.schemas.warehouse import (
    PackageLabelOut,
    PackageListOut,
    PackageOut,
    PackageQCRequest,
    PackageReceiveRequest,
    PackageWeighRequest,
)
from app.services import packages as packages_service

router = APIRouter(prefix="/warehouse/packages", tags=["warehouse-packages"])

PAGE_SIZE = 20


async def _package_to_out(db: AsyncSession, package: Package, tracking_number: str | None = None) -> PackageOut:
    return PackageOut(
        id=package.id,
        package_code=package.package_code,
        order_id=package.order_id,
        external_shipment_id=package.external_shipment_id,
        supplier_order_id=package.supplier_order_id,
        tracking_number=tracking_number or await packages_service.resolve_tracking_number(db, package),
        status=package.status,
        qc_status=package.qc_status,
        condition=package.condition,
        weight_grams=package.weight_grams,
        volume_cbm=package.volume_cbm,
        photo_urls=package.photo_urls,
        location_code=package.location_code,
        notes=package.notes,
        received_at=package.received_at,
        label_printed_at=package.label_printed_at,
        label_reprint_count=package.label_reprint_count,
        created_at=package.created_at,
    )


@router.post("/receive", response_model=PackageOut, status_code=201)
async def receive_package(
    payload: PackageReceiveRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("packages.receive")),
) -> PackageOut:
    try:
        package = await packages_service.receive_platform_package(
            db,
            tracking_number=payload.tracking_number,
            supplier_order_id=payload.supplier_order_id,
            weight_grams=payload.weight_grams,
            condition=payload.condition,
            notes=payload.notes,
            actor_user_id=user.id,
        )
    except packages_service.TrackingNumberNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except packages_service.InvalidSupplierOrderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except packages_service.DuplicateReceiptError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return await _package_to_out(db, package)


@router.get("", response_model=PackageListOut)
async def list_packages(
    q: str | None = None,
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("packages.read")),
) -> PackageListOut:
    stmt = select(Package)
    count_stmt = select(func.count()).select_from(Package)
    if status:
        stmt = stmt.where(Package.status == status)
        count_stmt = count_stmt.where(Package.status == status)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(Package.package_code.ilike(pattern))
        count_stmt = count_stmt.where(Package.package_code.ilike(pattern))

    stmt = stmt.order_by(Package.created_at.desc()).limit(PAGE_SIZE).offset((page - 1) * PAGE_SIZE)
    packages = list((await db.execute(stmt)).scalars().all())
    total = (await db.execute(count_stmt)).scalar_one()

    tracking_numbers = await packages_service.resolve_tracking_numbers_batch(db, packages)
    return PackageListOut(
        packages=[await _package_to_out(db, p, tracking_numbers[p.id]) for p in packages],
        total=total,
        page=page,
        page_size=PAGE_SIZE,
    )


@router.get("/{package_id}", response_model=PackageOut)
async def get_package(
    package_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("packages.read")),
) -> PackageOut:
    package = await db.get(Package, package_id)
    if package is None:
        raise HTTPException(status_code=404, detail="Package not found")
    return await _package_to_out(db, package)


@router.post("/{package_id}/qc", response_model=PackageOut)
async def qc_package(
    package_id: uuid.UUID,
    payload: PackageQCRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("packages.qc")),
) -> PackageOut:
    try:
        package = await packages_service.run_qc(
            db,
            package_id=package_id,
            qc_status=payload.qc_status,
            condition=payload.condition,
            notes=payload.notes,
            actor_user_id=user.id,
        )
    except packages_service.PackageNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return await _package_to_out(db, package)


@router.post("/{package_id}/weigh", response_model=PackageOut)
async def weigh_package(
    package_id: uuid.UUID,
    payload: PackageWeighRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("packages.qc")),
) -> PackageOut:
    try:
        package = await packages_service.record_weight(
            db,
            package_id=package_id,
            weight_grams=payload.weight_grams,
            length_cm=payload.length_cm,
            width_cm=payload.width_cm,
            height_cm=payload.height_cm,
            actor_user_id=user.id,
        )
    except packages_service.PackageNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return await _package_to_out(db, package)


@router.post("/{package_id}/photos", response_model=PackageOut, status_code=201)
async def upload_package_photo(
    package_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("packages.qc")),
) -> PackageOut:
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")
    secure_url, _public_id = upload_image(file_bytes, folder="hiar-business/packages")
    try:
        package = await packages_service.add_package_photo(
            db, package_id=package_id, photo_url=secure_url, actor_user_id=user.id
        )
    except packages_service.PackageNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return await _package_to_out(db, package)


@router.post("/{package_id}/label", response_model=PackageLabelOut, status_code=201)
async def print_label(
    package_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("packages.label")),
) -> PackageLabelOut:
    try:
        package = await packages_service.print_label(db, package_id=package_id, actor_user_id=user.id)
    except packages_service.PackageNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except packages_service.LabelAlreadyPrintedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    label_data = await packages_service.build_label(db, package)
    assert package.label_printed_at is not None  # guaranteed by print_label just above
    return PackageLabelOut(**label_data, printed_at=package.label_printed_at, reprint_count=package.label_reprint_count)


@router.post("/{package_id}/label/reprint", response_model=PackageLabelOut)
async def reprint_label(
    package_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("packages.label")),
) -> PackageLabelOut:
    try:
        package = await packages_service.reprint_label(db, package_id=package_id, actor_user_id=user.id)
    except packages_service.PackageNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except packages_service.LabelNotYetPrintedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    label_data = await packages_service.build_label(db, package)
    assert package.label_printed_at is not None  # guaranteed by reprint_label just above
    return PackageLabelOut(**label_data, printed_at=package.label_printed_at, reprint_count=package.label_reprint_count)

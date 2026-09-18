from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_permission
from app.models.consolidation import Consolidation
from app.models.enums import ConsolidationStatus, PackageCondition, PackageQCStatus, PackageStatus
from app.models.identity import User
from app.models.packages import Package
from app.schemas.warehouse import WarehouseDashboardOut

router = APIRouter(prefix="/warehouse/dashboard", tags=["warehouse-dashboard"])


async def _count(db: AsyncSession, model: type, *conditions: ColumnElement[bool]) -> int:
    stmt = select(func.count()).select_from(model)
    for condition in conditions:
        stmt = stmt.where(condition)
    return (await db.execute(stmt)).scalar_one()


@router.get("", response_model=WarehouseDashboardOut)
async def get_dashboard(
    db: AsyncSession = Depends(get_db), user: User = Depends(require_permission("packages.read"))
) -> WarehouseDashboardOut:
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    return WarehouseDashboardOut(
        received_today=await _count(db, Package, Package.received_at.is_not(None), Package.received_at >= today_start),
        pending_qc=await _count(
            db, Package, Package.status == PackageStatus.RECEIVED, Package.qc_status == PackageQCStatus.PENDING
        ),
        pending_weighing=await _count(db, Package, Package.status == PackageStatus.RECEIVED, Package.weight_grams.is_(None)),
        pending_labeling=await _count(
            db, Package, Package.status == PackageStatus.READY_FOR_CONSOLIDATION, Package.label_printed_at.is_(None)
        ),
        ready_for_consolidation=await _count(db, Package, Package.status == PackageStatus.READY_FOR_CONSOLIDATION),
        consolidated=await _count(db, Package, Package.status == PackageStatus.CONSOLIDATED),
        active_consolidations=await _count(
            db, Consolidation,
            Consolidation.status.in_([ConsolidationStatus.OPEN, ConsolidationStatus.READY_FOR_EXPORT]),
        ),
        exceptions=await _count(db, Package, Package.status == PackageStatus.EXCEPTION),
        damaged=await _count(db, Package, Package.condition == PackageCondition.DAMAGED),
    )

import json
from datetime import datetime, time

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_db, require_admin
from app.models.identity import AuditLog
from app.schemas.admin_audit import AuditLogListOut, AuditLogOut
from app.services.csv_export import to_csv

router = APIRouter(prefix="/admin/audit-logs", tags=["admin-audit-logs"], dependencies=[Depends(require_admin)])

PAGE_SIZE = 50
EXPORT_ROW_CAP = 5000


def _apply_filters(
    stmt: Select, *, action: str | None, entity_type: str | None, date_from: str | None, date_to: str | None
) -> Select:
    if action:
        stmt = stmt.where(AuditLog.action.ilike(f"%{action}%"))
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if date_from:
        stmt = stmt.where(AuditLog.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        end_of_day = datetime.combine(datetime.fromisoformat(date_to).date(), time.max)
        stmt = stmt.where(AuditLog.created_at <= end_of_day)
    return stmt


def _to_out(log: AuditLog) -> AuditLogOut:
    return AuditLogOut(
        id=log.id,
        user_email=log.user.email if log.user else None,
        action=log.action,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        metadata=log.metadata_json,
        created_at=log.created_at,
    )


@router.get("", response_model=AuditLogListOut)
async def list_audit_logs(
    db: AsyncSession = Depends(get_db),
    action: str | None = None,
    entity_type: str | None = None,
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
    page: int = Query(default=1, ge=1),
) -> AuditLogListOut:
    filters = {"action": action, "entity_type": entity_type, "date_from": date_from, "date_to": date_to}

    total = await db.scalar(_apply_filters(select(func.count()).select_from(AuditLog), **filters)) or 0

    stmt = _apply_filters(select(AuditLog), **filters)
    stmt = (
        stmt.options(selectinload(AuditLog.user))
        .order_by(AuditLog.created_at.desc())
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
    )
    logs = (await db.execute(stmt)).scalars().all()

    entity_types = list(
        (await db.execute(select(AuditLog.entity_type).distinct().order_by(AuditLog.entity_type))).scalars().all()
    )

    return AuditLogListOut(
        items=[_to_out(log) for log in logs], total=total, page=page, page_size=PAGE_SIZE, entity_types=entity_types
    )


@router.get("/export")
async def export_audit_logs(
    db: AsyncSession = Depends(get_db),
    action: str | None = None,
    entity_type: str | None = None,
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
) -> Response:
    stmt = _apply_filters(
        select(AuditLog), action=action, entity_type=entity_type, date_from=date_from, date_to=date_to
    )
    stmt = stmt.options(selectinload(AuditLog.user)).order_by(AuditLog.created_at.desc()).limit(EXPORT_ROW_CAP)
    logs = (await db.execute(stmt)).scalars().all()

    # Old app's exact camelCase headers, kept as-is: this is a human/Excel
    # -facing export artifact, not an API contract, so admin familiarity
    # wins over the API's own snake_case convention.
    csv_body = to_csv(
        [
            {
                "when": log.created_at.isoformat(),
                "actor": log.user.email if log.user else "system",
                "action": log.action,
                "entityType": log.entity_type,
                "entityId": log.entity_id,
                "metadata": json.dumps(log.metadata_json) if log.metadata_json else "",
            }
            for log in logs
        ]
    )

    return Response(
        content=csv_body,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="audit-logs.csv"'},
    )

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import AuditLog


async def log_audit(
    db: AsyncSession,
    *,
    user_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Direct port of src/lib/security/audit.ts. Used pervasively across
    mutations for traceability - does not commit its own transaction, so it
    composes with whatever transaction the caller is already in."""
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=metadata,
        )
    )

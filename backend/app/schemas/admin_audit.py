import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: uuid.UUID
    user_email: str | None
    action: str
    entity_type: str
    entity_id: str
    metadata: dict[str, Any] | None
    created_at: datetime


class AuditLogListOut(BaseModel):
    items: list[AuditLogOut]
    total: int
    page: int
    page_size: int
    entity_types: list[str]

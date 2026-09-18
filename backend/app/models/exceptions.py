import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from app.models.enums import OpsExceptionSeverity, OpsExceptionStatus, OpsExceptionType

if TYPE_CHECKING:
    from app.models.identity import User


class OpsException(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """Centralized operational exception/incident tracking. entity_type/
    entity_id is a polymorphic reference (any Order/Package/Consolidation/
    ExternalShipment/etc.), mirroring AuditLog's existing entity_type/
    entity_id pattern rather than inventing a new one."""

    __tablename__ = "ops_exceptions"

    type: Mapped[OpsExceptionType] = mapped_column(Enum(OpsExceptionType, name="ops_exception_type"), nullable=False)
    severity: Mapped[OpsExceptionSeverity] = mapped_column(
        Enum(OpsExceptionSeverity, name="ops_exception_severity"), default=OpsExceptionSeverity.MEDIUM, nullable=False
    )
    entity_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status: Mapped[OpsExceptionStatus] = mapped_column(
        Enum(OpsExceptionStatus, name="ops_exception_status"), default=OpsExceptionStatus.OPEN, nullable=False
    )
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped["User | None"] = relationship()

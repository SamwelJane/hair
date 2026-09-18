import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from app.models.enums import CustomsStatus

if TYPE_CHECKING:
    from app.models.consolidation import Consolidation
    from app.models.packages import Package


class CustomsDeclaration(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """Declarations are usually made at the consolidation (batch) level, with
    an optional package-level declaration for finer-grained duty/HS-code
    tracking - at least one of the two must be linked."""

    __tablename__ = "customs_declarations"
    __table_args__ = (
        CheckConstraint(
            "consolidation_id IS NOT NULL OR package_id IS NOT NULL",
            name="ck_customs_declarations_has_owner",
        ),
    )

    consolidation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consolidations.id"), nullable=True
    )
    package_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("packages.id"), nullable=True)
    hs_code: Mapped[str | None] = mapped_column(String, nullable=True)
    declared_value_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    duty_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    vat_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    status: Mapped[CustomsStatus] = mapped_column(
        Enum(CustomsStatus, name="customs_status"), default=CustomsStatus.PREPARING, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    consolidation: Mapped["Consolidation | None"] = relationship()
    package: Mapped["Package | None"] = relationship()

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from app.models.enums import WarehouseType


class Warehouse(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """A physical warehouse location - the Cherubim Vietnam warehouse and any
    Kenya-side facility. Deliberately minimal for now (a lookup table),
    extensible with capacity/contact fields later without a breaking change."""

    __tablename__ = "warehouses"

    code: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[WarehouseType] = mapped_column(Enum(WarehouseType, name="warehouse_type"), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

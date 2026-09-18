import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import (
    ExternalShipmentStatus,
    PackageCondition,
    PackageQCStatus,
    PackageStatus,
)


class ExternalShipmentCreateRequest(BaseModel):
    customer_name: str = Field(min_length=1)
    customer_phone: str = Field(min_length=7)
    customer_email: str | None = None
    supplier_reference: str | None = None
    notes: str | None = None
    weight_grams: int | None = Field(default=None, gt=0)
    length_cm: Decimal | None = None
    width_cm: Decimal | None = None
    height_cm: Decimal | None = None


class ExternalShipmentOut(BaseModel):
    id: uuid.UUID
    tracking_number: str
    customer_name: str
    customer_phone: str
    customer_email: str | None
    supplier_reference: str | None
    notes: str | None
    status: ExternalShipmentStatus
    created_at: datetime


class ExternalShipmentListOut(BaseModel):
    external_shipments: list[ExternalShipmentOut]
    total: int
    page: int
    page_size: int


class PackageReceiveRequest(BaseModel):
    tracking_number: str = Field(min_length=1)
    supplier_order_id: uuid.UUID | None = None
    weight_grams: int | None = Field(default=None, gt=0)
    condition: PackageCondition | None = None
    notes: str | None = None


class PackageQCRequest(BaseModel):
    qc_status: PackageQCStatus
    condition: PackageCondition | None = None
    notes: str | None = None


class PackageWeighRequest(BaseModel):
    """Warehouse staff enter weight in grams only.
    CBM/dimensions are not captured — the platform charges by weight ($60/kg),
    not volumetric rate. weight_kg is computed server-side."""
    weight_grams: int = Field(gt=0)


class PackageOut(BaseModel):
    id: uuid.UUID
    package_code: str
    order_id: uuid.UUID | None
    external_shipment_id: uuid.UUID | None
    supplier_order_id: uuid.UUID | None
    tracking_number: str
    status: PackageStatus
    qc_status: PackageQCStatus
    condition: PackageCondition | None
    weight_grams: int | None
    weight_kg: Decimal | None
    photo_urls: list[str] | None
    location_code: str | None
    notes: str | None
    received_at: datetime | None
    label_printed_at: datetime | None
    label_reprint_count: int
    created_at: datetime


class PackageListOut(BaseModel):
    packages: list[PackageOut]
    total: int
    page: int
    page_size: int


class PackageLabelOut(BaseModel):
    package_id: uuid.UUID
    package_code: str
    tracking_number: str
    masked_customer_name: str
    destination: str
    weight_grams: int | None
    qr_url: str
    printed_at: datetime
    reprint_count: int


class WarehouseDashboardOut(BaseModel):
    received_today: int
    pending_qc: int
    pending_weighing: int
    pending_labeling: int
    ready_for_consolidation: int
    consolidated: int
    active_consolidations: int
    exceptions: int
    damaged: int

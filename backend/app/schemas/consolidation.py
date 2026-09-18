import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import ConsolidationStatus, OpsExceptionSeverity, OpsExceptionType


class ConsolidationCreateRequest(BaseModel):
    # Defaults to the primary active VN warehouse when omitted - there is
    # only ever one today, so the frontend doesn't need a warehouse-picker
    # dropdown for it. An explicit value stays supported for when a second
    # VN-side warehouse is added.
    origin_warehouse_id: uuid.UUID | None = None
    destination_warehouse_id: uuid.UUID | None = None
    freight_method: str | None = None
    freight_provider: str | None = None


class AddPackageToConsolidationRequest(BaseModel):
    package_id: uuid.UUID


class MarkInTransitRequest(BaseModel):
    carrier: str | None = None
    carrier_tracking_reference: str | None = None
    current_location: str | None = None


class TransitUpdateRequest(BaseModel):
    current_location: str | None = None
    estimated_arrival: datetime | None = None


class ReportExceptionRequest(BaseModel):
    exception_type: OpsExceptionType
    severity: OpsExceptionSeverity = OpsExceptionSeverity.MEDIUM
    description: str | None = None


class OpsExceptionOut(BaseModel):
    id: uuid.UUID
    type: OpsExceptionType
    severity: OpsExceptionSeverity
    entity_type: str
    entity_id: str
    description: str | None
    status: str
    created_at: datetime


class ConsolidationPackageOut(BaseModel):
    id: uuid.UUID
    package_code: str
    tracking_number: str
    weight_grams: int | None
    volume_cbm: Decimal | None
    status: str


class ConsolidationOut(BaseModel):
    id: uuid.UUID
    consolidation_code: str
    shipment_code: str | None
    origin_warehouse_id: uuid.UUID
    destination_warehouse_id: uuid.UUID | None
    freight_method: str | None
    freight_provider: str | None
    carrier: str | None
    carrier_tracking_reference: str | None
    current_location: str | None
    total_weight_grams: int
    total_volume_cbm: Decimal
    declared_value_usd: Decimal | None
    departure_date: datetime | None
    estimated_arrival: datetime | None
    arrival_date: datetime | None
    status: ConsolidationStatus
    package_count: int
    packages: list[ConsolidationPackageOut]
    created_at: datetime


class ConsolidationListItemOut(BaseModel):
    id: uuid.UUID
    consolidation_code: str
    status: ConsolidationStatus
    total_weight_grams: int
    total_volume_cbm: Decimal
    package_count: int
    created_at: datetime


class ConsolidationListOut(BaseModel):
    consolidations: list[ConsolidationListItemOut]
    total: int
    page: int
    page_size: int

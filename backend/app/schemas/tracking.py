import uuid
from datetime import datetime

from pydantic import BaseModel


class TrackingEventOut(BaseModel):
    id: uuid.UUID
    label: str
    location: str | None
    note: str | None
    occurred_at: datetime


class TrackingPackageOut(BaseModel):
    package_code: str
    status: str
    qc_status: str


class DeliveryEstimateOut(BaseModel):
    min_days: int
    max_days: int


class PublicTrackingOut(BaseModel):
    tracking_number: str
    status: str
    packages: list[TrackingPackageOut]
    events: list[TrackingEventOut]
    delivery_estimate: DeliveryEstimateOut | None

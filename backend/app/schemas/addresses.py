import uuid

from pydantic import BaseModel, Field


class CreateAddressRequest(BaseModel):
    label: str | None = None
    full_name: str = Field(min_length=1)
    line1: str = Field(min_length=1)
    line2: str | None = None
    city: str = Field(min_length=1)
    country_code: str = Field(min_length=2, max_length=2)
    postal_code: str | None = None
    phone: str = Field(min_length=1)
    is_default: bool = False


class AddressOut(BaseModel):
    id: uuid.UUID
    label: str | None
    full_name: str
    line1: str
    line2: str | None
    city: str
    country_code: str
    postal_code: str | None
    phone: str
    is_default: bool

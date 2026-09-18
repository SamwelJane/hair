import uuid

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole


class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1)
    role: UserRole = UserRole.STAFF
    password: str = Field(min_length=8, max_length=128)


class AdminUserOut(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: UserRole
    is_active: bool

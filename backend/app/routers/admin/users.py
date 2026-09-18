import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_strict_admin
from app.models.identity import User
from app.schemas.admin_users import AdminUserOut, CreateUserRequest
from app.services import users as users_service

router = APIRouter(prefix="/admin/users", tags=["admin-users"], dependencies=[Depends(require_strict_admin)])


def _to_out(user: User) -> AdminUserOut:
    return AdminUserOut(id=user.id, email=user.email, name=user.name, role=user.role, is_active=user.is_active)


@router.get("", response_model=list[AdminUserOut])
async def list_users(db: AsyncSession = Depends(get_db)) -> list[AdminUserOut]:
    users = (await db.execute(select(User).order_by(User.created_at.desc()))).scalars().all()
    return [_to_out(u) for u in users]


@router.post("", response_model=AdminUserOut, status_code=201)
async def create_user(
    payload: CreateUserRequest, db: AsyncSession = Depends(get_db), admin: User = Depends(require_strict_admin)
) -> AdminUserOut:
    try:
        user = await users_service.create_user(
            db, email=payload.email, name=payload.name, role=payload.role, password=payload.password,
            actor_user_id=admin.id,
        )
    except users_service.EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _to_out(user)


@router.post("/{user_id}/toggle-active", response_model=AdminUserOut)
async def toggle_active(
    user_id: uuid.UUID, db: AsyncSession = Depends(get_db), admin: User = Depends(require_strict_admin)
) -> AdminUserOut:
    try:
        user = await users_service.toggle_user_active(db, user_id, actor_user_id=admin.id)
    except users_service.CannotDeactivateSelfError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except users_service.UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_out(user)

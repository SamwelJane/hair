import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.identity import RefreshToken, User
from app.services.audit import log_audit


class UserNotFoundError(Exception):
    pass


class CannotDeactivateSelfError(Exception):
    pass


class EmailAlreadyRegisteredError(Exception):
    pass


async def create_user(
    db: AsyncSession, *, email: str, name: str, role: UserRole, password: str, actor_user_id: uuid.UUID
) -> User:
    normalized_email = email.strip().lower()
    existing = await db.scalar(select(User).where(User.email == normalized_email))
    if existing is not None:
        raise EmailAlreadyRegisteredError(f"Email {normalized_email} is already registered")

    user = User(email=normalized_email, name=name, role=role, password_hash=hash_password(password))
    db.add(user)
    await db.flush()

    await log_audit(
        db, user_id=actor_user_id, action="CREATE_USER", entity_type="User", entity_id=str(user.id),
        metadata={"email": normalized_email, "role": role.value},
    )
    await db.commit()
    await db.refresh(user)
    return user


async def toggle_user_active(db: AsyncSession, user_id: uuid.UUID, *, actor_user_id: uuid.UUID) -> User:
    if user_id == actor_user_id:
        raise CannotDeactivateSelfError("You cannot deactivate your own account.")

    user = await db.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User {user_id} not found")

    user.is_active = not user.is_active
    await log_audit(
        db, user_id=actor_user_id, action="ACTIVATE_USER" if user.is_active else "DEACTIVATE_USER",
        entity_type="User", entity_id=str(user_id),
    )
    await db.commit()
    await db.refresh(user)
    return user


async def deactivate_own_account(db: AsyncSession, user: User) -> None:
    """Self-service counterpart to toggle_user_active above - deliberately
    separate rather than relaxing that function's CannotDeactivateSelfError
    guard, which exists specifically to stop an admin from being tricked (or
    accidentally clicking) into locking themselves out via the admin panel.
    Also revokes every outstanding refresh token, same as a password reset
    (see services/auth.py::reset_password) - the account is locked out via
    is_active either way, but this closes the window before any already
    -issued access token naturally expires."""
    user.is_active = False
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    await log_audit(db, user_id=user.id, action="SELF_DEACTIVATE_ACCOUNT", entity_type="User", entity_id=str(user.id))
    await db.commit()

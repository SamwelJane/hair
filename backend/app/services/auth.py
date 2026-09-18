import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_token_expiry,
    verify_password,
)
from app.models.enums import UserRole
from app.models.identity import PasswordResetToken, RefreshToken, User

RESET_TOKEN_TTL_MINUTES = 30


class AuthError(Exception):
    pass


class EmailAlreadyRegisteredError(AuthError):
    pass


class InvalidCredentialsError(AuthError):
    pass


class InvalidRefreshTokenError(AuthError):
    pass


class InvalidResetTokenError(AuthError):
    pass


async def register_user(db: AsyncSession, *, name: str, email: str, password: str, phone: str | None) -> User:
    normalized_email = email.strip().lower()
    existing = await db.scalar(select(User).where(User.email == normalized_email))
    if existing is not None:
        raise EmailAlreadyRegisteredError()

    user = User(
        name=name,
        email=normalized_email,
        password_hash=hash_password(password),
        phone=phone,
        role=UserRole.CUSTOMER,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, *, email: str, password: str) -> User:
    normalized_email = email.strip().lower()
    user = await db.scalar(select(User).where(User.email == normalized_email))
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()
    return user


async def issue_token_pair(db: AsyncSession, user: User) -> tuple[str, str]:
    access_token = create_access_token(user.id)
    refresh_token, refresh_hash = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=refresh_token_expiry(),
        )
    )
    await db.commit()
    return access_token, refresh_token


async def rotate_refresh_token(db: AsyncSession, presented_token: str) -> tuple[str, str, User]:
    """Validates and revokes the presented refresh token, issuing a new
    access+refresh pair. Rotation-on-use means a stolen-and-replayed token
    is only usable once before the chain is detectable as reused."""
    token_hash = hash_refresh_token(presented_token)
    stored = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    now = datetime.now(UTC)
    if stored is None or stored.revoked_at is not None or stored.expires_at < now:
        raise InvalidRefreshTokenError()

    user = await db.get(User, stored.user_id)
    if user is None or not user.is_active:
        raise InvalidRefreshTokenError()

    new_token, new_hash = generate_refresh_token()
    new_record = RefreshToken(user_id=user.id, token_hash=new_hash, expires_at=refresh_token_expiry())
    db.add(new_record)
    await db.flush()

    stored.revoked_at = now
    stored.replaced_by_id = new_record.id
    await db.commit()

    return create_access_token(user.id), new_token, user


async def revoke_refresh_token(db: AsyncSession, presented_token: str) -> None:
    token_hash = hash_refresh_token(presented_token)
    stored = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if stored is not None and stored.revoked_at is None:
        stored.revoked_at = datetime.now(UTC)
        await db.commit()


async def request_password_reset(db: AsyncSession, email: str) -> tuple[User, str] | None:
    """Returns (user, raw_token) on success, or None if no such user - the
    caller must always respond identically either way to avoid email
    enumeration, matching the old app's forgot-password behavior."""
    normalized_email = email.strip().lower()
    user = await db.scalar(select(User).where(User.email == normalized_email))
    if user is None:
        return None

    await db.execute(
        delete(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)
        )
    )

    raw_token = secrets.token_hex(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(minutes=RESET_TOKEN_TTL_MINUTES),
        )
    )
    await db.commit()
    return user, raw_token


async def reset_password(db: AsyncSession, *, token: str, new_password: str) -> None:
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    reset_token = await db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    now = datetime.now(UTC)
    if reset_token is None or reset_token.used_at is not None or reset_token.expires_at < now:
        raise InvalidResetTokenError()

    user = await db.get(User, reset_token.user_id)
    if user is None:
        raise InvalidResetTokenError()

    user.password_hash = hash_password(new_password)
    reset_token.used_at = now
    # Invalidate all other unused reset tokens and refresh tokens for this
    # user - a password reset should also log out every other session.
    await db.execute(
        delete(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.id != reset_token.id,
            PasswordResetToken.used_at.is_(None),
        )
    )
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    await db.commit()

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.models.enums import UserRole

settings = get_settings()
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def create_access_token(user_id: uuid.UUID) -> str:
    """Identity-only claim. Role/is_active are NOT trusted from this token -
    core/deps.get_current_user re-reads them live from the DB on every
    request, so deactivating a user takes effect immediately rather than
    waiting for token expiry (mirrors the old app's NextAuth behavior)."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_ttl_minutes),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> uuid.UUID:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("not an access token")
    return uuid.UUID(payload["sub"])


def generate_refresh_token() -> tuple[str, str]:
    """Returns (opaque_token_for_client, hash_to_store). The client sees only
    the opaque token; we persist the hash, mirroring how password reset
    tokens are already handled in the old app."""
    token = secrets.token_urlsafe(48)
    return token, hash_refresh_token(token)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def refresh_token_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(days=settings.jwt_refresh_ttl_days)


GUEST_ORDER_ACCESS_TTL_DAYS = 30


def create_guest_order_access_token(order_number: str) -> str:
    """Replaces the old app's httpOnly `hb_guest_orders` cookie (a
    comma-joined list of the last 20 order numbers), which doesn't translate
    to a mobile client. Instead, checkout returns one narrowly-scoped token
    per order, which the caller (web/mobile) stores locally and presents to
    view that specific guest order - never a session, never access to a
    registered customer's other orders."""
    now = datetime.now(UTC)
    payload = {
        "order_number": order_number,
        "iat": now,
        "exp": now + timedelta(days=GUEST_ORDER_ACCESS_TTL_DAYS),
        "type": "guest_order_access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def verify_guest_order_access_token(token: str, order_number: str) -> bool:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return False
    return payload.get("type") == "guest_order_access" and payload.get("order_number") == order_number


# Mirrors src/lib/auth/rbac.ts from the old app. WAREHOUSE/KENYA_OPS have no
# equivalent role-group constant here - their endpoints gate on
# core/permissions.py::require_permission(...) instead, see that module's
# docstring.
ADMIN_ROLES = (UserRole.ADMIN, UserRole.STAFF)
SUPPLIER_ROLES = (UserRole.SUPPLIER,)


def is_admin_role(role: UserRole) -> bool:
    return role in ADMIN_ROLES


def is_strict_admin(role: UserRole) -> bool:
    return role == UserRole.ADMIN

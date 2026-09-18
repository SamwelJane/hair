from collections.abc import Callable, Sequence

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    ADMIN_ROLES,
    SUPPLIER_ROLES,
    decode_access_token,
)
from app.db.session import get_db
from app.models.catalog import Supplier
from app.models.enums import UserRole
from app.models.identity import User

_bearer_scheme = HTTPBearer(auto_error=False)


async def _load_active_user(user_id, db: AsyncSession) -> User:
    """Live DB lookup for role/is_active on every request - see
    core/security.create_access_token for why this isn't trusted from the
    JWT claim alone."""
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is deactivated")
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        user_id = decode_access_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc
    return await _load_active_user(user_id, db)


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """For guest-allowed endpoints (checkout, cart) that behave differently
    when a valid session is present but must not reject anonymous callers."""
    if credentials is None:
        return None
    try:
        user_id = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        return None
    try:
        return await _load_active_user(user_id, db)
    except HTTPException:
        return None


def require_roles(allowed: Sequence[UserRole]) -> Callable:
    async def _guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return _guard


async def require_strict_admin(user: User = Depends(get_current_user)) -> User:
    """ADMIN only (excludes STAFF) - gates payment confirmation,
    pricing/exchange-rate settings, supplier mgmt, discount codes, and user
    mgmt, mirroring isStrictAdmin() in the old app's rbac.ts."""
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user


# Ready-made guards for the common cases, applied once per-router via
# `dependencies=[Depends(require_admin)]` (see routers/admin/suppliers.py
# and routers/supplier/orders.py for the pattern). There is deliberately no
# require_warehouse/require_kenya_ops equivalent: the warehouse portal's
# endpoints gate on core/permissions.py::require_permission(...) instead,
# since WAREHOUSE_ROLES/KENYA_OPS_ROLES alone can't express "read access for
# both, write access split by permission, ADMIN/STAFF get everything" - see
# docs/VNKE_ROADMAP.md Phase 4/11. An earlier require_roles-based pair of
# guards for these two roles was defined here but never wired to any
# endpoint once that design settled; removed during the Phase 11 audit.
require_admin = require_roles(ADMIN_ROLES)
require_supplier = require_roles(SUPPLIER_ROLES)


async def get_current_supplier(
    user: User = Depends(require_supplier),
    db: AsyncSession = Depends(get_db),
) -> Supplier:
    """Resolves the Supplier business-entity row linked to the current
    session via the real Supplier.user_id FK - see that model's docstring
    for why this replaces the old app's email-string match. Raises 404
    (not 403) when unlinked, since the caller does have a valid supplier
    login, just no profile attached to it yet."""
    supplier = (await db.execute(select(Supplier).where(Supplier.user_id == user.id))).scalar_one_or_none()
    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Your supplier account is not yet linked to a supplier profile.",
        )
    return supplier

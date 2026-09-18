from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.core.deps import get_current_user
from app.models.enums import UserRole
from app.models.identity import User

# Operation-level permissions (spec section 38) rather than only role checks -
# lets a role's exact capabilities change without touching every endpoint
# that currently gates on it. ADMIN/STAFF get full operational access for the
# same reason they already have full access to every other operational area
# (order management, product management) - see ADMIN_ROLES' docstring in
# core/security.py.
_VN_WAREHOUSE_WRITE_PERMISSIONS = frozenset(
    {
        "packages.receive",
        "packages.qc",
        "packages.label",
        "external_shipments.create",
        "consolidation.create",
        "consolidation.close",
    }
)
_READ_PERMISSIONS = frozenset({"packages.read", "external_shipments.read"})
# Customs clearance is Kenya-side work, not Vietnam warehouse work - see
# docs/VNKE_ROADMAP.md Phase 7. consolidation.receive (confirming physical
# arrival in Kenya, and flagging an exception once a batch is in transit or
# has arrived) is shared with the VN warehouse role rather than being
# Kenya-exclusive: either side may be the first to learn of an arrival or a
# problem, whereas customs.update genuinely only makes sense as Kenya-side
# work. Found and fixed during the Phase 11 RBAC audit - see
# docs/VNKE_ROADMAP.md.
_KENYA_OPS_WRITE_PERMISSIONS = frozenset({"customs.update", "consolidation.receive"})

ROLE_PERMISSIONS: dict[UserRole, frozenset[str]] = {
    UserRole.ADMIN: _VN_WAREHOUSE_WRITE_PERMISSIONS | _READ_PERMISSIONS | _KENYA_OPS_WRITE_PERMISSIONS,
    UserRole.STAFF: _VN_WAREHOUSE_WRITE_PERMISSIONS | _READ_PERMISSIONS | _KENYA_OPS_WRITE_PERMISSIONS,
    UserRole.WAREHOUSE: _VN_WAREHOUSE_WRITE_PERMISSIONS | _READ_PERMISSIONS | frozenset({"consolidation.receive"}),
    # Kenya-side last-mile delivery (delivery.*) is out of scope for now -
    # see docs/VNKE_ROADMAP.md Phase 8 - but customs clearance and confirming
    # a batch's Kenya arrival are in scope and are exactly this role's job.
    UserRole.KENYA_OPS: _READ_PERMISSIONS | _KENYA_OPS_WRITE_PERMISSIONS,
}


def require_permission(permission: str) -> Callable:
    async def _guard(user: User = Depends(get_current_user)) -> User:
        if permission not in ROLE_PERMISSIONS.get(user.role, frozenset()):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permission")
        return user

    return _guard

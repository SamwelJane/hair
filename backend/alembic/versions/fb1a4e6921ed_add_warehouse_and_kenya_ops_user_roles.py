"""add warehouse and kenya_ops user roles

Revision ID: fb1a4e6921ed
Revises: be6f2c3535f6
Create Date: 2026-09-16 09:31:12.594697

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'fb1a4e6921ed'
down_revision: str | None = 'be6f2c3535f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_VALUES = ("WAREHOUSE", "KENYA_OPS")
_OLD_VALUES = ("ADMIN", "STAFF", "SUPPLIER", "CUSTOMER")


def upgrade() -> None:
    # Postgres requires ALTER TYPE ... ADD VALUE to run outside a
    # transaction block - autogenerate can't detect or emit this at all,
    # it has to be hand-written.
    with op.get_context().autocommit_block():
        for value in _NEW_VALUES:
            op.execute(f"ALTER TYPE user_role ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # Postgres has no ALTER TYPE ... DROP VALUE. Downgrading means
    # recreating the enum without the new values, which is only safe if no
    # row actually uses them - refuse rather than silently reassigning or
    # deleting users.
    bind = op.get_bind()
    in_use = bind.execute(
        sa.text("SELECT count(*) FROM users WHERE role::text IN :roles").bindparams(
            sa.bindparam("roles", value=_NEW_VALUES, expanding=True)
        )
    ).scalar_one()
    if in_use:
        raise RuntimeError(
            f"Cannot downgrade: {in_use} user(s) still have a WAREHOUSE/KENYA_OPS role. "
            "Reassign or deactivate them before downgrading this migration."
        )

    old_enum = sa.Enum(*_OLD_VALUES, name="user_role")
    op.execute("ALTER TYPE user_role RENAME TO user_role_old")
    old_enum.create(bind, checkfirst=False)
    op.execute(
        "ALTER TABLE users ALTER COLUMN role TYPE user_role USING role::text::user_role"
    )
    op.execute("DROP TYPE user_role_old")

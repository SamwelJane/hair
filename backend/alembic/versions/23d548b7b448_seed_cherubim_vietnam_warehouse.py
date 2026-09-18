"""seed cherubim vietnam warehouse

Revision ID: 23d548b7b448
Revises: a9491cf1a36b
Create Date: 2026-09-16 10:55:53.621318

"""
import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '23d548b7b448'
down_revision: str | None = 'a9491cf1a36b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Fixed, deterministic ID so this row (and anything that might reference it
# by ID in a future migration/seed) is stable across environments, not a
# random UUID assigned differently in every database it's applied to.
CHERUBIM_VN_WAREHOUSE_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def upgrade() -> None:
    op.execute(
        sa.text(
            "INSERT INTO warehouses (id, code, name, type, country, city, is_active, created_at) "
            "VALUES (:id, 'CHERUBIM-VN', 'Cherubim Express', 'VN', 'VN', 'Ho Chi Minh City', true, now()) "
            "ON CONFLICT (code) DO NOTHING"
        ).bindparams(id=CHERUBIM_VN_WAREHOUSE_ID)
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM warehouses WHERE id = :id").bindparams(id=CHERUBIM_VN_WAREHOUSE_ID))

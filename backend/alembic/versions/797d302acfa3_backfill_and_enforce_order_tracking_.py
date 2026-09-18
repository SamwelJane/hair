"""backfill and enforce order tracking number not null

Revision ID: 797d302acfa3
Revises: fb1a4e6921ed
Create Date: 2026-09-16 10:11:04.313796

"""
import secrets
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '797d302acfa3'
down_revision: str | None = 'fb1a4e6921ed'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Deliberately not imported from app.services.order_numbering: migrations
# should stay self-contained so a future refactor of application code can't
# retroactively change what an already-applied historical migration did.
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _random_suffix(length: int = 6) -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


def upgrade() -> None:
    bind = op.get_bind()
    date_part = datetime.now(UTC).strftime("%Y%m%d")

    null_order_ids = bind.execute(sa.text("SELECT id FROM orders WHERE tracking_number IS NULL")).scalars().all()
    for order_id in null_order_ids:
        for _ in range(5):
            candidate = f"VNKE-{date_part}-{_random_suffix()}"
            taken = bind.execute(
                sa.text(
                    "SELECT 1 FROM orders WHERE tracking_number = :tn "
                    "UNION ALL SELECT 1 FROM external_shipments WHERE tracking_number = :tn"
                ),
                {"tn": candidate},
            ).first()
            if taken is None:
                bind.execute(sa.text("UPDATE orders SET tracking_number = :tn WHERE id = :id"), {"tn": candidate, "id": order_id})
                break
        else:
            raise RuntimeError(f"Could not generate a unique tracking number for order {order_id} after 5 attempts")

    op.alter_column('orders', 'tracking_number', existing_type=sa.String(), nullable=False)


def downgrade() -> None:
    op.alter_column('orders', 'tracking_number', existing_type=sa.String(), nullable=True)

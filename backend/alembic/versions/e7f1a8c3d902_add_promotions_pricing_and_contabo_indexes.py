"""add promotions, pricing markup fields, sub-orders, and contabo indexes

Revision ID: e7f1a8c3d902
Revises: d62ba7684e42
Create Date: 2026-09-18 22:55:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e7f1a8c3d902'
down_revision: str | None = 'd62ba7684e42'
down_revision: str | None = 'cc745216339c'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create Enums
    stock_type_enum = postgresql.ENUM('READY_TO_SHIP', 'MADE_TO_ORDER', 'DISCONTINUED', name='stock_type', create_type=False)
    stock_type_enum.create(op.get_bind(), checkfirst=True)

    promo_slot_enum = postgresql.ENUM('HERO_BANNER', 'FLASH_DEAL', 'CATEGORY_TOP', 'TRENDING_BADGE', name='promotion_slot', create_type=False)
    promo_slot_enum.create(op.get_bind(), checkfirst=True)

    promo_status_enum = postgresql.ENUM('PENDING', 'APPROVED', 'REJECTED', 'ACTIVE', 'EXPIRED', name='promotion_status', create_type=False)
    promo_status_enum.create(op.get_bind(), checkfirst=True)

    # 2. Product columns
    op.add_column('products', sa.Column('min_price_usd', sa.Numeric(10, 2), nullable=True))
    op.add_column('products', sa.Column('max_price_usd', sa.Numeric(10, 2), nullable=True))
    op.add_column('products', sa.Column('discount_pct', sa.Numeric(5, 2), nullable=True))
    op.add_column(
        'products',
        sa.Column(
            'stock_type',
            postgresql.ENUM('READY_TO_SHIP', 'MADE_TO_ORDER', 'DISCONTINUED', name='stock_type', create_type=False),
            server_default='MADE_TO_ORDER',
            nullable=False,
        ),
    )

    # 3. Order columns
    op.add_column('orders', sa.Column('packaging_fee_usd', sa.Numeric(10, 2), server_default='2', nullable=False))
    op.add_column('orders', sa.Column('subtotal_supplier_usd', sa.Numeric(10, 2), nullable=True))
    op.add_column('orders', sa.Column('platform_margin_usd', sa.Numeric(10, 2), nullable=True))
    op.add_column('orders', sa.Column('cancellation_fee_usd', sa.Numeric(10, 2), nullable=True))
    op.add_column('orders', sa.Column('refund_amount_usd', sa.Numeric(10, 2), nullable=True))

    # 4. SupplierOrder columns
    op.add_column('supplier_orders', sa.Column('sub_order_number', sa.String(), nullable=True))
    op.create_index(op.f('ix_supplier_orders_sub_order_number'), 'supplier_orders', ['sub_order_number'], unique=True)

    # 5. Package columns
    op.add_column('packages', sa.Column('weight_kg', sa.Numeric(8, 3), nullable=True))

    # 6. SupplierPromotionRequest table
    op.create_table(
        'supplier_promotion_requests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('supplier_id', sa.UUID(), nullable=False),
        sa.Column('product_id', sa.UUID(), nullable=False),
        sa.Column('slot_type', postgresql.ENUM('HERO_BANNER', 'FLASH_DEAL', 'CATEGORY_TOP', 'TRENDING_BADGE', name='promotion_slot', create_type=False), nullable=False),
        sa.Column('rate_usd', sa.Numeric(10, 2), nullable=False),
        sa.Column('duration_days', sa.Integer(), server_default='7', nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', postgresql.ENUM('PENDING', 'APPROVED', 'REJECTED', 'ACTIVE', 'EXPIRED', name='promotion_status', create_type=False), server_default='PENDING', nullable=False),
        sa.Column('banner_image_url', sa.String(), nullable=True),
        sa.Column('custom_headline', sa.String(), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('reviewed_by_id', sa.UUID(), nullable=True),
        sa.Column('impressions_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('clicks_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('orders_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_supplier_promotion_requests_supplier_id'), 'supplier_promotion_requests', ['supplier_id'], unique=False)
    op.create_index(op.f('ix_supplier_promotion_requests_product_id'), 'supplier_promotion_requests', ['product_id'], unique=False)
    op.create_index(op.f('ix_supplier_promotion_requests_status'), 'supplier_promotion_requests', ['status'], unique=False)

    # 7. Contabo Foreign Key Performance Indexes (eliminating sequential scans)
    op.create_index(op.f('ix_orders_user_id'), 'orders', ['user_id'], unique=False)
    op.create_index(op.f('ix_orders_status'), 'orders', ['status'], unique=False)
    op.create_index(op.f('ix_packages_order_id'), 'packages', ['order_id'], unique=False)
    op.create_index(op.f('ix_packages_external_shipment_id'), 'packages', ['external_shipment_id'], unique=False)
    op.create_index(op.f('ix_packages_consolidation_id'), 'packages', ['consolidation_id'], unique=False)
    op.create_index(op.f('ix_packages_warehouse_id'), 'packages', ['warehouse_id'], unique=False)
    op.create_index(op.f('ix_packages_status'), 'packages', ['status'], unique=False)
    op.create_index(op.f('ix_tracking_events_order_id'), 'tracking_events', ['order_id'], unique=False)
    op.create_index(op.f('ix_tracking_events_package_id'), 'tracking_events', ['package_id'], unique=False)
    op.create_index(op.f('ix_tracking_events_external_shipment_id'), 'tracking_events', ['external_shipment_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_tracking_events_external_shipment_id'), table_name='tracking_events')
    op.drop_index(op.f('ix_tracking_events_package_id'), table_name='tracking_events')
    op.drop_index(op.f('ix_tracking_events_order_id'), table_name='tracking_events')
    op.drop_index(op.f('ix_packages_status'), table_name='packages')
    op.drop_index(op.f('ix_packages_warehouse_id'), table_name='packages')
    op.drop_index(op.f('ix_packages_consolidation_id'), table_name='packages')
    op.drop_index(op.f('ix_packages_external_shipment_id'), table_name='packages')
    op.drop_index(op.f('ix_packages_order_id'), table_name='packages')
    op.drop_index(op.f('ix_orders_status'), table_name='orders')
    op.drop_index(op.f('ix_orders_user_id'), table_name='orders')

    # Drop promotion requests table
    op.drop_index(op.f('ix_supplier_promotion_requests_status'), table_name='supplier_promotion_requests')
    op.drop_index(op.f('ix_supplier_promotion_requests_product_id'), table_name='supplier_promotion_requests')
    op.drop_index(op.f('ix_supplier_promotion_requests_supplier_id'), table_name='supplier_promotion_requests')
    op.drop_table('supplier_promotion_requests')

    # Drop columns
    op.drop_column('packages', 'weight_kg')
    op.drop_index(op.f('ix_supplier_orders_sub_order_number'), table_name='supplier_orders')
    op.drop_column('supplier_orders', 'sub_order_number')
    op.drop_column('orders', 'refund_amount_usd')
    op.drop_column('orders', 'cancellation_fee_usd')
    op.drop_column('orders', 'platform_margin_usd')
    op.drop_column('orders', 'subtotal_supplier_usd')
    op.drop_column('orders', 'packaging_fee_usd')
    op.drop_column('products', 'stock_type')
    op.drop_column('products', 'discount_pct')
    op.drop_column('products', 'max_price_usd')
    op.drop_column('products', 'min_price_usd')

    # Drop enums
    sa.Enum(name='promotion_status').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='promotion_slot').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='stock_type').drop(op.get_bind(), checkfirst=True)

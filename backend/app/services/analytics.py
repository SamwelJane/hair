import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.catalog import Product, ProductVariant
from app.models.consolidation import Consolidation
from app.models.customs import CustomsDeclaration
from app.models.enums import (
    ConsolidationStatus,
    CustomsStatus,
    OpsExceptionStatus,
    OpsExceptionType,
    OrderStatus,
    PaymentProviderType,
    PaymentStatus,
    SupplierOrderStatus,
)
from app.models.exceptions import OpsException
from app.models.orders import Order, OrderItem
from app.models.packages import Package
from app.models.payments import Payment, SupplierOrder
from app.models.tracking_events import TrackingEvent

# Mirrors PAID_STATUSES in src/lib/analytics/queries.ts - "paid or further
# along" order statuses, used everywhere revenue/volume should count an
# order (as opposed to still-unpaid or cancelled).
PAID_ORDER_STATUSES: tuple[OrderStatus, ...] = (
    OrderStatus.PAID,
    OrderStatus.SENT_TO_SUPPLIER,
    OrderStatus.SUPPLIER_PROCESSING,
    OrderStatus.READY_FOR_PICKUP,
    OrderStatus.RECEIVED_AT_OFFICE,
    OrderStatus.SHIPPED_INTERNATIONALLY,
    OrderStatus.IN_TRANSIT,
    OrderStatus.DELIVERED,
)

LOW_STOCK_THRESHOLD = 5


def _round2(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


@dataclass
class CountryRevenue:
    country: str
    revenue_usd: Decimal


@dataclass
class ProductRevenue:
    product_name: str
    revenue_usd: Decimal


@dataclass
class RevenueSummary:
    total_revenue_usd: Decimal
    gross_margin_usd: Decimal
    # Net margin here is gross margin minus shipping/handling costs already
    # charged to customers (pass-through, so net ~= gross) - this is a
    # simplified model with no operating-expense tracking, same as the old
    # app's src/lib/analytics/queries.ts::getRevenueSummary.
    net_margin_usd: Decimal
    revenue_by_country: list[CountryRevenue]
    revenue_by_product: list[ProductRevenue]


async def get_revenue_summary(db: AsyncSession) -> RevenueSummary:
    orders = (
        (
            await db.execute(
                select(Order)
                .where(Order.status.in_(PAID_ORDER_STATUSES))
                .options(selectinload(Order.items).selectinload(OrderItem.product).selectinload(Product.supplier))
            )
        )
        .scalars()
        .all()
    )

    total_revenue = Decimal(0)
    total_cost = Decimal(0)
    by_country: dict[str, Decimal] = {}
    by_product: dict[str, Decimal] = {}

    for order in orders:
        total_revenue += order.total_amount_usd
        by_country[order.shipping_country] = by_country.get(order.shipping_country, Decimal(0)) + order.total_amount_usd

        for item in order.items:
            line_total = item.line_total_usd
            by_product[item.product.name] = by_product.get(item.product.name, Decimal(0)) + line_total
            margin_pct = item.product.supplier.default_margin_pct
            total_cost += line_total * (1 - margin_pct / 100)

    gross_margin = total_revenue - total_cost

    return RevenueSummary(
        total_revenue_usd=_round2(total_revenue),
        gross_margin_usd=_round2(gross_margin),
        net_margin_usd=_round2(gross_margin),
        revenue_by_country=sorted(
            (CountryRevenue(country=c, revenue_usd=_round2(v)) for c, v in by_country.items()),
            key=lambda r: r.revenue_usd, reverse=True,
        ),
        revenue_by_product=sorted(
            (ProductRevenue(product_name=p, revenue_usd=_round2(v)) for p, v in by_product.items()),
            key=lambda r: r.revenue_usd, reverse=True,
        ),
    )


@dataclass
class OrderVolumeDay:
    date: str
    count: int


@dataclass
class BestSellingProduct:
    product_name: str
    units_sold: int


@dataclass
class OperationsSummary:
    order_volume_trend: list[OrderVolumeDay]
    best_selling_products: list[BestSellingProduct]
    repeat_customer_rate_pct: float
    avg_supplier_processing_days: float | None
    shipments_in_transit: int


async def get_operations_summary(db: AsyncSession) -> OperationsSummary:
    orders = (
        (
            await db.execute(
                select(Order)
                .where(Order.status.in_(PAID_ORDER_STATUSES))
                .options(selectinload(Order.items).selectinload(OrderItem.product))
            )
        )
        .scalars()
        .all()
    )
    supplier_orders = (
        (await db.execute(select(SupplierOrder).where(SupplierOrder.confirmed_at.is_not(None)))).scalars().all()
    )
    # "Shipment" here means a Consolidation that has left the warehouse but
    # not yet arrived in Kenya - see docs/VNKE_ROADMAP.md Phase 6 for why
    # this is a Consolidation query rather than a separate Shipment table.
    shipments_in_transit = (
        await db.scalar(
            select(func.count())
            .select_from(Consolidation)
            .where(Consolidation.status.in_([ConsolidationStatus.DEPARTED, ConsolidationStatus.IN_TRANSIT]))
        )
        or 0
    )

    day_buckets: dict[str, int] = {}
    units_by_product: dict[str, int] = {}
    orders_by_customer: dict[uuid.UUID, int] = {}

    for order in orders:
        day = order.created_at.strftime("%Y-%m-%d")
        day_buckets[day] = day_buckets.get(day, 0) + 1
        orders_by_customer[order.user_id] = orders_by_customer.get(order.user_id, 0) + 1
        for item in order.items:
            units_by_product[item.product.name] = units_by_product.get(item.product.name, 0) + item.quantity

    repeat_customers = sum(1 for count in orders_by_customer.values() if count > 1)
    repeat_customer_rate_pct = (
        round((repeat_customers / len(orders_by_customer)) * 100, 2) if orders_by_customer else 0.0
    )

    if supplier_orders:
        total_days = 0.0
        for so in supplier_orders:
            assert so.confirmed_at is not None  # narrowed by the confirmed_at.is_not(None) filter above
            total_days += (so.confirmed_at - so.sent_at).total_seconds() / 86400
        avg_supplier_processing_days: float | None = round(total_days / len(supplier_orders), 2)
    else:
        avg_supplier_processing_days = None

    return OperationsSummary(
        order_volume_trend=sorted(
            (OrderVolumeDay(date=d, count=c) for d, c in day_buckets.items()), key=lambda x: x.date
        ),
        best_selling_products=sorted(
            (BestSellingProduct(product_name=p, units_sold=u) for p, u in units_by_product.items()),
            key=lambda x: x.units_sold, reverse=True,
        )[:10],
        repeat_customer_rate_pct=repeat_customer_rate_pct,
        avg_supplier_processing_days=avg_supplier_processing_days,
        shipments_in_transit=shipments_in_transit,
    )


@dataclass
class FinanceSummary:
    total_shipments: int
    avg_profit_per_shipment_usd: Decimal | None
    # No formal accounts-payable/invoice table in this schema - this is a
    # proxy based on default margin percentages, not a ledger, same caveat
    # as the old app's getFinanceSummary.
    estimated_outstanding_supplier_payments_usd: Decimal


async def get_finance_summary(db: AsyncSession) -> FinanceSummary:
    # "Shipment" here means an order that has at least one Package received
    # into the warehouse (i.e. actually entered the fulfilment pipeline) -
    # see docs/VNKE_ROADMAP.md Phase 6 for why this replaced a direct query
    # against the old one-shipment-per-order Shipment table.
    shipped_orders = (
        (
            await db.execute(
                select(Order)
                .join(Package, Package.order_id == Order.id)
                .distinct()
                .options(selectinload(Order.items).selectinload(OrderItem.product).selectinload(Product.supplier))
            )
        )
        .scalars()
        .all()
    )

    total_profit = Decimal(0)
    for order in shipped_orders:
        cost = sum(
            (item.line_total_usd * (1 - item.product.supplier.default_margin_pct / 100) for item in order.items),
            Decimal(0),
        )
        total_profit += order.total_amount_usd - cost - order.shipping_fee_usd

    open_supplier_orders = (
        (
            await db.execute(
                select(SupplierOrder)
                .where(SupplierOrder.status != SupplierOrderStatus.READY)
                .options(
                    selectinload(SupplierOrder.order).selectinload(Order.items).selectinload(OrderItem.product),
                    selectinload(SupplierOrder.supplier),
                )
            )
        )
        .scalars()
        .all()
    )

    estimated_outstanding = Decimal(0)
    for so in open_supplier_orders:
        relevant_items = [item for item in so.order.items if item.product.supplier_id == so.supplier_id]
        margin_pct = so.supplier.default_margin_pct
        estimated_outstanding += sum(
            (item.line_total_usd * (1 - margin_pct / 100) for item in relevant_items), Decimal(0)
        )

    return FinanceSummary(
        total_shipments=len(shipped_orders),
        avg_profit_per_shipment_usd=_round2(total_profit / len(shipped_orders)) if shipped_orders else None,
        estimated_outstanding_supplier_payments_usd=_round2(estimated_outstanding),
    )


@dataclass
class DashboardKpis:
    pending_orders: int
    revenue_today_usd: Decimal
    pending_bank_transfer_payments: int
    low_stock_variants: int


async def get_dashboard_kpis(db: AsyncSession) -> DashboardKpis:
    start_of_today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    pending_orders = (
        await db.scalar(
            select(func.count())
            .select_from(Order)
            .where(Order.status.not_in([OrderStatus.DELIVERED, OrderStatus.CANCELLED]))
        )
        or 0
    )

    todays_total = await db.scalar(
        select(func.coalesce(func.sum(Order.total_amount_usd), 0)).where(
            Order.status.in_(PAID_ORDER_STATUSES), Order.created_at >= start_of_today
        )
    )

    pending_bank_transfer_payments = (
        await db.scalar(
            select(func.count())
            .select_from(Payment)
            .where(
                Payment.provider == PaymentProviderType.BANK_TRANSFER,
                Payment.status.in_([PaymentStatus.INITIATED, PaymentStatus.PENDING]),
            )
        )
        or 0
    )

    low_stock_variants = (
        await db.scalar(
            select(func.count()).select_from(ProductVariant).where(ProductVariant.stock_qty < LOW_STOCK_THRESHOLD)
        )
        or 0
    )

    return DashboardKpis(
        pending_orders=pending_orders,
        revenue_today_usd=_round2(Decimal(todays_total or 0)),
        pending_bank_transfer_payments=pending_bank_transfer_payments,
        low_stock_variants=low_stock_variants,
    )


@dataclass
class StatusCount:
    status: str
    count: int


@dataclass
class LogisticsSummary:
    packages_by_status: list[StatusCount]
    consolidations_by_status: list[StatusCount]
    # Cycle time from a package's "Received at Cherubim Warehouse" tracking
    # event to its "Ready for Delivery" one - the fullest end-to-end
    # duration this roadmap can measure, since Kenya last-mile delivery
    # (Phase 8) is out of scope. None until at least one package has
    # completed the whole pipeline.
    avg_warehouse_to_delivery_ready_days: float | None
    avg_transit_days: float | None
    open_exceptions_count: int


async def get_logistics_summary(db: AsyncSession) -> LogisticsSummary:
    package_rows = (await db.execute(select(Package.status, func.count()).group_by(Package.status))).all()
    consolidation_rows = (
        await db.execute(select(Consolidation.status, func.count()).group_by(Consolidation.status))
    ).all()

    open_exceptions_count = (
        await db.scalar(
            select(func.count()).select_from(OpsException).where(OpsException.status == OpsExceptionStatus.OPEN)
        )
        or 0
    )

    received_at_by_package: dict[uuid.UUID, datetime] = {
        package_id: occurred_at
        for package_id, occurred_at in (
            await db.execute(
                select(TrackingEvent.package_id, TrackingEvent.occurred_at).where(
                    TrackingEvent.package_id.is_not(None), TrackingEvent.label == "Received at Cherubim Warehouse"
                )
            )
        ).all()
        if package_id is not None
    }
    ready_events = (
        await db.execute(
            select(TrackingEvent.package_id, TrackingEvent.occurred_at).where(
                TrackingEvent.package_id.is_not(None), TrackingEvent.label == "Ready for Delivery"
            )
        )
    ).all()
    warehouse_to_ready_days = [
        (ready_at - received_at_by_package[package_id]).total_seconds() / 86400
        for package_id, ready_at in ready_events
        if package_id in received_at_by_package
    ]

    transit_pairs = (
        await db.execute(
            select(Consolidation.departure_date, Consolidation.arrival_date).where(
                Consolidation.departure_date.is_not(None), Consolidation.arrival_date.is_not(None)
            )
        )
    ).all()
    transit_days = [(arrival - departure).total_seconds() / 86400 for departure, arrival in transit_pairs]

    return LogisticsSummary(
        packages_by_status=[StatusCount(status=s.value, count=c) for s, c in package_rows],
        consolidations_by_status=[StatusCount(status=s.value, count=c) for s, c in consolidation_rows],
        avg_warehouse_to_delivery_ready_days=(
            round(sum(warehouse_to_ready_days) / len(warehouse_to_ready_days), 2) if warehouse_to_ready_days else None
        ),
        avg_transit_days=round(sum(transit_days) / len(transit_days), 2) if transit_days else None,
        open_exceptions_count=open_exceptions_count,
    )


@dataclass
class CustomsSummary:
    declarations_by_status: list[StatusCount]
    total_duty_usd: Decimal
    total_vat_usd: Decimal
    # Proxied by OpsException(type=CUSTOMS_QUERY) count rather than a
    # "has ever been queried" flag on CustomsDeclaration - raise_query
    # already creates exactly one such exception per query, and the
    # exception record persists even after the declaration later clears.
    queries_raised_count: int
    query_rate_pct: float


async def get_customs_summary(db: AsyncSession) -> CustomsSummary:
    rows = (await db.execute(select(CustomsDeclaration.status, func.count()).group_by(CustomsDeclaration.status))).all()
    total_declarations = sum(count for _, count in rows)

    duty_total, vat_total = (
        await db.execute(
            select(
                func.coalesce(func.sum(CustomsDeclaration.duty_usd), 0),
                func.coalesce(func.sum(CustomsDeclaration.vat_usd), 0),
            ).where(CustomsDeclaration.status == CustomsStatus.CLEARED)
        )
    ).one()

    queries_raised_count = (
        await db.scalar(
            select(func.count()).select_from(OpsException).where(OpsException.type == OpsExceptionType.CUSTOMS_QUERY)
        )
        or 0
    )

    return CustomsSummary(
        declarations_by_status=[StatusCount(status=s.value, count=c) for s, c in rows],
        total_duty_usd=_round2(Decimal(duty_total)),
        total_vat_usd=_round2(Decimal(vat_total)),
        queries_raised_count=queries_raised_count,
        query_rate_pct=round((queries_raised_count / total_declarations) * 100, 2) if total_declarations else 0.0,
    )


@dataclass
class SupplierPerformance:
    supplier_name: str
    total_orders: int
    avg_processing_days: float | None


@dataclass
class SupplierPerformanceSummary:
    suppliers: list[SupplierPerformance]


async def get_supplier_performance_summary(db: AsyncSession) -> SupplierPerformanceSummary:
    supplier_orders = (
        (await db.execute(select(SupplierOrder).options(selectinload(SupplierOrder.supplier)))).scalars().all()
    )

    by_supplier: dict[str, list[SupplierOrder]] = {}
    for supplier_order in supplier_orders:
        by_supplier.setdefault(supplier_order.supplier.name, []).append(supplier_order)

    suppliers = []
    for name, orders in by_supplier.items():
        confirmed = [so for so in orders if so.confirmed_at is not None]
        processing_days = []
        for so in confirmed:
            assert so.confirmed_at is not None  # narrowed by the filter above
            processing_days.append((so.confirmed_at - so.sent_at).total_seconds() / 86400)
        avg_processing_days = round(sum(processing_days) / len(processing_days), 2) if processing_days else None
        suppliers.append(
            SupplierPerformance(supplier_name=name, total_orders=len(orders), avg_processing_days=avg_processing_days)
        )
    suppliers.sort(key=lambda s: s.total_orders, reverse=True)

    return SupplierPerformanceSummary(suppliers=suppliers)


async def list_current_month_orders(db: AsyncSession) -> list[Order]:
    """Backs the "monthly" CSV export type - an ad-hoc report distinct from
    the four summary functions above, same as the old app's export route."""
    now = datetime.now(UTC)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return list(
        (
            await db.execute(
                select(Order).where(Order.created_at >= start_of_month).order_by(Order.created_at.asc())
            )
        )
        .scalars()
        .all()
    )

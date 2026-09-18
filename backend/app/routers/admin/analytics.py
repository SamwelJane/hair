from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_admin
from app.schemas.admin_analytics import (
    BestSellingProductOut,
    CountryRevenueOut,
    CustomsSummaryOut,
    DashboardKpisOut,
    FinanceSummaryOut,
    LogisticsSummaryOut,
    OperationsSummaryOut,
    OrderVolumeDayOut,
    ProductRevenueOut,
    RevenueSummaryOut,
    StatusCountOut,
    SupplierPerformanceOut,
    SupplierPerformanceSummaryOut,
)
from app.services import analytics as analytics_service
from app.services.csv_export import to_csv

router = APIRouter(prefix="/admin/analytics", tags=["admin-analytics"], dependencies=[Depends(require_admin)])


def _revenue_out(summary: analytics_service.RevenueSummary) -> RevenueSummaryOut:
    return RevenueSummaryOut(
        total_revenue_usd=summary.total_revenue_usd,
        gross_margin_usd=summary.gross_margin_usd,
        net_margin_usd=summary.net_margin_usd,
        revenue_by_country=[CountryRevenueOut(country=r.country, revenue_usd=r.revenue_usd) for r in summary.revenue_by_country],
        revenue_by_product=[ProductRevenueOut(product_name=r.product_name, revenue_usd=r.revenue_usd) for r in summary.revenue_by_product],
    )


@router.get("/revenue", response_model=RevenueSummaryOut)
async def get_revenue(db: AsyncSession = Depends(get_db)) -> RevenueSummaryOut:
    return _revenue_out(await analytics_service.get_revenue_summary(db))


@router.get("/operations", response_model=OperationsSummaryOut)
async def get_operations(db: AsyncSession = Depends(get_db)) -> OperationsSummaryOut:
    summary = await analytics_service.get_operations_summary(db)
    return OperationsSummaryOut(
        order_volume_trend=[OrderVolumeDayOut(date=d.date, count=d.count) for d in summary.order_volume_trend],
        best_selling_products=[
            BestSellingProductOut(product_name=p.product_name, units_sold=p.units_sold)
            for p in summary.best_selling_products
        ],
        repeat_customer_rate_pct=summary.repeat_customer_rate_pct,
        avg_supplier_processing_days=summary.avg_supplier_processing_days,
        shipments_in_transit=summary.shipments_in_transit,
    )


@router.get("/finance", response_model=FinanceSummaryOut)
async def get_finance(db: AsyncSession = Depends(get_db)) -> FinanceSummaryOut:
    summary = await analytics_service.get_finance_summary(db)
    return FinanceSummaryOut(
        total_shipments=summary.total_shipments,
        avg_profit_per_shipment_usd=summary.avg_profit_per_shipment_usd,
        estimated_outstanding_supplier_payments_usd=summary.estimated_outstanding_supplier_payments_usd,
    )


@router.get("/dashboard-kpis", response_model=DashboardKpisOut)
async def get_dashboard_kpis(db: AsyncSession = Depends(get_db)) -> DashboardKpisOut:
    kpis = await analytics_service.get_dashboard_kpis(db)
    return DashboardKpisOut(
        pending_orders=kpis.pending_orders,
        revenue_today_usd=kpis.revenue_today_usd,
        pending_bank_transfer_payments=kpis.pending_bank_transfer_payments,
        low_stock_variants=kpis.low_stock_variants,
    )


@router.get("/logistics", response_model=LogisticsSummaryOut)
async def get_logistics(db: AsyncSession = Depends(get_db)) -> LogisticsSummaryOut:
    summary = await analytics_service.get_logistics_summary(db)
    return LogisticsSummaryOut(
        packages_by_status=[StatusCountOut(status=s.status, count=s.count) for s in summary.packages_by_status],
        consolidations_by_status=[
            StatusCountOut(status=s.status, count=s.count) for s in summary.consolidations_by_status
        ],
        avg_warehouse_to_delivery_ready_days=summary.avg_warehouse_to_delivery_ready_days,
        avg_transit_days=summary.avg_transit_days,
        open_exceptions_count=summary.open_exceptions_count,
    )


@router.get("/customs", response_model=CustomsSummaryOut)
async def get_customs(db: AsyncSession = Depends(get_db)) -> CustomsSummaryOut:
    summary = await analytics_service.get_customs_summary(db)
    return CustomsSummaryOut(
        declarations_by_status=[StatusCountOut(status=s.status, count=s.count) for s in summary.declarations_by_status],
        total_duty_usd=summary.total_duty_usd,
        total_vat_usd=summary.total_vat_usd,
        queries_raised_count=summary.queries_raised_count,
        query_rate_pct=summary.query_rate_pct,
    )


@router.get("/suppliers", response_model=SupplierPerformanceSummaryOut)
async def get_supplier_performance(db: AsyncSession = Depends(get_db)) -> SupplierPerformanceSummaryOut:
    summary = await analytics_service.get_supplier_performance_summary(db)
    return SupplierPerformanceSummaryOut(
        suppliers=[
            SupplierPerformanceOut(
                supplier_name=s.supplier_name, total_orders=s.total_orders, avg_processing_days=s.avg_processing_days
            )
            for s in summary.suppliers
        ]
    )


@router.get("/export")
async def export_analytics(type: str = "revenue", db: AsyncSession = Depends(get_db)) -> Response:
    """Matches src/app/api/admin/analytics/export/route.ts's 5 report types
    exactly - "revenue" and "products" both slice the one revenue summary
    two different ways, "monthly" is a distinct ad-hoc report, not one of
    the four summary functions."""
    csv_body = ""
    filename = "export.csv"

    if type == "revenue":
        revenue = await analytics_service.get_revenue_summary(db)
        csv_body = to_csv([{"country": r.country, "revenueUsd": str(r.revenue_usd)} for r in revenue.revenue_by_country])
        filename = "revenue-by-country.csv"
    elif type == "products":
        revenue = await analytics_service.get_revenue_summary(db)
        csv_body = to_csv([{"product": r.product_name, "revenueUsd": str(r.revenue_usd)} for r in revenue.revenue_by_product])
        filename = "revenue-by-product.csv"
    elif type == "operations":
        operations = await analytics_service.get_operations_summary(db)
        csv_body = to_csv([{"date": d.date, "orders": d.count} for d in operations.order_volume_trend])
        filename = "order-volume-trend.csv"
    elif type == "monthly":
        now = datetime.now(UTC)
        orders = await analytics_service.list_current_month_orders(db)
        csv_body = to_csv(
            [
                {
                    "orderNumber": o.order_number,
                    "date": o.created_at.strftime("%Y-%m-%d"),
                    "status": o.status.value,
                    "totalUsd": str(o.total_amount_usd),
                    "country": o.shipping_country,
                }
                for o in orders
            ]
        )
        filename = f"monthly-report-{now.year}-{now.month:02d}.csv"
    elif type == "finance":
        finance = await analytics_service.get_finance_summary(db)
        csv_body = to_csv(
            [
                {"metric": "Total Shipments", "value": finance.total_shipments},
                {"metric": "Avg Profit per Shipment (USD)", "value": str(finance.avg_profit_per_shipment_usd or Decimal(0))},
                {
                    "metric": "Estimated Outstanding Supplier Payments (USD)",
                    "value": str(finance.estimated_outstanding_supplier_payments_usd),
                },
            ]
        )
        filename = "finance-summary.csv"
    elif type == "logistics":
        logistics = await analytics_service.get_logistics_summary(db)
        csv_body = to_csv(
            [{"status": s.status, "count": s.count} for s in logistics.packages_by_status]
        )
        filename = "packages-by-status.csv"
    elif type == "customs":
        customs = await analytics_service.get_customs_summary(db)
        csv_body = to_csv(
            [
                {"metric": "Total Duty (USD)", "value": str(customs.total_duty_usd)},
                {"metric": "Total VAT (USD)", "value": str(customs.total_vat_usd)},
                {"metric": "Queries Raised", "value": customs.queries_raised_count},
                {"metric": "Query Rate (%)", "value": customs.query_rate_pct},
            ]
        )
        filename = "customs-summary.csv"
    elif type == "suppliers":
        suppliers = await analytics_service.get_supplier_performance_summary(db)
        csv_body = to_csv(
            [
                {
                    "supplier": s.supplier_name,
                    "totalOrders": s.total_orders,
                    "avgProcessingDays": s.avg_processing_days if s.avg_processing_days is not None else "",
                }
                for s in suppliers.suppliers
            ]
        )
        filename = "supplier-performance.csv"

    return Response(
        content=csv_body, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

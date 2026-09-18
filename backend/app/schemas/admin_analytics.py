from decimal import Decimal

from pydantic import BaseModel


class CountryRevenueOut(BaseModel):
    country: str
    revenue_usd: Decimal


class ProductRevenueOut(BaseModel):
    product_name: str
    revenue_usd: Decimal


class RevenueSummaryOut(BaseModel):
    total_revenue_usd: Decimal
    gross_margin_usd: Decimal
    net_margin_usd: Decimal
    revenue_by_country: list[CountryRevenueOut]
    revenue_by_product: list[ProductRevenueOut]


class OrderVolumeDayOut(BaseModel):
    date: str
    count: int


class BestSellingProductOut(BaseModel):
    product_name: str
    units_sold: int


class OperationsSummaryOut(BaseModel):
    order_volume_trend: list[OrderVolumeDayOut]
    best_selling_products: list[BestSellingProductOut]
    repeat_customer_rate_pct: float
    avg_supplier_processing_days: float | None
    shipments_in_transit: int


class FinanceSummaryOut(BaseModel):
    total_shipments: int
    avg_profit_per_shipment_usd: Decimal | None
    estimated_outstanding_supplier_payments_usd: Decimal


class DashboardKpisOut(BaseModel):
    pending_orders: int
    revenue_today_usd: Decimal
    pending_bank_transfer_payments: int
    low_stock_variants: int


class StatusCountOut(BaseModel):
    status: str
    count: int


class LogisticsSummaryOut(BaseModel):
    packages_by_status: list[StatusCountOut]
    consolidations_by_status: list[StatusCountOut]
    avg_warehouse_to_delivery_ready_days: float | None
    avg_transit_days: float | None
    open_exceptions_count: int


class CustomsSummaryOut(BaseModel):
    declarations_by_status: list[StatusCountOut]
    total_duty_usd: Decimal
    total_vat_usd: Decimal
    queries_raised_count: int
    query_rate_pct: float


class SupplierPerformanceOut(BaseModel):
    supplier_name: str
    total_orders: int
    avg_processing_days: float | None


class SupplierPerformanceSummaryOut(BaseModel):
    suppliers: list[SupplierPerformanceOut]

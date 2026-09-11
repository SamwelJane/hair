import { requireAdminSession } from "@/lib/auth/require-admin";
import { getOperationsSummary } from "@/lib/analytics/queries";
import { StatTile } from "@/components/admin/charts/StatTile";
import { HorizontalBarChart } from "@/components/admin/charts/HorizontalBarChart";
import { TrendLineChart } from "@/components/admin/charts/TrendLineChart";

export default async function OperationsAnalyticsPage() {
  await requireAdminSession();
  const operations = await getOperationsSummary();

  return (
    <div className="mx-auto max-w-4xl p-6 text-admin-ink">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Operations</h1>
        <a href="/api/admin/analytics/export?type=operations" className="rounded border border-admin-border px-3 py-1 text-sm hover:bg-admin-surface-2">
          Export Order Volume CSV
        </a>
      </div>

      <div className="mt-6 grid grid-cols-3 gap-4">
        <StatTile
          label="Avg Supplier Processing Time"
          value={operations.avgSupplierProcessingDays !== null ? `${operations.avgSupplierProcessingDays}d` : "-"}
        />
        <StatTile label="Repeat Customer Rate" value={`${operations.repeatCustomerRatePct}%`} />
        <StatTile label="Shipments In Transit / Open" value={`${operations.shipmentsInTransit}`} />
      </div>

      <h2 className="mt-8 mb-3 text-lg font-semibold">Order Volume Trend</h2>
      <TrendLineChart data={operations.orderVolumeTrend.map((d) => ({ label: d.date, value: d.count }))} />

      <h2 className="mt-8 mb-3 text-lg font-semibold">Best-Selling Products</h2>
      <HorizontalBarChart
        data={operations.bestSellingProducts.map((p) => ({ label: p.productName, value: p.unitsSold }))}
        valueFormatter={(v) => `${v} units`}
      />
    </div>
  );
}

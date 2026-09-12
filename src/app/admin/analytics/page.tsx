import Link from "next/link";
import { requireAdminSession } from "@/lib/auth/require-admin";
import { getRevenueSummary, getOperationsSummary, getFinanceSummary } from "@/lib/analytics/queries";
import { StatTile } from "@/components/admin/charts/StatTile";
import { HorizontalBarChart } from "@/components/admin/charts/HorizontalBarChart";
import { TrendLineChart } from "@/components/admin/charts/TrendLineChart";

export default async function AdminAnalyticsPage() {
  await requireAdminSession();
  const [revenue, operations, finance] = await Promise.all([
    getRevenueSummary(),
    getOperationsSummary(),
    getFinanceSummary(),
  ]);

  return (
    <div className="mx-auto max-w-5xl p-6 text-admin-ink">
      <h1 className="text-2xl font-semibold">Analytics</h1>
      <nav className="mt-2 flex gap-4 text-sm text-admin-accent">
        <Link href="/admin/analytics/revenue" className="underline">Revenue</Link>
        <Link href="/admin/analytics/operations" className="underline">Operations</Link>
        <Link href="/admin/analytics/finance" className="underline">Finance</Link>
      </nav>

      <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatTile label="Total Revenue" value={`$${revenue.totalRevenueUsd.toLocaleString()}`} />
        <StatTile label="Gross Margin" value={`$${revenue.grossMarginUsd.toLocaleString()}`} />
        <StatTile label="Repeat Customer Rate" value={`${operations.repeatCustomerRatePct}%`} />
        <StatTile
          label="Avg Profit / Shipment"
          value={finance.avgProfitPerShipmentUsd !== null ? `$${finance.avgProfitPerShipmentUsd}` : "-"}
        />
      </div>

      <div className="mt-8 grid grid-cols-1 gap-8 md:grid-cols-2">
        <div>
          <h2 className="mb-3 text-lg font-semibold">Revenue by Country</h2>
          <HorizontalBarChart
            data={revenue.revenueByCountry.map((r) => ({ label: r.country, value: r.revenueUsd }))}
            valueFormatter={(v) => `$${v.toLocaleString()}`}
          />
        </div>
        <div>
          <h2 className="mb-3 text-lg font-semibold">Best-Selling Products</h2>
          <HorizontalBarChart
            data={operations.bestSellingProducts.map((p) => ({ label: p.productName, value: p.unitsSold }))}
            valueFormatter={(v) => `${v} units`}
          />
        </div>
      </div>

      <div className="mt-8">
        <h2 className="mb-3 text-lg font-semibold">Order Volume Trend</h2>
        <TrendLineChart data={operations.orderVolumeTrend.map((d) => ({ label: d.date, value: d.count }))} />
      </div>
    </div>
  );
}

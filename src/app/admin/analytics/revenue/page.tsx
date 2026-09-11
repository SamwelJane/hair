import { requireAdminSession } from "@/lib/auth/require-admin";
import { getRevenueSummary } from "@/lib/analytics/queries";
import { StatTile } from "@/components/admin/charts/StatTile";
import { HorizontalBarChart } from "@/components/admin/charts/HorizontalBarChart";

export default async function RevenueAnalyticsPage() {
  await requireAdminSession();
  const revenue = await getRevenueSummary();

  return (
    <div className="mx-auto max-w-4xl p-6 text-admin-ink">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Revenue</h1>
        <div className="flex gap-2 text-sm">
          <a href="/api/admin/analytics/export?type=revenue" className="rounded border border-admin-border px-3 py-1 hover:bg-admin-surface-2">
            Export by Country CSV
          </a>
          <a href="/api/admin/analytics/export?type=products" className="rounded border border-admin-border px-3 py-1 hover:bg-admin-surface-2">
            Export by Product CSV
          </a>
          <a href="/api/admin/analytics/export?type=monthly" className="rounded border border-admin-border px-3 py-1 hover:bg-admin-surface-2">
            Monthly Report CSV
          </a>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-3 gap-4">
        <StatTile label="Total Revenue" value={`$${revenue.totalRevenueUsd.toLocaleString()}`} />
        <StatTile label="Gross Margin" value={`$${revenue.grossMarginUsd.toLocaleString()}`} />
        <StatTile label="Net Margin" value={`$${revenue.netMarginUsd.toLocaleString()}`} sublabel="approx., shipping is pass-through" />
      </div>

      <h2 className="mt-8 mb-3 text-lg font-semibold">Revenue by Country</h2>
      <HorizontalBarChart
        data={revenue.revenueByCountry.map((r) => ({ label: r.country, value: r.revenueUsd }))}
        valueFormatter={(v) => `$${v.toLocaleString()}`}
      />

      <h2 className="mt-8 mb-3 text-lg font-semibold">Revenue by Product</h2>
      <HorizontalBarChart
        data={revenue.revenueByProduct.map((r) => ({ label: r.productName, value: r.revenueUsd }))}
        valueFormatter={(v) => `$${v.toLocaleString()}`}
      />
    </div>
  );
}

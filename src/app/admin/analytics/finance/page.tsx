import { requireAdminSession } from "@/lib/auth/require-admin";
import { getFinanceSummary } from "@/lib/analytics/queries";
import { StatTile } from "@/components/admin/charts/StatTile";

export default async function FinanceAnalyticsPage() {
  await requireAdminSession();
  const finance = await getFinanceSummary();

  return (
    <div className="mx-auto max-w-3xl p-6 text-admin-ink">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Finance</h1>
        <a href="/api/admin/analytics/export?type=finance" className="rounded border border-admin-border px-3 py-1 text-sm hover:bg-admin-surface-2">
          Export CSV
        </a>
      </div>

      <div className="mt-6 grid grid-cols-3 gap-4">
        <StatTile label="Total Shipments" value={`${finance.totalShipments}`} />
        <StatTile
          label="Avg Profit / Shipment"
          value={finance.avgProfitPerShipmentUsd !== null ? `$${finance.avgProfitPerShipmentUsd}` : "-"}
          sublabel="revenue - est. supplier cost - shipping"
        />
        <StatTile
          label="Est. Outstanding to Suppliers"
          value={`$${finance.estimatedOutstandingSupplierPaymentsUsd.toLocaleString()}`}
          sublabel="unsettled supplier orders, margin-based estimate"
        />
      </div>

      <p className="mt-8 text-xs text-admin-muted">
        Note: there is no formal accounts-payable ledger yet - supplier cost and outstanding
        balances are estimated from each supplier&apos;s default margin percentage, not from
        actual invoices. Add a supplier invoicing model if precise AP tracking is needed.
      </p>
    </div>
  );
}

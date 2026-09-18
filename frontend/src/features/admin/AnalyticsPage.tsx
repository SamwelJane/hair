import {
  downloadAnalyticsExport,
  useCustomsSummary,
  useFinanceSummary,
  useLogisticsSummary,
  useOperationsSummary,
  useRevenueSummary,
  useSupplierPerformanceSummary,
} from "./hooks";

export function AdminAnalyticsPage() {
  const revenue = useRevenueSummary();
  const operations = useOperationsSummary();
  const finance = useFinanceSummary();
  const logistics = useLogisticsSummary();
  const customs = useCustomsSummary();
  const supplierPerformance = useSupplierPerformanceSummary();

  return (
    <div className="page">
      <h1>Analytics</h1>

      <div className="callout">
        <div className="link-row" style={{ justifyContent: "space-between" }}>
          <h2>Revenue</h2>
          <div className="link-row">
            <button type="button" onClick={() => void downloadAnalyticsExport("revenue")}>Export by country</button>
            <button type="button" onClick={() => void downloadAnalyticsExport("products")}>Export by product</button>
          </div>
        </div>
        {revenue.data && (
          <>
            <p>Total revenue: ${revenue.data.total_revenue_usd} · Gross margin: ${revenue.data.gross_margin_usd} · Net margin: ${revenue.data.net_margin_usd}</p>
            <h3>By country</h3>
            <ul className="order-item-list">
              {revenue.data.revenue_by_country.map((r) => <li key={r.country}><span>{r.country}</span><span>${r.revenue_usd}</span></li>)}
            </ul>
            <h3>By product</h3>
            <ul className="order-item-list">
              {revenue.data.revenue_by_product.map((r) => <li key={r.product_name}><span>{r.product_name}</span><span>${r.revenue_usd}</span></li>)}
            </ul>
          </>
        )}
      </div>

      <div className="callout">
        <div className="link-row" style={{ justifyContent: "space-between" }}>
          <h2>Operations</h2>
          <button type="button" onClick={() => void downloadAnalyticsExport("operations")}>Export order volume</button>
        </div>
        {operations.data && (
          <>
            <p>Repeat customer rate: {operations.data.repeat_customer_rate_pct}% · Avg supplier processing: {operations.data.avg_supplier_processing_days ?? "-"} days · Shipments in transit: {operations.data.shipments_in_transit}</p>
            <h3>Best sellers</h3>
            <ul className="order-item-list">
              {operations.data.best_selling_products.map((p) => <li key={p.product_name}><span>{p.product_name}</span><span>{p.units_sold} units</span></li>)}
            </ul>
          </>
        )}
      </div>

      <div className="callout">
        <div className="link-row" style={{ justifyContent: "space-between" }}>
          <h2>Finance</h2>
          <button type="button" onClick={() => void downloadAnalyticsExport("finance")}>Export summary</button>
        </div>
        {finance.data && (
          <p>
            Total shipments: {finance.data.total_shipments} · Avg profit/shipment: ${finance.data.avg_profit_per_shipment_usd ?? "-"} ·
            Estimated outstanding supplier payments: ${finance.data.estimated_outstanding_supplier_payments_usd}
          </p>
        )}
      </div>

      <div className="callout">
        <div className="link-row" style={{ justifyContent: "space-between" }}>
          <h2>Logistics</h2>
          <button type="button" onClick={() => void downloadAnalyticsExport("logistics")}>Export package status</button>
        </div>
        {logistics.data && (
          <>
            <p>
              Avg warehouse-to-delivery-ready: {logistics.data.avg_warehouse_to_delivery_ready_days ?? "-"} days ·
              Avg transit time: {logistics.data.avg_transit_days ?? "-"} days ·
              Open exceptions: {logistics.data.open_exceptions_count}
            </p>
            <h3>Packages by status</h3>
            <ul className="order-item-list">
              {logistics.data.packages_by_status.map((s) => (
                <li key={s.status}><span>{s.status.replaceAll("_", " ")}</span><span>{s.count}</span></li>
              ))}
            </ul>
            <h3>Consolidations by status</h3>
            <ul className="order-item-list">
              {logistics.data.consolidations_by_status.map((s) => (
                <li key={s.status}><span>{s.status.replaceAll("_", " ")}</span><span>{s.count}</span></li>
              ))}
            </ul>
          </>
        )}
      </div>

      <div className="callout">
        <div className="link-row" style={{ justifyContent: "space-between" }}>
          <h2>Customs</h2>
          <button type="button" onClick={() => void downloadAnalyticsExport("customs")}>Export summary</button>
        </div>
        {customs.data && (
          <>
            <p>
              Total duty collected: ${customs.data.total_duty_usd} · Total VAT collected: ${customs.data.total_vat_usd} ·
              Queries raised: {customs.data.queries_raised_count} ({customs.data.query_rate_pct}% of declarations)
            </p>
            <ul className="order-item-list">
              {customs.data.declarations_by_status.map((s) => (
                <li key={s.status}><span>{s.status.replaceAll("_", " ")}</span><span>{s.count}</span></li>
              ))}
            </ul>
          </>
        )}
      </div>

      <div className="callout">
        <div className="link-row" style={{ justifyContent: "space-between" }}>
          <h2>Supplier Performance</h2>
          <button type="button" onClick={() => void downloadAnalyticsExport("suppliers")}>Export summary</button>
        </div>
        {supplierPerformance.data && (
          <ul className="order-item-list">
            {supplierPerformance.data.suppliers.map((s) => (
              <li key={s.supplier_name}>
                <span>{s.supplier_name}</span>
                <span>{s.total_orders} orders · avg {s.avg_processing_days ?? "-"} days</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <p className="muted">
        <button type="button" className="link-button" onClick={() => void downloadAnalyticsExport("monthly")}>Download this month's order report</button>
      </p>
    </div>
  );
}

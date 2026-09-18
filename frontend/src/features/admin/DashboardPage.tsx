import { Link } from "react-router";
import { useDashboardKpis } from "./hooks";

export function AdminDashboardPage() {
  const { data: kpis, isLoading } = useDashboardKpis();

  if (isLoading) return <div className="page">Loading...</div>;

  return (
    <div className="page">
      <h1>Dashboard</h1>
      <div className="product-grid">
        <div className="product-card"><div style={{ padding: "1rem" }}><p className="muted">Pending Orders</p><p className="total">{kpis?.pending_orders}</p></div></div>
        <div className="product-card"><div style={{ padding: "1rem" }}><p className="muted">Revenue Today</p><p className="total">${kpis?.revenue_today_usd}</p></div></div>
        <div className="product-card"><div style={{ padding: "1rem" }}><p className="muted">Pending Bank Transfers</p><p className="total">{kpis?.pending_bank_transfer_payments}</p></div></div>
        <div className="product-card"><div style={{ padding: "1rem" }}><p className="muted">Low Stock Variants</p><p className="total">{kpis?.low_stock_variants}</p></div></div>
      </div>
      <p style={{ marginTop: "1.5rem" }}>
        <Link to="/admin/analytics">View full analytics →</Link>
      </p>
    </div>
  );
}

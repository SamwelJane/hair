import { useParams } from "react-router";
import { useAdminSupplierDetail, useAdvanceSupplierOrder } from "./hooks";

export function AdminSupplierDetailPage() {
  const { supplierId } = useParams<{ supplierId: string }>();
  const { data, isLoading } = useAdminSupplierDetail(supplierId);
  const advance = useAdvanceSupplierOrder();

  if (isLoading) return <div className="page">Loading...</div>;
  if (!data) return <div className="page">Supplier not found.</div>;

  return (
    <div className="page">
      <h1>{data.supplier.name}</h1>
      <p className="muted">{data.supplier.country} · {data.supplier.email} · Status: {data.supplier.status}</p>

      <div className="product-grid">
        <div className="product-card"><div style={{ padding: "1rem" }}><p className="muted">Total Orders</p><p className="total">{data.performance.total_orders}</p></div></div>
        <div className="product-card"><div style={{ padding: "1rem" }}><p className="muted">Completed</p><p className="total">{data.performance.completed_orders}</p></div></div>
        <div className="product-card"><div style={{ padding: "1rem" }}><p className="muted">Avg Processing (days)</p><p className="total">{data.performance.avg_processing_days ?? "-"}</p></div></div>
        <div className="product-card"><div style={{ padding: "1rem" }}><p className="muted">On-time Rate</p><p className="total">{data.performance.on_time_rate_pct ?? "-"}%</p></div></div>
      </div>

      <h2>Pending Orders</h2>
      <table className="page-table">
        <thead><tr><th>Order #</th><th>Customer</th><th>Status</th><th /></tr></thead>
        <tbody>
          {data.pending_orders.map((po) => (
            <tr key={po.id}>
              <td>{po.order_number}</td>
              <td>{po.customer_email}</td>
              <td><span className="badge">{po.status}</span></td>
              <td>
                {po.status !== "READY" && po.status !== "DECLINED" && (
                  <button type="button" onClick={() => advance.mutate(po.id)}>Advance</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {data.pending_orders.length === 0 && <p>No pending orders.</p>}
    </div>
  );
}

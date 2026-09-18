import { useState } from "react";
import { Link } from "react-router";
import { useAdminOrders } from "./hooks";

export function AdminOrdersPage() {
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const { data, isLoading } = useAdminOrders({ q: q || undefined, status: status || undefined, page });

  return (
    <div className="page">
      <h1>Orders</h1>
      <div className="filter-bar">
        <input placeholder="Search order # or email" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} />
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
          <option value="">All statuses</option>
          {["PENDING_PAYMENT", "PAID", "SENT_TO_SUPPLIER", "SUPPLIER_PROCESSING", "READY_FOR_PICKUP", "RECEIVED_AT_OFFICE", "SHIPPED_INTERNATIONALLY", "IN_TRANSIT", "DELIVERED", "CANCELLED"].map((s) => (
            <option key={s} value={s}>{s.replaceAll("_", " ")}</option>
          ))}
        </select>
      </div>

      {isLoading ? <p>Loading...</p> : (
        <table className="page-table">
          <thead><tr><th>Order #</th><th>Customer</th><th>Supplier(s)</th><th>Status</th><th>Total</th></tr></thead>
          <tbody>
            {data?.orders.map((o) => (
              <tr key={o.id}>
                <td><Link to={`/admin/orders/${o.id}`}>{o.order_number}</Link></td>
                <td>{o.customer_email}</td>
                <td>{o.supplier_names.join(", ")}</td>
                <td><span className="badge">{o.status.replaceAll("_", " ")}</span></td>
                <td>${o.total_amount_usd}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {data && data.total > data.page_size && (
        <div className="pagination">
          <button type="button" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>Previous</button>
          <span>Page {page}</span>
          <button type="button" disabled={page * data.page_size >= data.total} onClick={() => setPage((p) => p + 1)}>Next</button>
        </div>
      )}
    </div>
  );
}

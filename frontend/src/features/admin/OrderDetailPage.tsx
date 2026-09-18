import { useParams } from "react-router";
import { useAdminOrder, useTransitionOrderStatus } from "./hooks";

export function AdminOrderDetailPage() {
  const { orderId } = useParams<{ orderId: string }>();
  const { data: order, isLoading } = useAdminOrder(orderId);
  const transition = useTransitionOrderStatus(orderId!);

  if (isLoading) return <div className="page">Loading...</div>;
  if (!order) return <div className="page">Order not found.</div>;

  return (
    <div className="page">
      <h1>Order {order.order_number}</h1>
      <p className="badge">{order.status.replaceAll("_", " ")}</p>
      <p>{order.customer_name} · {order.customer_email}</p>
      <p className="muted">Tracking number: <strong>{order.tracking_number}</strong></p>

      <div className="link-row">
        {order.next_statuses.map((s) => (
          <button key={s} type="button" onClick={() => transition.mutate({ toStatus: s })}>
            Move to {s.replaceAll("_", " ")}
          </button>
        ))}
      </div>

      <h2>Items</h2>
      <ul className="order-item-list">
        {order.items.map((i) => (
          <li key={i.id}>
            <span>{i.quantity}× {i.product_name} {i.variant_label ? `(${i.variant_label})` : ""}</span>
            <span>${i.line_total_usd}</span>
          </li>
        ))}
      </ul>
      <p className="total">Total: ${order.total_amount_usd}{order.total_amount_kes ? ` (${order.total_amount_kes} KES)` : ""}</p>

      <h2>Supplier Orders</h2>
      <ul className="order-item-list">
        {order.supplier_orders.map((so) => (
          <li key={so.id}><span>{so.supplier_name}</span><span className="badge">{so.status}</span></li>
        ))}
        {order.supplier_orders.length === 0 && <li>None yet.</li>}
      </ul>

      <h2>Payments</h2>
      <ul className="order-item-list">
        {order.payments.map((p) => (
          <li key={p.id}><span>{p.provider} · {p.provider_ref ?? "-"}</span><span className="badge">{p.status}</span></li>
        ))}
        {order.payments.length === 0 && <li>None yet.</li>}
      </ul>

      <h2>Packages</h2>
      <ul className="order-item-list">
        {order.packages.map((p) => (
          <li key={p.id}>
            <span>{p.package_code} {p.consolidation_code ? `· ${p.consolidation_code}` : ""} {p.shipment_code ? `· ${p.shipment_code}` : ""}</span>
            <span className="badge">{p.status.replaceAll("_", " ")}</span>
          </li>
        ))}
        {order.packages.length === 0 && <li>Not yet received at the Vietnam warehouse.</li>}
      </ul>

      <h2>Status History</h2>
      <ul className="order-item-list">
        {order.status_history.map((h) => (
          <li key={h.id}>
            <span>{h.to_status.replaceAll("_", " ")} {h.note ? `- ${h.note}` : ""}</span>
            <span className="muted">{h.changed_by_name ?? "system"} · {new Date(h.created_at).toLocaleString()}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

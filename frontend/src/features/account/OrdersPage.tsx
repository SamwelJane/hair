import { useState } from "react";
import { Link } from "react-router";
import { useMyOrders } from "../orders/hooks";

export function OrdersPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useMyOrders(page);

  if (isLoading) return <div className="page">Loading...</div>;

  return (
    <div className="page narrow">
      <h1>Order History</h1>
      <ul className="order-list">
        {data?.orders.map((o) => (
          <li key={o.order_number}>
            <Link to={`/account/orders/${o.order_number}`}>
              <span>{o.order_number}</span>
              <span className="badge">{o.status.replaceAll("_", " ")}</span>
              <span>${o.total_amount_usd}</span>
            </Link>
          </li>
        ))}
        {data?.orders.length === 0 && <p>You haven't placed any orders yet.</p>}
      </ul>

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

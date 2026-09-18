import { useState } from "react";
import { Link, useParams } from "react-router";
import { useCancelOrder, useOrder, useRequestReturn, useSubmitReview } from "../orders/hooks";

// Mirrors order_state_machine.TRANSITIONS in backend - kept in sync by
// hand for now (see packages/shared-types for the equivalent pattern
// already used for status display groupings).
const CANCELLABLE_STATUSES = new Set([
  "PENDING_PAYMENT", "PAID", "SENT_TO_SUPPLIER", "SUPPLIER_PROCESSING", "READY_FOR_PICKUP", "RECEIVED_AT_OFFICE",
]);

export function OrderDetailPage() {
  const { orderNumber } = useParams<{ orderNumber: string }>();
  const { data: order, isLoading } = useOrder(orderNumber);
  const cancelOrder = useCancelOrder();
  const submitReview = useSubmitReview();
  const requestReturn = useRequestReturn();

  const [returnReason, setReturnReason] = useState("");
  const [returnSubmitted, setReturnSubmitted] = useState(false);
  const [reviewDrafts, setReviewDrafts] = useState<Record<string, { rating: number; body: string }>>({});
  const [submittedProductIds, setSubmittedProductIds] = useState<Set<string>>(new Set());

  if (isLoading) return <div className="page">Loading...</div>;
  if (!order) return <div className="page">Order not found.</div>;

  const canCancel = CANCELLABLE_STATUSES.has(order.status);
  const isDelivered = order.status === "DELIVERED";
  const uniqueProducts = [...new Map(order.items.map((i) => [i.product_id, i])).values()];

  async function handleReview(productId: string) {
    const draft = reviewDrafts[productId];
    if (!draft) return;
    await submitReview.mutateAsync({ order_id: order!.id, product_id: productId, rating: draft.rating, body: draft.body });
    setSubmittedProductIds((prev) => new Set(prev).add(productId));
  }

  async function handleReturn(e: React.FormEvent) {
    e.preventDefault();
    await requestReturn.mutateAsync({ order_id: order!.id, reason: returnReason });
    setReturnSubmitted(true);
  }

  return (
    <div className="page narrow">
      <h1>Order {order.order_number}</h1>
      <p className="badge">{order.status.replaceAll("_", " ")}</p>
      <p className="muted">
        Tracking number: <Link to={`/track/${order.tracking_number}`}>{order.tracking_number}</Link>
      </p>

      {order.packages.length > 0 && (
        <div className="callout">
          <h2>Packages</h2>
          <ul className="order-item-list">
            {order.packages.map((pkg) => (
              <li key={pkg.package_code}>
                <span>{pkg.package_code}</span>
                <span className="badge">{pkg.status.replaceAll("_", " ")}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <ul className="order-item-list">
        {order.items.map((item, idx) => (
          <li key={idx}>
            <Link to={`/products/${item.product_slug}`}>{item.quantity}× {item.product_name}</Link>
            {item.variant_label && <span className="muted"> ({item.variant_label})</span>}
            <span>${item.line_total_usd}</span>
          </li>
        ))}
      </ul>
      <p className="total">Total: ${order.total_amount_usd}</p>

      {canCancel && (
        <button type="button" className="danger" disabled={cancelOrder.isPending} onClick={() => cancelOrder.mutate(order.order_number)}>
          Cancel Order
        </button>
      )}
      {cancelOrder.isError && <p className="error">This order can no longer be cancelled.</p>}

      {isDelivered && (
        <div className="callout">
          <h2>Request a Return</h2>
          {returnSubmitted || requestReturn.isSuccess ? (
            <p>Your return request has been submitted.</p>
          ) : (
            <form onSubmit={handleReturn}>
              <textarea
                required
                placeholder="Tell us why you'd like to return this order"
                value={returnReason}
                onChange={(e) => setReturnReason(e.target.value)}
              />
              <button type="submit" disabled={requestReturn.isPending}>Request Return</button>
              {requestReturn.isError && <p className="error">Could not submit your return request.</p>}
            </form>
          )}
        </div>
      )}

      {isDelivered && (
        <div className="callout">
          <h2>Reviews</h2>
          {uniqueProducts.map((item) => {
            const done = submittedProductIds.has(item.product_id);
            const draft = reviewDrafts[item.product_id] ?? { rating: 5, body: "" };
            return (
              <div key={item.product_id} className="review-form">
                <p><strong>{item.product_name}</strong></p>
                {done ? (
                  <p className="muted">Thanks for your review!</p>
                ) : (
                  <>
                    <select
                      value={draft.rating}
                      onChange={(e) => setReviewDrafts((prev) => ({ ...prev, [item.product_id]: { ...draft, rating: Number(e.target.value) } }))}
                    >
                      {[5, 4, 3, 2, 1].map((n) => <option key={n} value={n}>{n} / 5</option>)}
                    </select>
                    <textarea
                      placeholder="Share your thoughts about this product"
                      value={draft.body}
                      onChange={(e) => setReviewDrafts((prev) => ({ ...prev, [item.product_id]: { ...draft, body: e.target.value } }))}
                    />
                    <button type="button" disabled={submitReview.isPending || !draft.body} onClick={() => void handleReview(item.product_id)}>
                      Submit Review
                    </button>
                  </>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

import { useState } from "react";
import { useAdminReturns, useResolveReturn } from "./hooks";

export function AdminReturnsPage() {
  const { data: returns, isLoading } = useAdminReturns();
  const resolve = useResolveReturn();
  const [refundAmounts, setRefundAmounts] = useState<Record<string, string>>({});

  if (isLoading) return <div className="page">Loading...</div>;

  return (
    <div className="page">
      <h1>Returns</h1>
      <div className="address-list">
        {returns?.map((r) => (
          <div key={r.id} className="address-card">
            <div className="link-row">
              <strong>{r.order_number}</strong>
              <span>{r.customer_email}</span>
              <span className="badge">{r.status}</span>
            </div>
            <p className="muted">{r.reason}</p>
            {r.resolved_by_name && <p className="muted">Resolved by {r.resolved_by_name}</p>}
            {r.status === "REQUESTED" && (
              <div className="link-row">
                <input
                  placeholder="Refund amount (USD)"
                  value={refundAmounts[r.id] ?? ""}
                  onChange={(e) => setRefundAmounts((prev) => ({ ...prev, [r.id]: e.target.value }))}
                />
                <button type="button" onClick={() => resolve.mutate({ returnId: r.id, status: "APPROVED", refundAmountUsd: refundAmounts[r.id] })}>Approve</button>
                <button type="button" onClick={() => resolve.mutate({ returnId: r.id, status: "REFUNDED", refundAmountUsd: refundAmounts[r.id] })}>Mark Refunded</button>
                <button type="button" className="danger" onClick={() => resolve.mutate({ returnId: r.id, status: "REJECTED" })}>Reject</button>
              </div>
            )}
          </div>
        ))}
        {returns?.length === 0 && <p>No return requests.</p>}
      </div>
    </div>
  );
}

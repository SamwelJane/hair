import { useState } from "react";
import { useSupplierOrders, useUpdateSupplierOrderStatus } from "./hooks";

const NEXT_STATUS: Record<string, string[]> = {
  SENT: ["ACKNOWLEDGED", "DECLINED"],
  ACKNOWLEDGED: ["IN_PRODUCTION", "DECLINED"],
  IN_PRODUCTION: ["READY"],
  READY: [],
  DECLINED: [],
};

export function SupplierOrdersPage() {
  const { data: orders, isLoading } = useSupplierOrders();
  const updateStatus = useUpdateSupplierOrderStatus();
  const [etaDays, setEtaDays] = useState<Record<string, string>>({});
  const [declineReasons, setDeclineReasons] = useState<Record<string, string>>({});

  if (isLoading) return <div className="page">Loading...</div>;

  return (
    <div className="page">
      <h1>Incoming Orders</h1>
      <div className="address-list">
        {orders?.map((so) => {
          const next = NEXT_STATUS[so.status] ?? [];
          return (
            <div key={so.id} className="address-card">
              <div className="link-row">
                <strong>{so.order_number}</strong>
                <span>{so.customer_name}</span>
                <span className="badge">{so.status.replaceAll("_", " ")}</span>
              </div>
              <p className="muted">{so.items.map((i) => `${i.quantity}× ${i.product_name}`).join(", ")}</p>
              {so.eta_days != null && <p className="muted">ETA given: {so.eta_days} day(s)</p>}
              {so.decline_reason && <p className="error">Declined: {so.decline_reason}</p>}

              <div className="link-row">
                {next.includes("ACKNOWLEDGED") && (
                  <>
                    <input
                      type="number"
                      placeholder="ETA (days)"
                      value={etaDays[so.id] ?? ""}
                      onChange={(e) => setEtaDays((prev) => ({ ...prev, [so.id]: e.target.value }))}
                    />
                    <button
                      type="button"
                      onClick={() =>
                        updateStatus.mutate({ supplierOrderId: so.id, toStatus: "ACKNOWLEDGED", etaDays: Number(etaDays[so.id]) || undefined })
                      }
                    >
                      Acknowledge
                    </button>
                  </>
                )}
                {next.includes("IN_PRODUCTION") && (
                  <button type="button" onClick={() => updateStatus.mutate({ supplierOrderId: so.id, toStatus: "IN_PRODUCTION" })}>
                    Mark In Production
                  </button>
                )}
                {next.includes("READY") && (
                  <button type="button" onClick={() => updateStatus.mutate({ supplierOrderId: so.id, toStatus: "READY" })}>
                    Mark Ready
                  </button>
                )}
                {next.includes("DECLINED") && (
                  <>
                    <input
                      placeholder="Reason for declining"
                      value={declineReasons[so.id] ?? ""}
                      onChange={(e) => setDeclineReasons((prev) => ({ ...prev, [so.id]: e.target.value }))}
                    />
                    <button
                      type="button"
                      className="danger"
                      disabled={!declineReasons[so.id]}
                      onClick={() => updateStatus.mutate({ supplierOrderId: so.id, toStatus: "DECLINED", declineReason: declineReasons[so.id] })}
                    >
                      Decline
                    </button>
                  </>
                )}
              </div>
            </div>
          );
        })}
        {orders?.length === 0 && <p>No orders yet.</p>}
      </div>
    </div>
  );
}

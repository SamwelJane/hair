import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

/** Admin Promotions Page — /admin/promotions
 *
 * Admins can:
 *  - View all promotion requests across all suppliers, filtered by status
 *  - Approve a PENDING request (setting start date + duration)
 *  - Reject a PENDING request (with required admin notes)
 */

const SLOT_LABELS: Record<string, string> = {
  HERO_BANNER: "🖼️ Hero Banner",
  FLASH_DEAL: "⚡ Flash Deal",
  CATEGORY_TOP: "🔝 Category Top",
  TRENDING_BADGE: "🔥 Trending Badge",
};

const STATUS_COLORS: Record<string, string> = {
  PENDING: "promo-status--pending",
  APPROVED: "promo-status--approved",
  ACTIVE: "promo-status--active",
  REJECTED: "promo-status--rejected",
  EXPIRED: "promo-status--expired",
};

function authHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
  };
}

function fetchAllPromotions(status: string) {
  const q = status ? `?status=${status}` : "";
  return fetch(`/api/admin/promotions${q}`, { headers: authHeaders() }).then((r) => r.json());
}

type Promotion = {
  id: string;
  supplier_name: string;
  product_name: string;
  slot_type: string;
  rate_usd: string;
  duration_days: number;
  status: string;
  start_date: string | null;
  end_date: string | null;
  custom_headline: string | null;
  admin_notes: string | null;
  reviewed_by_name: string | null;
  impressions_count: number;
  clicks_count: number;
  orders_count: number;
  created_at: string;
};

export function AdminPromotionsPage() {
  const queryClient = useQueryClient();
  const [filterStatus, setFilterStatus] = useState("PENDING");
  const [actionPromo, setActionPromo] = useState<Promotion | null>(null);
  const [actionType, setActionType] = useState<"approve" | "reject" | null>(null);
  const [adminNotes, setAdminNotes] = useState("");
  const [startDate, setStartDate] = useState("");
  const [durationDays, setDurationDays] = useState(7);

  const { data: promotions = [], isLoading } = useQuery({
    queryKey: ["admin-promotions", filterStatus],
    queryFn: () => fetchAllPromotions(filterStatus),
  });

  const approveMutation = useMutation({
    mutationFn: async ({ id, notes, start, days }: { id: string; notes: string; start: string; days: number }) => {
      const res = await fetch(`/api/admin/promotions/${id}/approve`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          admin_notes: notes || null,
          start_date: start || null,
          duration_days: days,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin-promotions"] });
      setActionPromo(null);
      setActionType(null);
      setAdminNotes("");
    },
  });

  const rejectMutation = useMutation({
    mutationFn: async ({ id, notes }: { id: string; notes: string }) => {
      const res = await fetch(`/api/admin/promotions/${id}/reject`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ admin_notes: notes }),
      });
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin-promotions"] });
      setActionPromo(null);
      setActionType(null);
      setAdminNotes("");
    },
  });

  function openApprove(promo: Promotion) {
    setActionPromo(promo);
    setActionType("approve");
    setAdminNotes("");
    setStartDate("");
    setDurationDays(promo.duration_days);
  }

  function openReject(promo: Promotion) {
    setActionPromo(promo);
    setActionType("reject");
    setAdminNotes("");
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Supplier Promotions</h1>
      </div>

      {/* Filter bar */}
      <div className="promo-filter">
        {["", "PENDING", "ACTIVE", "APPROVED", "REJECTED", "EXPIRED"].map((s) => (
          <button
            key={s}
            type="button"
            className={`btn btn--sm ${filterStatus === s ? "btn--primary" : "btn--outline"}`}
            onClick={() => setFilterStatus(s)}
          >
            {s || "All"}
          </button>
        ))}
      </div>

      {/* ── Action modal ──────────────────────────────────────────────────── */}
      {actionPromo && actionType && (
        <div className="modal-overlay" onClick={() => { setActionPromo(null); setActionType(null); }}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h2>{actionType === "approve" ? "✅ Approve Promotion" : "❌ Reject Promotion"}</h2>
            <p><strong>Supplier:</strong> {actionPromo.supplier_name}</p>
            <p><strong>Product:</strong> {actionPromo.product_name}</p>
            <p><strong>Slot:</strong> {SLOT_LABELS[actionPromo.slot_type] ?? actionPromo.slot_type}</p>

            {actionType === "approve" && (
              <>
                <label className="form-label">
                  Start Date (leave blank for immediate)
                  <input type="datetime-local" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
                </label>
                <label className="form-label">
                  Duration (days)
                  <input
                    type="number"
                    min={7}
                    max={90}
                    step={7}
                    value={durationDays}
                    onChange={(e) => setDurationDays(Number(e.target.value))}
                  />
                </label>
              </>
            )}

            <label className="form-label">
              Admin Notes {actionType === "reject" ? "(required)" : "(optional)"}
              <textarea
                required={actionType === "reject"}
                rows={3}
                value={adminNotes}
                onChange={(e) => setAdminNotes(e.target.value)}
                placeholder={actionType === "reject" ? "Reason for rejection…" : "Optional notes for the supplier…"}
              />
            </label>

            <div className="modal-actions">
              <button
                type="button"
                className={`btn ${actionType === "approve" ? "btn--primary" : "btn--danger"}`}
                disabled={approveMutation.isPending || rejectMutation.isPending}
                onClick={() => {
                  if (actionType === "approve") {
                    approveMutation.mutate({ id: actionPromo.id, notes: adminNotes, start: startDate, days: durationDays });
                  } else {
                    if (!adminNotes.trim()) return;
                    rejectMutation.mutate({ id: actionPromo.id, notes: adminNotes });
                  }
                }}
              >
                {actionType === "approve" ? "Approve & Activate" : "Reject Request"}
              </button>
              <button type="button" className="btn btn--outline" onClick={() => { setActionPromo(null); setActionType(null); }}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Promotions table ─────────────────────────────────────────────── */}
      {isLoading ? (
        <p className="loading">Loading…</p>
      ) : (promotions as Promotion[]).length === 0 ? (
        <div className="empty-state">
          <p>No promotion requests {filterStatus ? `with status ${filterStatus}` : ""}.</p>
        </div>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Supplier</th>
                <th>Product</th>
                <th>Slot</th>
                <th>Rate</th>
                <th>Duration</th>
                <th>Status</th>
                <th>Performance</th>
                <th>Submitted</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {(promotions as Promotion[]).map((p) => (
                <tr key={p.id}>
                  <td>{p.supplier_name}</td>
                  <td>{p.product_name}</td>
                  <td>{SLOT_LABELS[p.slot_type] ?? p.slot_type}</td>
                  <td>${p.rate_usd}/7d</td>
                  <td>{p.duration_days}d</td>
                  <td>
                    <span className={`promo-status ${STATUS_COLORS[p.status] ?? ""}`}>{p.status}</span>
                  </td>
                  <td className="promo-stats">
                    👁️{p.impressions_count} 🖱️{p.clicks_count} 🛒{p.orders_count}
                  </td>
                  <td>{new Date(p.created_at).toLocaleDateString()}</td>
                  <td className="action-cell">
                    {p.status === "PENDING" && (
                      <>
                        <button type="button" className="btn btn--sm btn--primary" onClick={() => openApprove(p)}>
                          Approve
                        </button>
                        <button type="button" className="btn btn--sm btn--danger" onClick={() => openReject(p)}>
                          Reject
                        </button>
                      </>
                    )}
                    {p.admin_notes && <span className="promo-note" title={p.admin_notes}>📝</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}


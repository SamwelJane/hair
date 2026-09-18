import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

/** Supplier Promotions Page — /supplier/promotions
 *
 * Suppliers can:
 *  - View all their promotion requests and statuses
 *  - Submit a new promotion request for a slot (HERO_BANNER, FLASH_DEAL, etc.)
 *
 * Rate card (per 7 days, USD):
 *  HERO_BANNER    $150   FLASH_DEAL     $80
 *  CATEGORY_TOP   $50    TRENDING_BADGE $30
 */

const RATE_CARD: Record<string, number> = {
  HERO_BANNER: 150,
  FLASH_DEAL: 80,
  CATEGORY_TOP: 50,
  TRENDING_BADGE: 30,
};

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

interface SupplierPromotion {
  id: string;
  product_id: string;
  product_name: string;
  slot_type: string;
  rate_usd: string;
  duration_days: number;
  status: string;
  start_date?: string | null;
  end_date?: string | null;
  banner_image_url?: string | null;
  custom_headline?: string | null;
  admin_notes?: string | null;
  impressions_count: number;
  clicks_count: number;
  orders_count: number;
  created_at: string;
}

function fetchMyPromotions(): Promise<SupplierPromotion[]> {
  return fetch("/api/supplier/promotions", {
    headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` },
  }).then((r) => r.json());
}

function fetchMyProducts() {
  return fetch("/api/supplier/products", {
    headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` },
  }).then((r) => r.json());
}

export function SupplierPromotionsPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    product_id: "",
    slot_type: "FLASH_DEAL",
    duration_days: 7,
    custom_headline: "",
    banner_image_url: "",
  });

  const { data: promotions = [], isLoading } = useQuery<SupplierPromotion[]>({
    queryKey: ["supplier-promotions"],
    queryFn: fetchMyPromotions,
  });

  const { data: products = [] } = useQuery({
    queryKey: ["supplier-products"],
    queryFn: fetchMyProducts,
  });

  const submitMutation = useMutation({
    mutationFn: async (payload: typeof form) => {
      const res = await fetch("/api/supplier/promotions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
        body: JSON.stringify({
          ...payload,
          duration_days: Number(payload.duration_days),
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["supplier-promotions"] });
      setShowForm(false);
      setForm({ product_id: "", slot_type: "FLASH_DEAL", duration_days: 7, custom_headline: "", banner_image_url: "" });
    },
  });

  const estimatedCost = ((RATE_CARD[form.slot_type] ?? 50) * Math.ceil(form.duration_days / 7)).toFixed(0);

  return (
    <div className="page">
      <div className="page-header">
        <h1>My Promotions</h1>
        <button type="button" className="btn btn--primary" onClick={() => setShowForm((s) => !s)}>
          {showForm ? "Cancel" : "✚ Request Promotion"}
        </button>
      </div>

      {/* ── Request Form ────────────────────────────────────────────────── */}
      {showForm && (
        <form
          className="promo-form card"
          onSubmit={(e) => {
            e.preventDefault();
            submitMutation.mutate(form);
          }}
        >
          <h2>New Promotion Request</h2>

          <label className="form-label">
            Product
            <select
              required
              value={form.product_id}
              onChange={(e) => setForm((f) => ({ ...f, product_id: e.target.value }))}
            >
              <option value="">Select a product…</option>
              {Array.isArray(products?.products ?? products) &&
                (products?.products ?? products).map((p: { id: string; name: string }) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
            </select>
          </label>

          <label className="form-label">
            Placement Slot
            <select value={form.slot_type} onChange={(e) => setForm((f) => ({ ...f, slot_type: e.target.value }))}>
              {Object.entries(SLOT_LABELS).map(([key, label]) => (
                <option key={key} value={key}>
                  {label} — ${RATE_CARD[key]}/7 days
                </option>
              ))}
            </select>
          </label>

          <label className="form-label">
            Duration (days)
            <input
              type="number"
              min={7}
              max={90}
              step={7}
              value={form.duration_days}
              onChange={(e) => setForm((f) => ({ ...f, duration_days: Number(e.target.value) }))}
            />
          </label>

          <label className="form-label">
            Custom Headline (optional)
            <input
              type="text"
              maxLength={120}
              placeholder="e.g. Summer Sale — 10% OFF!"
              value={form.custom_headline}
              onChange={(e) => setForm((f) => ({ ...f, custom_headline: e.target.value }))}
            />
          </label>

          <label className="form-label">
            Banner Image URL (optional)
            <input
              type="url"
              placeholder="https://…"
              value={form.banner_image_url}
              onChange={(e) => setForm((f) => ({ ...f, banner_image_url: e.target.value }))}
            />
          </label>

          <p className="promo-form__cost">
            💰 Estimated cost: <strong>${estimatedCost}</strong> for {form.duration_days} days
          </p>

          {submitMutation.isError && (
            <p className="form-error">Error: {String(submitMutation.error)}</p>
          )}

          <button type="submit" className="btn btn--primary" disabled={submitMutation.isPending}>
            {submitMutation.isPending ? "Submitting…" : "Submit Request"}
          </button>
        </form>
      )}

      {/* ── Promotions List ──────────────────────────────────────────────── */}
      {isLoading ? (
        <p className="loading">Loading promotions…</p>
      ) : promotions.length === 0 ? (
        <div className="empty-state">
          <p>You haven't requested any promotions yet.</p>
          <p>Boost your product visibility with a Hero Banner or Flash Deal placement!</p>
        </div>
      ) : (
        <div className="promo-list">
          {promotions.map((p) => (
            <div key={p.id} className="promo-card card">
              <div className="promo-card__header">
                <span className="promo-card__slot">{SLOT_LABELS[p.slot_type] ?? p.slot_type}</span>
                <span className={`promo-status ${STATUS_COLORS[p.status] ?? ""}`}>
                  {p.status}
                </span>
              </div>
              <p className="promo-card__product"><strong>{p.product_name}</strong></p>
              {p.custom_headline ? <p className="promo-card__headline">"{p.custom_headline}"</p> : null}
              <div className="promo-card__meta">
                <span>Rate: ${p.rate_usd}/7 days</span>
                <span>Duration: {p.duration_days} days</span>
                {p.start_date && p.end_date ? (
                  <span>Active: {new Date(p.start_date).toLocaleDateString()} – {new Date(p.end_date).toLocaleDateString()}</span>
                ) : null}
              </div>
              {p.admin_notes ? (
                <p className="promo-card__notes">Admin notes: {p.admin_notes}</p>
              ) : null}
              <div className="promo-card__stats">
                👁️ {p.impressions_count} impressions &nbsp;
                🖱️ {p.clicks_count} clicks &nbsp;
                🛒 {p.orders_count} orders
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


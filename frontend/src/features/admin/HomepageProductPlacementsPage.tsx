import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";
import { useAdminPlacements, useCreatePlacement, useDeletePlacement, useUpdatePlacement } from "./hooks";

function useProductSearch(q: string) {
  return useQuery({
    queryKey: ["admin-product-search", q],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/products", { params: { query: { q: q || undefined } } });
      if (error) throw error;
      return data;
    },
    enabled: q.length > 1,
  });
}

const EMPTY_FORM = {
  product_id: "", section: "FEATURED" as "FEATURED" | "DEAL", sale_price_usd: "", starts_at: "", ends_at: "",
  sort_order: 0, is_active: true,
};

export function AdminHomepageProductPlacementsPage() {
  const { data: placements, isLoading } = useAdminPlacements();
  const createPlacement = useCreatePlacement();
  const updatePlacement = useUpdatePlacement();
  const deletePlacement = useDeletePlacement();

  const [form, setForm] = useState(EMPTY_FORM);
  const [productQuery, setProductQuery] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const { data: productResults } = useProductSearch(productQuery);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    await createPlacement.mutateAsync({
      product_id: form.product_id,
      section: form.section,
      sale_price_usd: form.section === "DEAL" && form.sale_price_usd ? form.sale_price_usd : null,
      starts_at: form.starts_at || null,
      ends_at: form.ends_at || null,
      sort_order: form.sort_order,
      is_active: form.is_active,
    });
    setForm(EMPTY_FORM);
    setProductQuery("");
  }

  async function handleUpdate(e: React.FormEvent) {
    e.preventDefault();
    if (!editingId) return;
    await updatePlacement.mutateAsync({
      placementId: editingId,
      section: form.section,
      sale_price_usd: form.section === "DEAL" && form.sale_price_usd ? form.sale_price_usd : null,
      starts_at: form.starts_at || null,
      ends_at: form.ends_at || null,
      sort_order: form.sort_order,
      is_active: form.is_active,
    });
    setEditingId(null);
    setForm(EMPTY_FORM);
  }

  function startEdit(placement: NonNullable<typeof placements>[number]) {
    setEditingId(placement.id);
    setForm({
      product_id: placement.product_id,
      section: placement.section,
      sale_price_usd: placement.sale_price_usd ?? "",
      starts_at: placement.starts_at ?? "",
      ends_at: placement.ends_at ?? "",
      sort_order: placement.sort_order,
      is_active: placement.is_active,
    });
  }

  if (isLoading) return <div className="page">Loading...</div>;

  const featured = placements?.filter((p) => p.section === "FEATURED") ?? [];
  const deals = placements?.filter((p) => p.section === "DEAL") ?? [];

  return (
    <div className="page">
      <h1>Homepage Products</h1>
      <p className="muted">Feature products on the landing page, or run time-boxed deals with a sale price.</p>

      <div className="callout">
        <h2>Featured</h2>
        <ul className="order-item-list">
          {featured.map((p) => (
            <li key={p.id}>
              <span>{p.product_name} {!p.is_active && <span className="badge">Inactive</span>}</span>
              <span className="link-row">
                <button type="button" onClick={() => startEdit(p)}>Edit</button>
                <button type="button" className="danger" onClick={() => void deletePlacement.mutateAsync(p.id)}>Remove</button>
              </span>
            </li>
          ))}
          {featured.length === 0 && <li><span className="muted">None yet.</span></li>}
        </ul>
      </div>

      <div className="callout">
        <h2>Deals</h2>
        <ul className="order-item-list">
          {deals.map((p) => (
            <li key={p.id}>
              <span>
                {p.product_name} - ${p.sale_price_usd} {p.ends_at && <span className="muted">until {new Date(p.ends_at).toLocaleString()}</span>}
                {!p.is_active && <span className="badge">Inactive</span>}
              </span>
              <span className="link-row">
                <button type="button" onClick={() => startEdit(p)}>Edit</button>
                <button type="button" className="danger" onClick={() => void deletePlacement.mutateAsync(p.id)}>Remove</button>
              </span>
            </li>
          ))}
          {deals.length === 0 && <li><span className="muted">None yet.</span></li>}
        </ul>
      </div>

      <h2>{editingId ? "Edit Placement" : "Add Product to Homepage"}</h2>
      <form onSubmit={editingId ? handleUpdate : handleCreate} className="checkout-form">
        {!editingId && (
          <label>
            Search product
            <input
              placeholder="Type a product name..."
              value={productQuery}
              onChange={(e) => setProductQuery(e.target.value)}
            />
          </label>
        )}
        {!editingId && productResults && productResults.items.length > 0 && (
          <ul className="order-item-list">
            {productResults.items.map((product) => (
              <li key={product.id}>
                <button
                  type="button"
                  className={form.product_id === product.id ? "" : "danger"}
                  onClick={() => { setForm({ ...form, product_id: product.id }); setProductQuery(product.name); }}
                >
                  {product.name}
                </button>
              </li>
            ))}
          </ul>
        )}
        <label>Section
          <select value={form.section} onChange={(e) => setForm({ ...form, section: e.target.value as "FEATURED" | "DEAL" })}>
            <option value="FEATURED">Featured</option>
            <option value="DEAL">Deal</option>
          </select>
        </label>
        {form.section === "DEAL" && (
          <>
            <label>Sale price (USD)<input value={form.sale_price_usd} onChange={(e) => setForm({ ...form, sale_price_usd: e.target.value })} /></label>
            <label>Starts at<input type="datetime-local" value={form.starts_at} onChange={(e) => setForm({ ...form, starts_at: e.target.value })} /></label>
            <label>Ends at<input type="datetime-local" value={form.ends_at} onChange={(e) => setForm({ ...form, ends_at: e.target.value })} /></label>
          </>
        )}
        <label>Sort order<input type="number" value={form.sort_order} onChange={(e) => setForm({ ...form, sort_order: Number(e.target.value) })} /></label>
        <label className="checkbox-label">
          <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
          Active
        </label>
        <div className="link-row">
          <button type="submit" disabled={!form.product_id || createPlacement.isPending || updatePlacement.isPending}>
            {editingId ? "Save Changes" : "Add to Homepage"}
          </button>
          {editingId && (
            <button type="button" className="danger" onClick={() => { setEditingId(null); setForm(EMPTY_FORM); }}>
              Cancel
            </button>
          )}
        </div>
      </form>
    </div>
  );
}

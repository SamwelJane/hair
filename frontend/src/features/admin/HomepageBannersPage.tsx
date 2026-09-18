import { useState } from "react";
import {
  useAdminBanners,
  useCreateBanner,
  useDeleteBanner,
  useUpdateBanner,
  useUploadBannerImage,
} from "./hooks";

const EMPTY_FORM = { headline: "", subheadline: "", cta_label: "", cta_url: "", sort_order: 0, is_active: true };

export function AdminHomepageBannersPage() {
  const { data: banners, isLoading } = useAdminBanners();
  const createBanner = useCreateBanner();
  const updateBanner = useUpdateBanner();
  const deleteBanner = useDeleteBanner();
  const uploadImage = useUploadBannerImage();

  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState<string | null>(null);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    await createBanner.mutateAsync(form);
    setForm(EMPTY_FORM);
  }

  function startEdit(banner: NonNullable<typeof banners>[number]) {
    setEditingId(banner.id);
    setForm({
      headline: banner.headline,
      subheadline: banner.subheadline ?? "",
      cta_label: banner.cta_label ?? "",
      cta_url: banner.cta_url ?? "",
      sort_order: banner.sort_order,
      is_active: banner.is_active,
    });
  }

  async function handleUpdate(e: React.FormEvent) {
    e.preventDefault();
    if (!editingId) return;
    await updateBanner.mutateAsync({ bannerId: editingId, ...form });
    setEditingId(null);
    setForm(EMPTY_FORM);
  }

  if (isLoading) return <div className="page">Loading...</div>;

  return (
    <div className="page">
      <h1>Homepage Banners</h1>
      <p className="muted">Hero carousel slides shown at the top of the storefront landing page.</p>

      <ul className="order-item-list">
        {banners?.map((banner) => (
          <li key={banner.id}>
            <span>
              {banner.image_url ? <img src={banner.image_url} alt="" style={{ width: 60, height: 40, objectFit: "cover", marginRight: "0.75rem", verticalAlign: "middle" }} /> : null}
              {banner.headline} {!banner.is_active && <span className="badge">Inactive</span>}
            </span>
            <span className="link-row">
              <label className="link-button" style={{ cursor: "pointer" }}>
                Upload image
                <input
                  type="file"
                  accept="image/*"
                  style={{ display: "none" }}
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) void uploadImage.mutateAsync({ bannerId: banner.id, file });
                  }}
                />
              </label>
              <button type="button" onClick={() => startEdit(banner)}>Edit</button>
              <button type="button" className="danger" onClick={() => void deleteBanner.mutateAsync(banner.id)}>Delete</button>
            </span>
          </li>
        ))}
      </ul>

      <h2>{editingId ? "Edit Banner" : "New Banner"}</h2>
      <form onSubmit={editingId ? handleUpdate : handleCreate} className="checkout-form">
        <label>Headline<input required value={form.headline} onChange={(e) => setForm({ ...form, headline: e.target.value })} /></label>
        <label>Subheadline<input value={form.subheadline} onChange={(e) => setForm({ ...form, subheadline: e.target.value })} /></label>
        <label>CTA label<input value={form.cta_label} onChange={(e) => setForm({ ...form, cta_label: e.target.value })} /></label>
        <label>CTA link (e.g. /products)<input value={form.cta_url} onChange={(e) => setForm({ ...form, cta_url: e.target.value })} /></label>
        <label>Sort order<input type="number" value={form.sort_order} onChange={(e) => setForm({ ...form, sort_order: Number(e.target.value) })} /></label>
        <label className="checkbox-label">
          <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
          Active
        </label>
        <div className="link-row">
          <button type="submit" disabled={createBanner.isPending || updateBanner.isPending}>
            {editingId ? "Save Changes" : "Create Banner"}
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

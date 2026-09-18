import { useState } from "react";
import {
  useAdminCategories,
  useCreateCategory,
  useDeleteCategory,
  useUpdateCategory,
  useUploadCategoryImage,
} from "./hooks";

export function AdminCategoriesPage() {
  const { data: categories, isLoading } = useAdminCategories();
  const createCategory = useCreateCategory();
  const deleteCategory = useDeleteCategory();
  const updateCategory = useUpdateCategory();
  const uploadImage = useUploadCategoryImage();
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({ name: "", is_featured: false, sort_order: 0 });

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    await createCategory.mutateAsync(name);
    setName("");
  }

  async function handleDelete(id: string) {
    try {
      await deleteCategory.mutateAsync(id);
    } catch {
      setError("This category is in use and cannot be deleted.");
    }
  }

  function startEdit(category: NonNullable<typeof categories>[number]) {
    setEditingId(category.id);
    setEditForm({ name: category.name, is_featured: category.is_featured, sort_order: category.sort_order });
  }

  async function handleSaveEdit(e: React.FormEvent) {
    e.preventDefault();
    if (!editingId) return;
    await updateCategory.mutateAsync({ categoryId: editingId, ...editForm });
    setEditingId(null);
  }

  if (isLoading) return <div className="page">Loading...</div>;

  return (
    <div className="page narrow">
      <h1>Categories</h1>
      <p className="muted">Mark a category "Featured" with an image to show it in the homepage's Shop by Category grid.</p>
      {error && <p className="error">{error}</p>}
      <ul className="order-item-list">
        {categories?.map((c) => (
          <li key={c.id} style={{ display: "block" }}>
            <div className="link-row" style={{ justifyContent: "space-between" }}>
              <span>
                {c.image_url ? <img src={c.image_url} alt="" style={{ width: 32, height: 32, borderRadius: "50%", objectFit: "cover", marginRight: "0.5rem", verticalAlign: "middle" }} /> : null}
                {c.name} {c.is_featured && <span className="badge">Featured</span>}
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
                      if (file) void uploadImage.mutateAsync({ categoryId: c.id, file });
                    }}
                  />
                </label>
                <button type="button" onClick={() => startEdit(c)}>Edit</button>
                <button type="button" className="danger" onClick={() => void handleDelete(c.id)}>Delete</button>
              </span>
            </div>
            {editingId === c.id && (
              <form onSubmit={handleSaveEdit} className="link-row" style={{ marginTop: "0.5rem" }}>
                <input value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} />
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={editForm.is_featured}
                    onChange={(e) => setEditForm({ ...editForm, is_featured: e.target.checked })}
                  />
                  Featured
                </label>
                <input
                  type="number"
                  style={{ width: "5rem" }}
                  value={editForm.sort_order}
                  onChange={(e) => setEditForm({ ...editForm, sort_order: Number(e.target.value) })}
                />
                <button type="submit" disabled={updateCategory.isPending}>Save</button>
                <button type="button" className="danger" onClick={() => setEditingId(null)}>Cancel</button>
              </form>
            )}
          </li>
        ))}
      </ul>
      <form onSubmit={handleCreate} className="link-row" style={{ marginTop: "1rem" }}>
        <input placeholder="New category name" required value={name} onChange={(e) => setName(e.target.value)} />
        <button type="submit">Add</button>
      </form>
    </div>
  );
}

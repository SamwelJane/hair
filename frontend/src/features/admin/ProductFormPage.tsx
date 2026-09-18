import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";
import { tokenStore } from "../../lib/auth/tokenStore";
import { useCategories, useSuppliers } from "../catalog/hooks";

const HAIR_CATEGORIES = ["BULK_HAIR", "EXTENSION", "WIG", "CLOSURE", "FRONTAL", "MACHINE_WEFT"];

function useAdminProduct(productId: string | undefined) {
  return useQuery({
    queryKey: ["admin-product", productId],
    enabled: !!productId,
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/products/{product_id}", { params: { path: { product_id: productId! } } });
      if (error) throw error;
      return data;
    },
  });
}

export function AdminProductFormPage() {
  const { productId } = useParams<{ productId: string }>();
  const isEdit = !!productId;
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: product } = useAdminProduct(productId);
  const { data: categories } = useCategories();
  const { data: suppliers } = useSuppliers();

  const [name, setName] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [supplierId, setSupplierId] = useState("");
  const [description, setDescription] = useState("");
  const [countryOfOrigin, setCountryOfOrigin] = useState("");
  const [basePriceUsd, setBasePriceUsd] = useState("");
  const [hairCategory, setHairCategory] = useState("BULK_HAIR");
  const [processingTimeDays, setProcessingTimeDays] = useState(7);
  const [status, setStatus] = useState<"draft" | "published">("published");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (product) {
      setName(product.name);
      setCategoryId(product.category_id);
      setSupplierId(product.supplier_id);
      setDescription(product.description);
      setCountryOfOrigin(product.country_of_origin);
      setBasePriceUsd(product.base_price_usd);
      setHairCategory(product.hair_category);
      setProcessingTimeDays(product.processing_time_days);
      setStatus(product.status);
    }
  }, [product]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    const body = {
      name, category_id: categoryId, supplier_id: supplierId, description, country_of_origin: countryOfOrigin,
      base_price_usd: basePriceUsd, hair_category: hairCategory as never, status,
      processing_time_days: processingTimeDays, base_weight_grams: 200,
    };
    try {
      if (isEdit) {
        const { error: err } = await apiClient.PATCH("/admin/products/{product_id}", { params: { path: { product_id: productId! } }, body });
        if (err) throw err;
        void queryClient.invalidateQueries({ queryKey: ["admin-product", productId] });
      } else {
        const { data, error: err } = await apiClient.POST("/admin/products", { body });
        if (err) throw err;
        navigate(`/admin/products/${data.id}`);
        return;
      }
      void queryClient.invalidateQueries({ queryKey: ["admin-products"] });
    } catch {
      setError("Could not save this product. Check the required fields.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="page narrow">
      <h1>{isEdit ? "Edit Product" : "New Product"}</h1>
      <form onSubmit={handleSubmit} className="auth-form">
        <label>Name<input required value={name} onChange={(e) => setName(e.target.value)} /></label>
        <label>Category
          <select required value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
            <option value="">Select a category</option>
            {categories?.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </label>
        <label>Supplier
          <select required value={supplierId} onChange={(e) => setSupplierId(e.target.value)}>
            <option value="">Select a supplier</option>
            {suppliers?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </label>
        <label>Description<textarea required value={description} onChange={(e) => setDescription(e.target.value)} /></label>
        <label>Country of origin<input required maxLength={2} value={countryOfOrigin} onChange={(e) => setCountryOfOrigin(e.target.value.toUpperCase())} /></label>
        <label>Hair category
          <select value={hairCategory} onChange={(e) => setHairCategory(e.target.value)}>
            {HAIR_CATEGORIES.map((h) => <option key={h} value={h}>{h.replaceAll("_", " ")}</option>)}
          </select>
        </label>
        <label>Base price (USD)<input required type="number" step="0.01" value={basePriceUsd} onChange={(e) => setBasePriceUsd(e.target.value)} /></label>
        <label>Processing time (days)<input type="number" value={processingTimeDays} onChange={(e) => setProcessingTimeDays(Number(e.target.value))} /></label>
        <label>Status
          <select value={status} onChange={(e) => setStatus(e.target.value as "draft" | "published")}>
            <option value="draft">Draft</option>
            <option value="published">Published</option>
          </select>
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={saving}>{isEdit ? "Save Changes" : "Create Product"}</button>
      </form>

      {isEdit && product && <VariantsAndImages productId={productId!} product={product} />}
    </div>
  );
}

interface AdminVariant {
  id: string; sku: string; length: string | null; density: string | null; texture: string | null; color: string | null;
  price_delta_usd: string; stock_qty: number; weight_override_grams: number | null;
}
interface AdminImage { id: string; url: string }
interface AdminProductDetail { variants?: AdminVariant[]; images?: AdminImage[] }

function VariantsAndImages({ productId, product }: { productId: string; product: AdminProductDetail }) {
  const queryClient = useQueryClient();
  const [sku, setSku] = useState("");
  const [length, setLength] = useState("");
  const [priceDelta, setPriceDelta] = useState("0");
  const [stockQty, setStockQty] = useState(0);
  const [file, setFile] = useState<File | null>(null);

  function invalidate() {
    void queryClient.invalidateQueries({ queryKey: ["admin-product", productId] });
  }

  async function addVariant(e: React.FormEvent) {
    e.preventDefault();
    const { error } = await apiClient.POST("/admin/products/{product_id}/variants", {
      params: { path: { product_id: productId } },
      body: { sku, length: length || undefined, price_delta_usd: priceDelta, stock_qty: stockQty },
    });
    if (!error) { setSku(""); setLength(""); setPriceDelta("0"); setStockQty(0); invalidate(); }
  }

  async function updateStock(variantId: string, quantity: number) {
    // A partial-looking "just update stock" UI, but the API replaces the
    // whole variant record - every other field must be re-sent unchanged
    // or it gets wiped back to its default.
    const variant = product.variants!.find((v) => v.id === variantId)!;
    await apiClient.PATCH("/admin/products/{product_id}/variants/{variant_id}", {
      params: { path: { product_id: productId, variant_id: variantId } },
      body: {
        sku: variant.sku, length: variant.length ?? undefined, density: variant.density ?? undefined,
        texture: variant.texture ?? undefined, color: variant.color ?? undefined,
        price_delta_usd: variant.price_delta_usd, stock_qty: quantity,
        weight_override_grams: variant.weight_override_grams ?? undefined,
      },
    });
    invalidate();
  }

  async function deleteVariant(variantId: string) {
    await apiClient.DELETE("/admin/products/{product_id}/variants/{variant_id}", {
      params: { path: { product_id: productId, variant_id: variantId } },
    });
    invalidate();
  }

  async function uploadImage(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    const token = tokenStore.getState().accessToken;
    await fetch(`${tokenStore.apiBaseUrl}/admin/products/${productId}/images`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    setFile(null);
    invalidate();
  }

  async function deleteImage(imageId: string) {
    await apiClient.DELETE("/admin/products/{product_id}/images/{image_id}", {
      params: { path: { product_id: productId, image_id: imageId } },
    });
    invalidate();
  }

  return (
    <>
      <div className="callout">
        <h2>Images</h2>
        <div className="link-row">
          {product.images?.map((img) => (
            <div key={img.id}>
              <img src={img.url} alt="" style={{ width: 96, height: 96, objectFit: "cover", borderRadius: 6 }} />
              <button type="button" className="danger" onClick={() => void deleteImage(img.id)}>Remove</button>
            </div>
          ))}
        </div>
        <form onSubmit={uploadImage} className="link-row">
          <input type="file" accept="image/*" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          <button type="submit" disabled={!file}>Upload Image</button>
        </form>
      </div>

      <div className="callout">
        <h2>Variants</h2>
        <table className="page-table">
          <thead><tr><th>SKU</th><th>Length</th><th>Price Δ</th><th>Stock</th><th /></tr></thead>
          <tbody>
            {product.variants?.map((v) => (
              <tr key={v.id}>
                <td>{v.sku}</td>
                <td>{v.length ?? "-"}</td>
                <td>${v.price_delta_usd}</td>
                <td><input type="number" defaultValue={v.stock_qty} onBlur={(e) => void updateStock(v.id, Number(e.target.value))} /></td>
                <td><button type="button" className="danger" onClick={() => void deleteVariant(v.id)}>Delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
        <form onSubmit={addVariant} className="link-row">
          <input placeholder="SKU" required value={sku} onChange={(e) => setSku(e.target.value)} />
          <input placeholder="Length" value={length} onChange={(e) => setLength(e.target.value)} />
          <input placeholder="Price Δ" type="number" step="0.01" value={priceDelta} onChange={(e) => setPriceDelta(e.target.value)} />
          <input placeholder="Stock" type="number" value={stockQty} onChange={(e) => setStockQty(Number(e.target.value))} />
          <button type="submit">Add Variant</button>
        </form>
      </div>
    </>
  );
}

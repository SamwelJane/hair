import { useState } from "react";
import { Link, useParams } from "react-router";
import { useAddCartItem } from "../cart/hooks";
import { ProductCard } from "./ProductCard";
import { useProductDetail, useProducts } from "./hooks";

function humanize(value: string): string {
  return value.replaceAll("_", " ").toLowerCase().replace(/^./, (c) => c.toUpperCase());
}

export function ProductDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const { data: product, isLoading, isError } = useProductDetail(slug);
  const addItem = useAddCartItem();
  const [variantId, setVariantId] = useState<string>("");
  const [quantity, setQuantity] = useState(1);
  const [activeImage, setActiveImage] = useState(0);

  const { data: relatedData } = useProducts({ category: product?.category.slug });

  if (isLoading) return <div className="page">Loading...</div>;
  if (isError || !product) return <div className="page">Product not found.</div>;

  const images = product.images ?? [];
  const variants = product.variants ?? [];
  const reviews = product.reviews ?? [];
  const mainImage = images[activeImage] ?? images[0];
  const hasDeal = product.sale_price_usd != null;

  const specs: [string, string][] = [
    ["Origin", product.country_of_origin],
    ["Supplier", product.supplier.name],
    ["Processing time", `${product.processing_time_days} days`],
    ...(product.hair_length ? ([["Length", product.hair_length]] as [string, string][]) : []),
    ...(product.texture ? ([["Texture", product.texture]] as [string, string][]) : []),
    ...(product.color ? ([["Color", product.color]] as [string, string][]) : []),
    ...(product.quality ? ([["Quality", product.quality]] as [string, string][]) : []),
    ...(product.drawn_type ? ([["Drawn type", humanize(product.drawn_type)]] as [string, string][]) : []),
    ...(product.wig_construction ? ([["Construction", humanize(product.wig_construction)]] as [string, string][]) : []),
    ...(product.wig_cap_size ? ([["Cap size", product.wig_cap_size]] as [string, string][]) : []),
    ...(product.accessory_type ? ([["Accessory", humanize(product.accessory_type)]] as [string, string][]) : []),
  ];

  const relatedProducts = (relatedData?.items ?? []).filter((p) => p.id !== product.id).slice(0, 4);

  return (
    <div className="page">
      <p className="breadcrumb">
        <Link to="/">Home</Link> / <Link to="/products">Shop</Link> / <Link to={`/products?category=${product.category.slug}`}>{product.category.name}</Link> / {product.name}
      </p>

      <div className="product-detail">
        <div>
          <div className="product-detail-image">
            {mainImage ? <img src={mainImage.url} alt={product.name} /> : <div className="placeholder" />}
          </div>
          {images.length > 1 && (
            <div className="gallery-thumbs">
              {images.map((img, i) => (
                <button
                  key={img.id}
                  type="button"
                  className={`gallery-thumb${i === activeImage ? " active" : ""}`}
                  onClick={() => setActiveImage(i)}
                >
                  <img src={img.url} alt="" />
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="product-detail-info">
          <h1>{product.name}</h1>
          {hasDeal ? (
            <p className="price">
              <span className="price-strike">${product.base_price_usd}</span>
              <span className="price-sale">${product.sale_price_usd}</span>
            </p>
          ) : (
            <p className="price">from ${product.base_price_usd}</p>
          )}
          {product.average_rating != null && (
            <p className="rating">
              {"★".repeat(Math.round(product.average_rating))}
              {"☆".repeat(5 - Math.round(product.average_rating))} ({reviews.length} reviews)
            </p>
          )}
          <p>{product.description}</p>

          <p className="muted">Ships from Vietnam · Processing time: {product.processing_time_days} days</p>

          <dl className="product-meta">
            {specs.map(([label, value]) => (
              <div key={label} style={{ display: "contents" }}>
                <dt>{label}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>

          {variants.length > 0 && (
            <label>
              Variant
              <select value={variantId} onChange={(e) => setVariantId(e.target.value)}>
                <option value="">Standard</option>
                {variants.map((v) => (
                  <option key={v.id} value={v.id} disabled={v.stock_qty === 0}>
                    {[v.length, v.color, v.texture].filter(Boolean).join(" / ") || v.sku}
                    {v.stock_qty === 0 ? " (out of stock)" : ""}
                  </option>
                ))}
              </select>
            </label>
          )}

          <label>
            Quantity
            <input
              type="number"
              min={1}
              max={50}
              value={quantity}
              onChange={(e) => setQuantity(Number(e.target.value) || 1)}
            />
          </label>

          <button
            type="button"
            disabled={addItem.isPending}
            onClick={() =>
              addItem.mutate({ product_id: product.id, variant_id: variantId || null, quantity })
            }
          >
            Add to cart
          </button>
          {addItem.isSuccess && <p className="success">Added to cart.</p>}

          <h2>Reviews</h2>
          {reviews.length === 0 && <p>No reviews yet.</p>}
          <ul className="review-list">
            {reviews.map((r) => (
              <li key={r.id}>
                <strong>{r.user_name}</strong> — {"★".repeat(r.rating)}
                <p>{r.body}</p>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {relatedProducts.length > 0 && (
        <section className="callout">
          <div className="rail-header">
            <h2>You may also like</h2>
          </div>
          <div className="product-grid">
            {relatedProducts.map((p) => <ProductCard key={p.id} product={p} />)}
          </div>
        </section>
      )}
    </div>
  );
}

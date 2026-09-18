import { useEffect, useState } from "react";
import { Link } from "react-router";
import { useAddCartItem } from "../cart/hooks";

export type ProductCardData = {
  id: string;
  slug: string;
  name: string;
  image_url: string | null;
  base_price_usd: string;
  sale_price_usd?: string | null;
  average_rating: number | null;
  review_count: number;
  deal_ends_at?: string | null;
};

function formatCountdown(msRemaining: number): string {
  if (msRemaining <= 0) return "Deal ended";
  const totalMinutes = Math.floor(msRemaining / 60_000);
  const days = Math.floor(totalMinutes / (60 * 24));
  const hours = Math.floor((totalMinutes % (60 * 24)) / 60);
  const minutes = totalMinutes % 60;
  if (days > 0) return `${days}d ${hours}h left`;
  return `${hours}h ${minutes}m left`;
}

function DealCountdown({ endsAt }: { endsAt: string }) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 60_000);
    return () => clearInterval(id);
  }, []);

  return <p className="countdown">{formatCountdown(new Date(endsAt).getTime() - now)}</p>;
}

export function ProductCard({ product }: { product: ProductCardData }) {
  const addItem = useAddCartItem();
  const hasDeal = product.sale_price_usd != null;
  const discountPct = hasDeal
    ? Math.round((1 - Number(product.sale_price_usd) / Number(product.base_price_usd)) * 100)
    : null;

  return (
    <div className="product-card">
      <Link to={`/products/${product.slug}`}>
        <div className="product-card-image">
          {product.image_url ? <img src={product.image_url} alt={product.name} /> : <div className="placeholder" />}
          {discountPct != null && discountPct > 0 && <span className="deal-badge">-{discountPct}%</span>}
        </div>
        <h3>{product.name}</h3>
        {hasDeal ? (
          <p className="price">
            <span className="price-strike">${product.base_price_usd}</span>
            <span className="price-sale">${product.sale_price_usd}</span>
          </p>
        ) : (
          <p className="price">from ${product.base_price_usd}</p>
        )}
        {product.deal_ends_at && <DealCountdown endsAt={product.deal_ends_at} />}
        {product.average_rating != null && (
          <p className="rating">
            {"★".repeat(Math.round(product.average_rating))}
            {"☆".repeat(5 - Math.round(product.average_rating))} ({product.review_count})
          </p>
        )}
      </Link>
      <button
        type="button"
        disabled={addItem.isPending}
        onClick={() => addItem.mutate({ product_id: product.id, quantity: 1 })}
      >
        Add to cart
      </button>
    </div>
  );
}

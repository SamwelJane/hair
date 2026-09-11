import Link from "next/link";
import Image from "next/image";

export interface ProductCardData {
  slug: string;
  name: string;
  basePriceUsd: number;
  countryOfOrigin: string;
  imageUrl?: string;
  averageRating?: number | null;
  reviewCount?: number;
}

export function ProductCard({ product }: { product: ProductCardData }) {
  return (
    <Link
      href={`/products/${product.slug}`}
      className="group flex flex-col overflow-hidden rounded-lg border border-brand-border bg-brand-surface transition hover:shadow-lg"
    >
      <div className="relative aspect-square w-full bg-brand-accent-soft">
        {product.imageUrl ? (
          <Image
            src={product.imageUrl}
            alt={product.name}
            fill
            className="object-cover transition group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-sm text-brand-muted">
            No image
          </div>
        )}
      </div>
      <div className="flex flex-col gap-1 p-4">
        <h3 className="text-sm font-medium text-brand-ink">{product.name}</h3>
        <p className="text-sm font-semibold text-brand-accent">From ${product.basePriceUsd.toFixed(2)}</p>
        {product.averageRating != null && (
          <div className="flex items-center gap-1 text-xs text-brand-star">
            {"★".repeat(Math.round(product.averageRating))}
            {"☆".repeat(5 - Math.round(product.averageRating))}
            <span className="text-brand-muted">({product.reviewCount})</span>
          </div>
        )}
        <p className="text-xs text-brand-muted">Supplier: {product.countryOfOrigin}</p>
      </div>
    </Link>
  );
}

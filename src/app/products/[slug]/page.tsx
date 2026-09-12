import Image from "next/image";
import { notFound } from "next/navigation";
import { SiteHeader } from "@/components/storefront/SiteHeader";
import { SiteFooter } from "@/components/storefront/SiteFooter";
import { PriceCalculator } from "@/components/storefront/PriceCalculator";
import { getProductBySlug } from "@/lib/products/queries";
import { db } from "@/lib/db";

export default async function ProductDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const [product, shippingRules] = await Promise.all([
    getProductBySlug(slug),
    db.countryShippingRule.findMany({ orderBy: { countryName: "asc" } }),
  ]);

  if (!product) notFound();

  const mainImage = product.images[0];

  return (
    <>
      <SiteHeader />
      <main className="flex-1 bg-brand-bg">
        <div className="mx-auto grid max-w-6xl grid-cols-1 gap-10 px-6 py-10 md:grid-cols-2">
          <div className="flex flex-col gap-4">
            <div className="relative aspect-square w-full overflow-hidden rounded-lg bg-brand-accent-soft">
              {mainImage ? (
                <Image src={mainImage.url} alt={product.name} fill className="object-cover" />
              ) : (
                <div className="flex h-full items-center justify-center text-brand-muted">No image</div>
              )}
            </div>
            {product.images.length > 1 && (
              <div className="flex gap-2">
                {product.images.slice(1).map((img) => (
                  <div key={img.id} className="relative h-20 w-20 overflow-hidden rounded bg-brand-accent-soft">
                    <Image src={img.url} alt={product.name} fill className="object-cover" />
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <h1 className="text-2xl font-semibold text-brand-ink">{product.name}</h1>
            <p className="mt-2 text-sm text-brand-muted">{product.description}</p>
            <p className="mt-1 text-xs text-brand-muted">
              Country of origin: {product.countryOfOrigin} · Processing time: {product.processingTimeDays} days
            </p>

            <div className="mt-6">
              <PriceCalculator
                productId={product.id}
                productSlug={product.slug}
                productName={product.name}
                imageUrl={mainImage?.url}
                basePriceUsd={product.basePriceUsd.toNumber()}
                variants={product.variants.map((v) => ({
                  id: v.id,
                  label: [v.length, v.density, v.color, v.texture].filter(Boolean).join(" / ") || v.sku,
                  priceDeltaUsd: v.priceDeltaUsd.toNumber(),
                }))}
                countries={shippingRules.map((r) => ({ code: r.countryCode, name: r.countryName }))}
              />
            </div>

            {product.reviews.length > 0 && (
              <div className="mt-8">
                <h2 className="text-lg font-semibold text-brand-ink">Reviews</h2>
                <ul className="mt-3 flex flex-col gap-3">
                  {product.reviews.map((review) => (
                    <li key={review.id} className="rounded border border-brand-border bg-brand-surface p-3 text-sm">
                      <p className="font-medium text-brand-ink">{review.user.name} - {review.rating}/5</p>
                      <p className="text-brand-muted">{review.body}</p>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}

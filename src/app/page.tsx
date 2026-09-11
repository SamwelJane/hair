import Link from "next/link";
import { SiteHeader } from "@/components/storefront/SiteHeader";
import { SiteFooter } from "@/components/storefront/SiteFooter";
import { ProductCard } from "@/components/storefront/ProductCard";
import { FilterBar } from "@/components/storefront/FilterBar";
import { ProcessSteps } from "@/components/storefront/ProcessSteps";
import { InfoCards } from "@/components/storefront/InfoCards";
import {
  listPublishedProducts,
  listCategories,
  listActiveSuppliers,
  listVariantAttributeOptions,
  averageRating,
} from "@/lib/products/queries";

export default async function HomePage() {
  const [products, categories, suppliers, variantOptions] = await Promise.all([
    listPublishedProducts({ sort: "newest" }),
    listCategories(),
    listActiveSuppliers(),
    listVariantAttributeOptions(),
  ]);

  const featured = products.slice(0, 4);
  const allProducts = products.slice(0, 6);

  return (
    <>
      <SiteHeader />
      <main className="flex-1 bg-brand-bg">
        <section className="relative overflow-hidden px-6 py-24 text-white sm:py-32">
          <div
            className="absolute inset-0 bg-cover bg-center"
            style={{
              backgroundImage:
                "linear-gradient(90deg, rgba(33,26,22,0.88) 0%, rgba(33,26,22,0.35) 60%, rgba(33,26,22,0.1) 100%), url(https://images.unsplash.com/photo-1519699047748-de8e457a634e?q=80&w=1600&auto=format&fit=crop)",
            }}
          />
          <div className="relative mx-auto max-w-6xl">
            <h1 className="max-w-xl text-4xl font-bold sm:text-5xl">Discover Your Perfect Hair</h1>
            <p className="mt-4 max-w-md text-brand-dark-ink/85">
              Explore premium hair collections sourced from Vietnam, quality-checked at our office and
              shipped worldwide.
            </p>
            <Link
              href="/products"
              className="mt-8 inline-block rounded-full bg-white px-6 py-3 text-sm font-semibold text-brand-ink hover:bg-brand-accent-soft"
            >
              Shop Now
            </Link>
          </div>
        </section>

        <FilterBar
          options={{
            categories: categories.map((c) => ({ slug: c.slug, name: c.name })),
            suppliers: suppliers.map((s) => ({ id: s.id, name: s.name })),
            ...variantOptions,
          }}
          values={{}}
        />

        <section className="mx-auto max-w-6xl px-6 py-10">
          <h2 className="mb-6 text-2xl font-semibold text-brand-ink">Featured Products</h2>
          {featured.length === 0 ? (
            <p className="text-sm text-brand-muted">No products published yet.</p>
          ) : (
            <div className="grid grid-cols-2 gap-6 sm:grid-cols-3 lg:grid-cols-4">
              {featured.map((product) => (
                <ProductCard
                  key={product.id}
                  product={{
                    slug: product.slug,
                    name: product.name,
                    basePriceUsd: product.basePriceUsd.toNumber(),
                    countryOfOrigin: product.countryOfOrigin,
                    imageUrl: product.images[0]?.url,
                    averageRating: averageRating(product.reviews),
                    reviewCount: product.reviews.length,
                  }}
                />
              ))}
            </div>
          )}
        </section>

        <section className="mx-auto max-w-6xl px-6 pb-10">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-semibold text-brand-ink">All Hair Products</h2>
            <Link href="/products" className="text-sm font-medium text-brand-accent hover:underline">
              View All &rarr;
            </Link>
          </div>
          {allProducts.length === 0 ? (
            <p className="text-sm text-brand-muted">No products published yet.</p>
          ) : (
            <div className="grid grid-cols-2 gap-6 sm:grid-cols-3 lg:grid-cols-6">
              {allProducts.map((product) => (
                <ProductCard
                  key={product.id}
                  product={{
                    slug: product.slug,
                    name: product.name,
                    basePriceUsd: product.basePriceUsd.toNumber(),
                    countryOfOrigin: product.countryOfOrigin,
                    imageUrl: product.images[0]?.url,
                    averageRating: averageRating(product.reviews),
                    reviewCount: product.reviews.length,
                  }}
                />
              ))}
            </div>
          )}
        </section>

        <ProcessSteps />
        <InfoCards />
      </main>
      <SiteFooter />
    </>
  );
}

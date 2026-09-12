import { SiteHeader } from "@/components/storefront/SiteHeader";
import { SiteFooter } from "@/components/storefront/SiteFooter";
import { ProductCard } from "@/components/storefront/ProductCard";
import { FilterBar } from "@/components/storefront/FilterBar";
import {
  listPublishedProducts,
  listCategories,
  listActiveSuppliers,
  listVariantAttributeOptions,
  averageRating,
} from "@/lib/products/queries";

interface ProductsPageProps {
  searchParams: Promise<{
    category?: string;
    supplierId?: string;
    length?: string;
    texture?: string;
    color?: string;
    q?: string;
    minPrice?: string;
    maxPrice?: string;
    sort?: "newest" | "price_asc" | "price_desc";
  }>;
}

export default async function ProductsPage({ searchParams }: ProductsPageProps) {
  const params = await searchParams;
  const [products, categories, suppliers, variantOptions] = await Promise.all([
    listPublishedProducts({
      categorySlug: params.category,
      supplierId: params.supplierId,
      search: params.q,
      length: params.length,
      texture: params.texture,
      color: params.color,
      minPriceUsd: params.minPrice ? Number(params.minPrice) : undefined,
      maxPriceUsd: params.maxPrice ? Number(params.maxPrice) : undefined,
      sort: params.sort,
    }),
    listCategories(),
    listActiveSuppliers(),
    listVariantAttributeOptions(),
  ]);

  return (
    <>
      <SiteHeader />
      <main className="flex-1 bg-brand-bg">
        <div className="mx-auto max-w-6xl px-6 pt-10">
          <h1 className="text-2xl font-semibold text-brand-ink">All Hair Products</h1>
        </div>

        <FilterBar
          options={{
            categories: categories.map((c) => ({ slug: c.slug, name: c.name })),
            suppliers: suppliers.map((s) => ({ id: s.id, name: s.name })),
            ...variantOptions,
          }}
          values={params}
        />

        <div className="mx-auto max-w-6xl px-6 pb-10">
          {products.length === 0 ? (
            <p className="text-sm text-brand-muted">No products match your filters.</p>
          ) : (
            <div className="grid grid-cols-2 gap-6 sm:grid-cols-3 lg:grid-cols-4">
              {products.map((product) => (
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
        </div>
      </main>
      <SiteFooter />
    </>
  );
}

import { useSearchParams } from "react-router";
import { ProductCard } from "./ProductCard";
import { useCategories, useProductFacets, useProducts, useSuppliers, type ProductFilters } from "./hooks";

export function ProductsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const filters: ProductFilters = {
    category: searchParams.get("category") ?? undefined,
    supplier_id: searchParams.get("supplierId") ?? undefined,
    q: searchParams.get("q") ?? undefined,
    min_price: searchParams.get("minPrice") ?? undefined,
    max_price: searchParams.get("maxPrice") ?? undefined,
    length: searchParams.get("length") ?? undefined,
    texture: searchParams.get("texture") ?? undefined,
    color: searchParams.get("color") ?? undefined,
    sort: (searchParams.get("sort") as ProductFilters["sort"]) ?? undefined,
    page: Number(searchParams.get("page")) || 1,
  };

  const { data, isLoading, isError } = useProducts(filters);
  const { data: categories } = useCategories();
  const { data: suppliers } = useSuppliers();
  const { data: facets } = useProductFacets();

  function updateFilter(key: string, value: string) {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    if (key !== "page") next.delete("page");
    setSearchParams(next);
  }

  return (
    <div className="page">
      <h1>Shop</h1>

      <form className="filter-bar" onSubmit={(e) => e.preventDefault()}>
        <input
          type="search"
          placeholder="Search..."
          defaultValue={filters.q ?? ""}
          onBlur={(e) => updateFilter("q", e.target.value)}
        />
        <select value={filters.category ?? ""} onChange={(e) => updateFilter("category", e.target.value)}>
          <option value="">All categories</option>
          {categories?.map((c) => (
            <option key={c.id} value={c.slug}>{c.name}</option>
          ))}
        </select>
        <select value={filters.supplier_id ?? ""} onChange={(e) => updateFilter("supplierId", e.target.value)}>
          <option value="">All suppliers</option>
          {suppliers?.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
        <select value={filters.length ?? ""} onChange={(e) => updateFilter("length", e.target.value)}>
          <option value="">Any length</option>
          {facets?.lengths.map((l) => (
            <option key={l} value={l}>{l}</option>
          ))}
        </select>
        <select value={filters.texture ?? ""} onChange={(e) => updateFilter("texture", e.target.value)}>
          <option value="">Any texture</option>
          {facets?.textures.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
        <select value={filters.color ?? ""} onChange={(e) => updateFilter("color", e.target.value)}>
          <option value="">Any color</option>
          {facets?.colors.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <select value={filters.sort ?? "newest"} onChange={(e) => updateFilter("sort", e.target.value)}>
          <option value="newest">Newest</option>
          <option value="price_asc">Price: Low to High</option>
          <option value="price_desc">Price: High to Low</option>
        </select>
      </form>

      {isLoading && <p>Loading products...</p>}
      {isError && <p className="error">Could not load products.</p>}

      <div className="product-grid">
        {data?.items.map((product) => <ProductCard key={product.id} product={product} />)}
        {data?.items.length === 0 && <p>No products match your filters.</p>}
      </div>

      {data && data.total > data.page_size && (
        <div className="pagination">
          <button
            type="button"
            disabled={filters.page === 1}
            onClick={() => updateFilter("page", String((filters.page ?? 1) - 1))}
          >
            Previous
          </button>
          <span>Page {filters.page}</span>
          <button
            type="button"
            disabled={(filters.page ?? 1) * data.page_size >= data.total}
            onClick={() => updateFilter("page", String((filters.page ?? 1) + 1))}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

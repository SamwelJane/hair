"use client";

export interface FilterBarOptions {
  categories: { slug: string; name: string }[];
  suppliers: { id: string; name: string }[];
  lengths: string[];
  textures: string[];
  colors: string[];
}

export interface FilterBarValues {
  q?: string;
  category?: string;
  supplierId?: string;
  length?: string;
  texture?: string;
  color?: string;
  minPrice?: string;
  maxPrice?: string;
  sort?: string;
}

const PRICE_BANDS = [
  { label: "Any Price", min: "", max: "" },
  { label: "Under $50", min: "", max: "50" },
  { label: "$50 - $100", min: "50", max: "100" },
  { label: "$100 - $200", min: "100", max: "200" },
  { label: "$200+", min: "200", max: "" },
];

export function FilterBar({ options, values }: { options: FilterBarOptions; values: FilterBarValues }) {
  const priceValue = `${values.minPrice ?? ""}-${values.maxPrice ?? ""}`;

  return (
    <form action="/products" method="get" className="mx-auto flex max-w-6xl flex-wrap items-center gap-3 px-6 py-5 text-sm">
      <span className="font-medium text-brand-ink">Filter by:</span>

      <select name="supplierId" defaultValue={values.supplierId ?? ""} className="rounded-full border border-brand-border bg-brand-surface px-4 py-2 text-brand-ink">
        <option value="">Supplier</option>
        {options.suppliers.map((s) => (
          <option key={s.id} value={s.id}>{s.name}</option>
        ))}
      </select>

      <select name="category" defaultValue={values.category ?? ""} className="rounded-full border border-brand-border bg-brand-surface px-4 py-2 text-brand-ink">
        <option value="">Hair Type</option>
        {options.categories.map((c) => (
          <option key={c.slug} value={c.slug}>{c.name}</option>
        ))}
      </select>

      <select name="length" defaultValue={values.length ?? ""} className="rounded-full border border-brand-border bg-brand-surface px-4 py-2 text-brand-ink">
        <option value="">Length</option>
        {options.lengths.map((l) => (
          <option key={l} value={l}>{l}</option>
        ))}
      </select>

      <select name="texture" defaultValue={values.texture ?? ""} className="rounded-full border border-brand-border bg-brand-surface px-4 py-2 text-brand-ink">
        <option value="">Texture</option>
        {options.textures.map((t) => (
          <option key={t} value={t}>{t}</option>
        ))}
      </select>

      <select name="color" defaultValue={values.color ?? ""} className="rounded-full border border-brand-border bg-brand-surface px-4 py-2 text-brand-ink">
        <option value="">Color</option>
        {options.colors.map((c) => (
          <option key={c} value={c}>{c}</option>
        ))}
      </select>

      <select
        name="priceBand"
        defaultValue={priceValue}
        className="rounded-full border border-brand-border bg-brand-surface px-4 py-2 text-brand-ink"
        onChange={(e) => {
          const [min, max] = e.target.value.split("-");
          const form = e.target.form!;
          (form.elements.namedItem("minPrice") as HTMLInputElement).value = min;
          (form.elements.namedItem("maxPrice") as HTMLInputElement).value = max;
        }}
      >
        {PRICE_BANDS.map((band) => (
          <option key={band.label} value={`${band.min}-${band.max}`}>{band.label}</option>
        ))}
      </select>
      <input type="hidden" name="minPrice" defaultValue={values.minPrice ?? ""} />
      <input type="hidden" name="maxPrice" defaultValue={values.maxPrice ?? ""} />
      {values.q && <input type="hidden" name="q" value={values.q} />}

      <button type="submit" className="rounded-full bg-brand-accent px-5 py-2 font-medium text-white hover:bg-brand-accent-hover">
        Apply
      </button>
    </form>
  );
}

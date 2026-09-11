import { db } from "@/lib/db";

export interface ProductFilters {
  categorySlug?: string;
  supplierId?: string;
  search?: string;
  minPriceUsd?: number;
  maxPriceUsd?: number;
  length?: string;
  texture?: string;
  color?: string;
  sort?: "newest" | "price_asc" | "price_desc";
}

export function listPublishedProducts(filters: ProductFilters = {}) {
  const orderBy =
    filters.sort === "price_asc"
      ? { basePriceUsd: "asc" as const }
      : filters.sort === "price_desc"
        ? { basePriceUsd: "desc" as const }
        : { createdAt: "desc" as const };

  const variantFilter =
    filters.length || filters.texture || filters.color
      ? {
          variants: {
            some: {
              ...(filters.length ? { length: filters.length } : {}),
              ...(filters.texture ? { texture: filters.texture } : {}),
              ...(filters.color ? { color: filters.color } : {}),
            },
          },
        }
      : {};

  return db.product.findMany({
    where: {
      status: "published",
      ...(filters.categorySlug ? { category: { slug: filters.categorySlug } } : {}),
      ...(filters.supplierId ? { supplierId: filters.supplierId } : {}),
      ...(filters.search
        ? { name: { contains: filters.search, mode: "insensitive" as const } }
        : {}),
      ...(filters.minPriceUsd || filters.maxPriceUsd
        ? {
            basePriceUsd: {
              ...(filters.minPriceUsd ? { gte: filters.minPriceUsd } : {}),
              ...(filters.maxPriceUsd ? { lte: filters.maxPriceUsd } : {}),
            },
          }
        : {}),
      ...variantFilter,
    },
    include: {
      images: { orderBy: { sortOrder: "asc" }, take: 1 },
      supplier: true,
      category: true,
      reviews: { where: { status: "approved" }, select: { rating: true } },
    },
    orderBy,
  });
}

export function getProductBySlug(slug: string) {
  return db.product.findUnique({
    where: { slug },
    include: {
      images: { orderBy: { sortOrder: "asc" } },
      variants: true,
      supplier: true,
      category: true,
      reviews: { where: { status: "approved" }, include: { user: true }, orderBy: { createdAt: "desc" } },
    },
  });
}

export function listCategories() {
  return db.category.findMany({ orderBy: { name: "asc" } });
}

export function listActiveSuppliers() {
  return db.supplier.findMany({ where: { status: "active" }, orderBy: { name: "asc" } });
}

export async function listVariantAttributeOptions() {
  const variants = await db.productVariant.findMany({
    select: { length: true, texture: true, color: true },
  });

  const uniq = (values: (string | null)[]) => [...new Set(values.filter((v): v is string => !!v))].sort();

  return {
    lengths: uniq(variants.map((v) => v.length)),
    textures: uniq(variants.map((v) => v.texture)),
    colors: uniq(variants.map((v) => v.color)),
  };
}

export function averageRating(reviews: { rating: number }[]): number | null {
  if (reviews.length === 0) return null;
  return Math.round((reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length) * 10) / 10;
}

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export interface ProductFilters {
  category?: string;
  q?: string;
  sort?: "newest" | "price_asc" | "price_desc";
  page?: number;
}

export function useProducts(filters: ProductFilters) {
  return useQuery({
    queryKey: ["products", filters],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/products", { params: { query: filters } });
      if (error) throw error;
      return data;
    },
  });
}

export function useCategories() {
  return useQuery({
    queryKey: ["categories"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/categories", {});
      if (error) throw error;
      return data;
    },
    staleTime: 5 * 60_000,
  });
}

export function useProductDetail(slug: string | undefined) {
  return useQuery({
    queryKey: ["product", slug],
    enabled: !!slug,
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/products/{slug}", { params: { path: { slug: slug! } } });
      if (error) throw error;
      return data;
    },
  });
}

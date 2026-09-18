import { useMutation, useQuery } from "@tanstack/react-query";
import type { components } from "@hiar-business/api-client";
import { apiClient } from "../../lib/apiClient";

type CheckoutRequest = components["schemas"]["CheckoutRequest"];

interface CartLine {
  product_id: string;
  variant_id?: string | null;
  quantity: number;
}

export function useCheckoutSummary(
  items: CartLine[],
  countryCode: string,
  discountCode: string | undefined,
) {
  return useQuery({
    queryKey: ["checkout-summary", items, countryCode, discountCode],
    enabled: items.length > 0 && countryCode.length === 2,
    queryFn: async () => {
      const { data, error } = await apiClient.POST("/checkout/summary", {
        body: { items, country_code: countryCode, discount_code: discountCode || undefined },
      });
      if (error) throw error;
      return data;
    },
    retry: false,
  });
}

export function useSubmitCheckout() {
  return useMutation({
    mutationFn: async (body: CheckoutRequest) => {
      const { data, error } = await apiClient.POST("/orders", { body });
      if (error) throw error;
      return data;
    },
  });
}

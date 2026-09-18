import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";
import { getGuestCartToken, setGuestCartToken } from "../../lib/cart/guestCartToken";

const CART_QUERY_KEY = ["cart"];

async function guestHeaders(): Promise<Record<string, string>> {
  const token = await getGuestCartToken();
  return token ? { "X-Guest-Cart-Token": token } : {};
}

async function captureGuestToken(response: Response): Promise<void> {
  const token = response.headers.get("X-Guest-Cart-Token");
  if (token) await setGuestCartToken(token);
}

export function useCart() {
  return useQuery({
    queryKey: CART_QUERY_KEY,
    queryFn: async () => {
      const { data, response, error } = await apiClient.GET("/cart", { headers: await guestHeaders() });
      await captureGuestToken(response);
      if (error) throw error;
      return data;
    },
    staleTime: 10_000,
  });
}

export function useAddCartItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: { product_id: string; variant_id?: string | null; quantity: number }) => {
      const { data, response, error } = await apiClient.POST("/cart/items", { body, headers: await guestHeaders() });
      await captureGuestToken(response);
      if (error) throw error;
      return data;
    },
    onSuccess: (data) => queryClient.setQueryData(CART_QUERY_KEY, data),
  });
}

export function useUpdateCartItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ itemId, quantity }: { itemId: string; quantity: number }) => {
      const { data, response, error } = await apiClient.PATCH("/cart/items/{item_id}", {
        params: { path: { item_id: itemId } },
        body: { quantity },
        headers: await guestHeaders(),
      });
      await captureGuestToken(response);
      if (error) throw error;
      return data;
    },
    onSuccess: (data) => queryClient.setQueryData(CART_QUERY_KEY, data),
  });
}

export function useRemoveCartItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (itemId: string) => {
      const { data, response, error } = await apiClient.DELETE("/cart/items/{item_id}", {
        params: { path: { item_id: itemId } },
        headers: await guestHeaders(),
      });
      await captureGuestToken(response);
      if (error) throw error;
      return data;
    },
    onSuccess: (data) => queryClient.setQueryData(CART_QUERY_KEY, data),
  });
}

export function useClearCart() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data, response, error } = await apiClient.DELETE("/cart", { headers: await guestHeaders() });
      await captureGuestToken(response);
      if (error) throw error;
      return data;
    },
    onSuccess: (data) => queryClient.setQueryData(CART_QUERY_KEY, data),
  });
}

export function useMergeGuestCartOnLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const guestToken = await getGuestCartToken();
      if (!guestToken) return null;
      const { data, error } = await apiClient.POST("/cart/merge", { body: { guest_token: guestToken } });
      if (error) throw error;
      await setGuestCartToken(null);
      return data;
    },
    onSuccess: (data) => {
      if (data) queryClient.setQueryData(CART_QUERY_KEY, data);
    },
  });
}

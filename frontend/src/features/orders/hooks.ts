import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export function useOrder(orderNumber: string | undefined, guestToken?: string) {
  return useQuery({
    queryKey: ["order", orderNumber, guestToken],
    enabled: !!orderNumber,
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/orders/{order_number}", {
        params: { path: { order_number: orderNumber! }, query: guestToken ? { guest_token: guestToken } : undefined },
      });
      if (error) throw error;
      return data;
    },
  });
}

export function useMyOrders(page: number) {
  return useQuery({
    queryKey: ["my-orders", page],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/orders", { params: { query: { page } } });
      if (error) throw error;
      return data;
    },
  });
}

export function useCancelOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (orderNumber: string) => {
      const { data, error } = await apiClient.POST("/orders/{order_number}/cancel", {
        params: { path: { order_number: orderNumber } },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["order", data.order_number, undefined], data);
      void queryClient.invalidateQueries({ queryKey: ["my-orders"] });
    },
  });
}

export function useSubmitReview() {
  return useMutation({
    mutationFn: async (body: { order_id: string; product_id: string; rating: number; body: string }) => {
      const { data, error } = await apiClient.POST("/reviews", { body });
      if (error) throw error;
      return data;
    },
  });
}

export function useRequestReturn() {
  return useMutation({
    mutationFn: async (body: { order_id: string; reason: string }) => {
      const { data, error } = await apiClient.POST("/returns", { body });
      if (error) throw error;
      return data;
    },
  });
}

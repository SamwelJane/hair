import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export function useSupplierOrders() {
  return useQuery({
    queryKey: ["supplier-orders"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/supplier/orders", {});
      if (error) throw error;
      return data;
    },
  });
}

export function useUpdateSupplierOrderStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      supplierOrderId,
      toStatus,
      etaDays,
      declineReason,
    }: {
      supplierOrderId: string;
      toStatus: "ACKNOWLEDGED" | "IN_PRODUCTION" | "READY" | "DECLINED";
      etaDays?: number;
      declineReason?: string;
    }) => {
      const { data, error } = await apiClient.POST("/supplier/orders/{supplier_order_id}/status", {
        params: { path: { supplier_order_id: supplierOrderId } },
        body: { to_status: toStatus, eta_days: etaDays, decline_reason: declineReason },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["supplier-orders"] }),
  });
}

export function useSupplierProducts() {
  return useQuery({
    queryKey: ["supplier-products"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/supplier/products", {});
      if (error) throw error;
      return data;
    },
  });
}

export function useSupplierProduct(productId: string | undefined) {
  return useQuery({
    queryKey: ["supplier-product", productId],
    enabled: !!productId,
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/supplier/products/{product_id}", {
        params: { path: { product_id: productId! } },
      });
      if (error) throw error;
      return data;
    },
  });
}

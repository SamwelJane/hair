import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";
import { tokenStore } from "../../lib/auth/tokenStore";

// ---------- Dashboard / analytics ----------

export function useDashboardKpis() {
  return useQuery({
    queryKey: ["admin-dashboard-kpis"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/analytics/dashboard-kpis", {});
      if (error) throw error;
      return data;
    },
  });
}

export function useRevenueSummary() {
  return useQuery({
    queryKey: ["admin-revenue"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/analytics/revenue", {});
      if (error) throw error;
      return data;
    },
  });
}

export function useOperationsSummary() {
  return useQuery({
    queryKey: ["admin-operations"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/analytics/operations", {});
      if (error) throw error;
      return data;
    },
  });
}

export function useFinanceSummary() {
  return useQuery({
    queryKey: ["admin-finance"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/analytics/finance", {});
      if (error) throw error;
      return data;
    },
  });
}

export function useLogisticsSummary() {
  return useQuery({
    queryKey: ["admin-logistics"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/analytics/logistics", {});
      if (error) throw error;
      return data;
    },
  });
}

export function useCustomsSummary() {
  return useQuery({
    queryKey: ["admin-customs"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/analytics/customs", {});
      if (error) throw error;
      return data;
    },
  });
}

export function useSupplierPerformanceSummary() {
  return useQuery({
    queryKey: ["admin-supplier-performance"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/analytics/suppliers", {});
      if (error) throw error;
      return data;
    },
  });
}

async function downloadAuthenticated(path: string, filename: string): Promise<void> {
  const token = tokenStore.getState().accessToken;
  const res = await fetch(`${tokenStore.apiBaseUrl}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error("Export failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export async function downloadAnalyticsExport(type: string): Promise<void> {
  await downloadAuthenticated(`/admin/analytics/export?type=${type}`, `${type}-export.csv`);
}

// ---------- Orders ----------

export function useAdminOrders(filters: { q?: string; status?: string; from?: string; to?: string; page?: number }) {
  return useQuery({
    queryKey: ["admin-orders", filters],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/orders", { params: { query: filters as never } });
      if (error) throw error;
      return data;
    },
  });
}

export function useAdminOrder(orderId: string | undefined) {
  return useQuery({
    queryKey: ["admin-order", orderId],
    enabled: !!orderId,
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/orders/{order_id}", { params: { path: { order_id: orderId! } } });
      if (error) throw error;
      return data;
    },
  });
}

export function useTransitionOrderStatus(orderId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ toStatus, note }: { toStatus: string; note?: string }) => {
      const { data, error } = await apiClient.POST("/admin/orders/{order_id}/status", {
        params: { path: { order_id: orderId } },
        body: { to_status: toStatus as never, note },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-order", orderId] }),
  });
}


// ---------- Payments ----------

export function useAdminPayments() {
  return useQuery({
    queryKey: ["admin-payments"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/payments", {});
      if (error) throw error;
      return data;
    },
  });
}

export function useConfirmBankTransfer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (paymentId: string) => {
      const { error } = await apiClient.POST("/payments/bank-transfer/confirm", { body: { payment_id: paymentId } });
      if (error) throw error;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-payments"] }),
  });
}

export function useRejectBankTransfer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (paymentId: string) => {
      const { error } = await apiClient.POST("/payments/bank-transfer/reject", { body: { payment_id: paymentId } });
      if (error) throw error;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-payments"] }),
  });
}

// ---------- Categories ----------

export function useAdminCategories() {
  return useQuery({
    queryKey: ["admin-categories"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/categories", {});
      if (error) throw error;
      return data;
    },
  });
}

export function useCreateCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (name: string) => {
      const { data, error } = await apiClient.POST("/admin/categories", { body: { name } });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-categories"] }),
  });
}

export function useDeleteCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (categoryId: string) => {
      const { error } = await apiClient.DELETE("/admin/categories/{category_id}", { params: { path: { category_id: categoryId } } });
      if (error) throw error;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-categories"] }),
  });
}

export function useUpdateCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: { categoryId: string; name: string; is_featured: boolean; sort_order: number }) => {
      const { categoryId, ...body } = params;
      const { data, error } = await apiClient.PATCH("/admin/categories/{category_id}", {
        params: { path: { category_id: categoryId } },
        body,
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-categories"] }),
  });
}

export function useUploadCategoryImage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: { categoryId: string; file: File }) => {
      const formData = new FormData();
      formData.append("file", params.file);
      const token = tokenStore.getState().accessToken;
      const res = await fetch(`${tokenStore.apiBaseUrl}/admin/categories/${params.categoryId}/image`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });
      if (!res.ok) throw new Error("Upload failed");
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-categories"] }),
  });
}

// ---------- Homepage: banners ----------

export function useAdminBanners() {
  return useQuery({
    queryKey: ["admin-homepage-banners"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/homepage/banners", {});
      if (error) throw error;
      return data;
    },
  });
}

type BannerFormValues = {
  headline: string;
  subheadline?: string | null;
  cta_label?: string | null;
  cta_url?: string | null;
  sort_order: number;
  is_active: boolean;
};

export function useCreateBanner() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: BannerFormValues) => {
      const { data, error } = await apiClient.POST("/admin/homepage/banners", { body });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-homepage-banners"] }),
  });
}

export function useUpdateBanner() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: { bannerId: string } & BannerFormValues) => {
      const { bannerId, ...body } = params;
      const { data, error } = await apiClient.PATCH("/admin/homepage/banners/{banner_id}", {
        params: { path: { banner_id: bannerId } },
        body,
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-homepage-banners"] }),
  });
}

export function useDeleteBanner() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (bannerId: string) => {
      const { error } = await apiClient.DELETE("/admin/homepage/banners/{banner_id}", {
        params: { path: { banner_id: bannerId } },
      });
      if (error) throw error;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-homepage-banners"] }),
  });
}

export function useUploadBannerImage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: { bannerId: string; file: File }) => {
      const formData = new FormData();
      formData.append("file", params.file);
      const token = tokenStore.getState().accessToken;
      const res = await fetch(`${tokenStore.apiBaseUrl}/admin/homepage/banners/${params.bannerId}/image`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });
      if (!res.ok) throw new Error("Upload failed");
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-homepage-banners"] }),
  });
}

// ---------- Homepage: product placements (Featured / Deals) ----------

export function useAdminPlacements() {
  return useQuery({
    queryKey: ["admin-homepage-placements"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/homepage/product-placements", {});
      if (error) throw error;
      return data;
    },
  });
}

type PlacementFormValues = {
  section: "FEATURED" | "DEAL";
  sale_price_usd?: string | null;
  starts_at?: string | null;
  ends_at?: string | null;
  sort_order: number;
  is_active: boolean;
};

export function useCreatePlacement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: PlacementFormValues & { product_id: string }) => {
      const { data, error } = await apiClient.POST("/admin/homepage/product-placements", { body });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-homepage-placements"] }),
  });
}

export function useUpdatePlacement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: { placementId: string } & PlacementFormValues) => {
      const { placementId, ...body } = params;
      const { data, error } = await apiClient.PATCH("/admin/homepage/product-placements/{placement_id}", {
        params: { path: { placement_id: placementId } },
        body,
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-homepage-placements"] }),
  });
}

export function useDeletePlacement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (placementId: string) => {
      const { error } = await apiClient.DELETE("/admin/homepage/product-placements/{placement_id}", {
        params: { path: { placement_id: placementId } },
      });
      if (error) throw error;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-homepage-placements"] }),
  });
}

// ---------- Suppliers ----------

export function useAdminSuppliers() {
  return useQuery({
    queryKey: ["admin-suppliers"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/suppliers", {});
      if (error) throw error;
      return data;
    },
  });
}

export function useAdminSupplierDetail(supplierId: string | undefined) {
  return useQuery({
    queryKey: ["admin-supplier", supplierId],
    enabled: !!supplierId,
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/suppliers/{supplier_id}", { params: { path: { supplier_id: supplierId! } } });
      if (error) throw error;
      return data;
    },
  });
}

export function useCreateSupplier() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: { name: string; country: string; email: string; whatsapp_number: string; default_margin_pct: string; temporary_password?: string }) => {
      const { data, error } = await apiClient.POST("/admin/suppliers", { body });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-suppliers"] }),
  });
}

export function useAdvanceSupplierOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (supplierOrderId: string) => {
      const { data, error } = await apiClient.POST("/admin/supplier-orders/{supplier_order_id}/advance", {
        params: { path: { supplier_order_id: supplierOrderId } },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-supplier"] }),
  });
}

// ---------- Returns / Reviews ----------

export function useAdminReturns() {
  return useQuery({
    queryKey: ["admin-returns"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/returns", {});
      if (error) throw error;
      return data;
    },
  });
}

export function useResolveReturn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ returnId, status, refundAmountUsd }: { returnId: string; status: "APPROVED" | "REJECTED" | "REFUNDED"; refundAmountUsd?: string }) => {
      const { data, error } = await apiClient.POST("/admin/returns/{return_id}/resolve", {
        params: { path: { return_id: returnId } },
        body: { status, refund_amount_usd: refundAmountUsd || undefined },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-returns"] }),
  });
}

export function useAdminReviews() {
  return useQuery({
    queryKey: ["admin-reviews"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/reviews", {});
      if (error) throw error;
      return data;
    },
  });
}

export function useModerateReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ reviewId, status }: { reviewId: string; status: "approved" | "rejected" }) => {
      const { data, error } = await apiClient.POST("/admin/reviews/{review_id}/moderate", {
        params: { path: { review_id: reviewId } },
        body: { status },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-reviews"] }),
  });
}

// ---------- Users ----------

export function useAdminUsers() {
  return useQuery({
    queryKey: ["admin-users"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/users", {});
      if (error) throw error;
      return data;
    },
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      email: string;
      name: string;
      role: "ADMIN" | "STAFF" | "SUPPLIER" | "CUSTOMER" | "WAREHOUSE" | "KENYA_OPS";
      password: string;
    }) => {
      const { data, error } = await apiClient.POST("/admin/users", { body });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });
}

export function useToggleUserActive() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (userId: string) => {
      const { data, error } = await apiClient.POST("/admin/users/{user_id}/toggle-active", { params: { path: { user_id: userId } } });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });
}

// ---------- Audit logs ----------

export function useAuditLogs(filters: { action?: string; entity_type?: string; from?: string; to?: string; page?: number }) {
  return useQuery({
    queryKey: ["admin-audit-logs", filters],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/audit-logs", { params: { query: filters } });
      if (error) throw error;
      return data;
    },
  });
}

export async function downloadAuditLogExport(filters: { action?: string; entity_type?: string; from?: string; to?: string }): Promise<void> {
  const params = new URLSearchParams(Object.entries(filters).filter(([, v]) => v) as [string, string][]);
  await downloadAuthenticated(`/admin/audit-logs/export?${params}`, "audit-logs.csv");
}

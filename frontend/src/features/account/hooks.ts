import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";
import { tokenStore } from "../../lib/auth/tokenStore";

export function useAddresses() {
  return useQuery({
    queryKey: ["addresses"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/addresses", {});
      if (error) throw error;
      return data;
    },
  });
}

export function useCreateAddress() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      label?: string;
      full_name: string;
      line1: string;
      line2?: string;
      city: string;
      country_code: string;
      postal_code?: string;
      phone: string;
      is_default: boolean;
    }) => {
      const { data, error } = await apiClient.POST("/addresses", { body });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["addresses"] }),
  });
}

export function useDeleteAddress() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (addressId: string) => {
      const { error } = await apiClient.DELETE("/addresses/{address_id}", { params: { path: { address_id: addressId } } });
      if (error) throw error;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["addresses"] }),
  });
}

export function useSetDefaultAddress() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (addressId: string) => {
      const { data, error } = await apiClient.POST("/addresses/{address_id}/set-default", {
        params: { path: { address_id: addressId } },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["addresses"] }),
  });
}

export function useDeactivateAccount() {
  return useMutation({
    mutationFn: async () => {
      const { error } = await apiClient.POST("/account/deactivate", {});
      if (error) throw error;
    },
  });
}

export async function downloadAccountExport(): Promise<void> {
  // Not routed through the typed api-client: we want the raw Blob/headers
  // for a file download, which openapi-fetch's JSON-first client doesn't
  // make convenient - a plain authenticated fetch is simpler here.
  const token = tokenStore.getState().accessToken;
  const res = await fetch(`${tokenStore.apiBaseUrl}/account/export`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error("Export failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "my-hiar-business-data.json";
  link.click();
  URL.revokeObjectURL(url);
}

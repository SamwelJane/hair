import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

// Spec section 48 wants the backend's specific error text ("Tracking number
// not found.", "This package has already been received.") shown to
// warehouse staff, not a generic failure message - unlike most other forms
// in this app, so this extracts it from the thrown error instead of
// swallowing it into a canned string.
export function getErrorDetail(error: unknown): string | undefined {
  if (typeof error === "object" && error && "detail" in error) {
    return String((error as { detail: unknown }).detail);
  }
  return undefined;
}

export function useWarehouseDashboard() {
  return useQuery({
    queryKey: ["warehouse-dashboard"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/warehouse/dashboard", {});
      if (error) throw error;
      return data;
    },
    refetchInterval: 30_000,
  });
}

export function usePackages(params: { q?: string; status?: string; page: number }) {
  return useQuery({
    queryKey: ["warehouse-packages", params],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/warehouse/packages", {
        params: { query: { q: params.q, status: params.status, page: params.page } },
      });
      if (error) throw error;
      return data;
    },
  });
}

export function usePackage(packageId: string | undefined) {
  return useQuery({
    queryKey: ["warehouse-package", packageId],
    enabled: !!packageId,
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/warehouse/packages/{package_id}", {
        params: { path: { package_id: packageId! } },
      });
      if (error) throw error;
      return data;
    },
  });
}

export function useReceivePackage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { trackingNumber: string; weightGrams?: number; condition?: "GOOD" | "DAMAGED"; notes?: string }) => {
      const { data, error } = await apiClient.POST("/warehouse/packages/receive", {
        body: {
          tracking_number: payload.trackingNumber,
          weight_grams: payload.weightGrams,
          condition: payload.condition,
          notes: payload.notes,
        },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["warehouse-packages"] });
      void queryClient.invalidateQueries({ queryKey: ["warehouse-dashboard"] });
    },
  });
}

export function useQCPackage(packageId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { qcStatus: "PENDING" | "PASSED" | "FAILED"; condition?: "GOOD" | "DAMAGED"; notes?: string }) => {
      const { data, error } = await apiClient.POST("/warehouse/packages/{package_id}/qc", {
        params: { path: { package_id: packageId } },
        body: { qc_status: payload.qcStatus, condition: payload.condition, notes: payload.notes },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["warehouse-package", packageId] });
      void queryClient.invalidateQueries({ queryKey: ["warehouse-dashboard"] });
    },
  });
}

export function useWeighPackage(packageId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { weightGrams: number; lengthCm?: string; widthCm?: string; heightCm?: string }) => {
      const { data, error } = await apiClient.POST("/warehouse/packages/{package_id}/weigh", {
        params: { path: { package_id: packageId } },
        body: {
          weight_grams: payload.weightGrams,
          length_cm: payload.lengthCm,
          width_cm: payload.widthCm,
          height_cm: payload.heightCm,
        },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["warehouse-package", packageId] });
      void queryClient.invalidateQueries({ queryKey: ["warehouse-dashboard"] });
    },
  });
}

export function usePrintLabel(packageId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data, error } = await apiClient.POST("/warehouse/packages/{package_id}/label", {
        params: { path: { package_id: packageId } },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["warehouse-package", packageId] }),
  });
}

export function useReprintLabel(packageId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data, error } = await apiClient.POST("/warehouse/packages/{package_id}/label/reprint", {
        params: { path: { package_id: packageId } },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["warehouse-package", packageId] }),
  });
}

export function useCreateExternalShipment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      customerName: string;
      customerPhone: string;
      customerEmail?: string;
      supplierReference?: string;
      notes?: string;
      weightGrams?: number;
      lengthCm?: string;
      widthCm?: string;
      heightCm?: string;
    }) => {
      const { data, error } = await apiClient.POST("/warehouse/external-shipments", {
        body: {
          customer_name: payload.customerName,
          customer_phone: payload.customerPhone,
          customer_email: payload.customerEmail,
          supplier_reference: payload.supplierReference,
          notes: payload.notes,
          weight_grams: payload.weightGrams,
          length_cm: payload.lengthCm,
          width_cm: payload.widthCm,
          height_cm: payload.heightCm,
        },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["warehouse-external-shipments"] });
      void queryClient.invalidateQueries({ queryKey: ["warehouse-packages"] });
      void queryClient.invalidateQueries({ queryKey: ["warehouse-dashboard"] });
    },
  });
}

export function useExternalShipments(params: { q?: string; page: number }) {
  return useQuery({
    queryKey: ["warehouse-external-shipments", params],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/warehouse/external-shipments", {
        params: { query: { q: params.q, page: params.page } },
      });
      if (error) throw error;
      return data;
    },
  });
}

export function useExternalShipment(shipmentId: string | undefined) {
  return useQuery({
    queryKey: ["warehouse-external-shipment", shipmentId],
    enabled: !!shipmentId,
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/warehouse/external-shipments/{shipment_id}", {
        params: { path: { shipment_id: shipmentId! } },
      });
      if (error) throw error;
      return data;
    },
  });
}

export function useConsolidations(params: { status?: string; page: number }) {
  return useQuery({
    queryKey: ["warehouse-consolidations", params],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/warehouse/consolidations", {
        params: { query: { status: params.status, page: params.page } },
      });
      if (error) throw error;
      return data;
    },
  });
}

export function useConsolidation(consolidationId: string | undefined) {
  return useQuery({
    queryKey: ["warehouse-consolidation", consolidationId],
    enabled: !!consolidationId,
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/warehouse/consolidations/{consolidation_id}", {
        params: { path: { consolidation_id: consolidationId! } },
      });
      if (error) throw error;
      return data;
    },
  });
}

export function useCreateConsolidation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { originWarehouseId?: string; destinationWarehouseId?: string; freightMethod?: string; freightProvider?: string } = {}) => {
      const { data, error } = await apiClient.POST("/warehouse/consolidations", {
        body: {
          origin_warehouse_id: payload.originWarehouseId,
          destination_warehouse_id: payload.destinationWarehouseId,
          freight_method: payload.freightMethod,
          freight_provider: payload.freightProvider,
        },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["warehouse-consolidations"] }),
  });
}

export function useAddPackageToConsolidation(consolidationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (packageId: string) => {
      const { data, error } = await apiClient.POST("/warehouse/consolidations/{consolidation_id}/packages", {
        params: { path: { consolidation_id: consolidationId } },
        body: { package_id: packageId },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["warehouse-consolidation", consolidationId] });
      void queryClient.invalidateQueries({ queryKey: ["warehouse-packages"] });
      void queryClient.invalidateQueries({ queryKey: ["warehouse-dashboard"] });
    },
  });
}

export function useRemovePackageFromConsolidation(consolidationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (packageId: string) => {
      const { data, error } = await apiClient.DELETE("/warehouse/consolidations/{consolidation_id}/packages/{package_id}", {
        params: { path: { consolidation_id: consolidationId, package_id: packageId } },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["warehouse-consolidation", consolidationId] });
      void queryClient.invalidateQueries({ queryKey: ["warehouse-packages"] });
      void queryClient.invalidateQueries({ queryKey: ["warehouse-dashboard"] });
    },
  });
}

export function useMarkReadyForExport(consolidationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data, error } = await apiClient.POST("/warehouse/consolidations/{consolidation_id}/ready-for-export", {
        params: { path: { consolidation_id: consolidationId } },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["warehouse-consolidation", consolidationId] }),
  });
}

export function useMarkDeparted(consolidationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data, error } = await apiClient.POST("/warehouse/consolidations/{consolidation_id}/depart", {
        params: { path: { consolidation_id: consolidationId } },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["warehouse-consolidation", consolidationId] });
      void queryClient.invalidateQueries({ queryKey: ["warehouse-consolidations"] });
    },
  });
}

export function useMarkInTransit(consolidationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { carrier?: string; carrierTrackingReference?: string; currentLocation?: string }) => {
      const { data, error } = await apiClient.POST("/warehouse/consolidations/{consolidation_id}/mark-in-transit", {
        params: { path: { consolidation_id: consolidationId } },
        body: {
          carrier: payload.carrier,
          carrier_tracking_reference: payload.carrierTrackingReference,
          current_location: payload.currentLocation,
        },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["warehouse-consolidation", consolidationId] }),
  });
}

export function useTransitUpdate(consolidationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { currentLocation?: string }) => {
      const { data, error } = await apiClient.POST("/warehouse/consolidations/{consolidation_id}/transit-update", {
        params: { path: { consolidation_id: consolidationId } },
        body: { current_location: payload.currentLocation },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["warehouse-consolidation", consolidationId] }),
  });
}

export function useArriveKenya(consolidationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data, error } = await apiClient.POST("/warehouse/consolidations/{consolidation_id}/arrive-kenya", {
        params: { path: { consolidation_id: consolidationId } },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["warehouse-consolidation", consolidationId] }),
  });
}

export function useReportConsolidationException(consolidationId: string) {
  return useMutation({
    mutationFn: async (payload: { exceptionType: string; severity: string; description?: string }) => {
      const { data, error } = await apiClient.POST("/warehouse/consolidations/{consolidation_id}/exceptions", {
        params: { path: { consolidation_id: consolidationId } },
        body: {
          exception_type: payload.exceptionType as never,
          severity: payload.severity as never,
          description: payload.description,
        },
      });
      if (error) throw error;
      return data;
    },
  });
}

export function useCustomsDeclarations(params: { status?: string; page: number }) {
  return useQuery({
    queryKey: ["warehouse-customs-declarations", params],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/warehouse/customs-declarations", {
        params: { query: { status: params.status, page: params.page } },
      });
      if (error) throw error;
      return data;
    },
  });
}

export function useCustomsDeclaration(declarationId: string | undefined) {
  return useQuery({
    queryKey: ["warehouse-customs-declaration", declarationId],
    enabled: !!declarationId,
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/warehouse/customs-declarations/{declaration_id}", {
        params: { path: { declaration_id: declarationId! } },
      });
      if (error) throw error;
      return data;
    },
  });
}

export function useDeclareCustoms(declarationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { hsCode: string; declaredValueUsd: string; dutyUsd?: string; vatUsd?: string }) => {
      const { data, error } = await apiClient.POST("/warehouse/customs-declarations/{declaration_id}/declare", {
        params: { path: { declaration_id: declarationId } },
        body: {
          hs_code: payload.hsCode,
          declared_value_usd: payload.declaredValueUsd,
          duty_usd: payload.dutyUsd ?? "0",
          vat_usd: payload.vatUsd ?? "0",
        },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["warehouse-customs-declaration", declarationId] });
      void queryClient.invalidateQueries({ queryKey: ["warehouse-customs-declarations"] });
    },
  });
}

export function useRaiseCustomsQuery(declarationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (note: string) => {
      const { data, error } = await apiClient.POST("/warehouse/customs-declarations/{declaration_id}/query", {
        params: { path: { declaration_id: declarationId } },
        body: { note },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["warehouse-customs-declaration", declarationId] });
      void queryClient.invalidateQueries({ queryKey: ["warehouse-customs-declarations"] });
    },
  });
}

export function useClearCustoms(declarationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data, error } = await apiClient.POST("/warehouse/customs-declarations/{declaration_id}/clear", {
        params: { path: { declaration_id: declarationId } },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["warehouse-customs-declaration", declarationId] });
      void queryClient.invalidateQueries({ queryKey: ["warehouse-customs-declarations"] });
      void queryClient.invalidateQueries({ queryKey: ["warehouse-consolidations"] });
    },
  });
}

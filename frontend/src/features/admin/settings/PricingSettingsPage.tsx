import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../../lib/apiClient";

export function AdminPricingSettingsPage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["pricing-settings"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/settings/pricing", {});
      if (error) throw error;
      return data;
    },
  });

  const [commission, setCommission] = useState("");
  const [shippingPerKg, setShippingPerKg] = useState("");
  const [packaging, setPackaging] = useState("");
  const [kesAdjustment, setKesAdjustment] = useState("");

  useEffect(() => {
    if (data) {
      setCommission(data.commission_pct);
      setShippingPerKg(data.shipping_per_kg_usd);
      setPackaging(data.packaging_fee_usd);
      setKesAdjustment(data.kes_adjustment);
    }
  }, [data]);

  const update = useMutation({
    mutationFn: async () => {
      const { error } = await apiClient.PUT("/admin/settings/pricing", {
        body: { commission_pct: commission, shipping_per_kg_usd: shippingPerKg, packaging_fee_usd: packaging, kes_adjustment: kesAdjustment },
      });
      if (error) throw error;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["pricing-settings"] }),
  });

  if (isLoading) return <div className="page">Loading...</div>;

  return (
    <div className="page narrow">
      <h1>Pricing Settings</h1>
      <form onSubmit={(e) => { e.preventDefault(); update.mutate(); }} className="auth-form">
        <label>Commission %<input required type="number" step="0.01" value={commission} onChange={(e) => setCommission(e.target.value)} /></label>
        <label>Shipping per kg (USD)<input required type="number" step="0.01" value={shippingPerKg} onChange={(e) => setShippingPerKg(e.target.value)} /></label>
        <label>Packaging fee (USD)<input required type="number" step="0.01" value={packaging} onChange={(e) => setPackaging(e.target.value)} /></label>
        <label>KES adjustment<input required type="number" step="0.01" value={kesAdjustment} onChange={(e) => setKesAdjustment(e.target.value)} /></label>
        <button type="submit" disabled={update.isPending}>Save</button>
      </form>
    </div>
  );
}

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../../lib/apiClient";

export function AdminShippingRulesPage() {
  const queryClient = useQueryClient();
  const { data: rules, isLoading } = useQuery({
    queryKey: ["shipping-rules"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/settings/shipping-rules", {});
      if (error) throw error;
      return data;
    },
  });

  const [countryCode, setCountryCode] = useState("");
  const [countryName, setCountryName] = useState("");
  const [baseFee, setBaseFee] = useState("");
  const [perKgFee, setPerKgFee] = useState("");
  const [customsRate, setCustomsRate] = useState("0");
  const [minDays, setMinDays] = useState(3);
  const [maxDays, setMaxDays] = useState(7);

  const upsert = useMutation({
    mutationFn: async () => {
      const { error } = await apiClient.PUT("/admin/settings/shipping-rules", {
        body: {
          country_code: countryCode, country_name: countryName, base_fee_usd: baseFee, per_kg_fee_usd: perKgFee,
          customs_rate_pct: customsRate, estimated_days_min: minDays, estimated_days_max: maxDays,
        },
      });
      if (error) throw error;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["shipping-rules"] });
      setCountryCode(""); setCountryName(""); setBaseFee(""); setPerKgFee(""); setCustomsRate("0");
    },
  });

  const remove = useMutation({
    mutationFn: async (code: string) => {
      const { error } = await apiClient.DELETE("/admin/settings/shipping-rules/{country_code}", { params: { path: { country_code: code } } });
      if (error) throw error;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["shipping-rules"] }),
  });

  if (isLoading) return <div className="page">Loading...</div>;

  return (
    <div className="page">
      <h1>Shipping Rules</h1>
      <table className="page-table">
        <thead><tr><th>Country</th><th>Base Fee</th><th>Per kg</th><th>Customs %</th><th>Est. Days</th><th /></tr></thead>
        <tbody>
          {rules?.map((r) => (
            <tr key={r.country_code}>
              <td>{r.country_name} ({r.country_code})</td>
              <td>${r.base_fee_usd}</td>
              <td>${r.per_kg_fee_usd}</td>
              <td>{r.customs_rate_pct}%</td>
              <td>{r.estimated_days_min}-{r.estimated_days_max}</td>
              <td><button type="button" className="danger" onClick={() => remove.mutate(r.country_code)}>Delete</button></td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Add / Update Rule</h2>
      <form onSubmit={(e) => { e.preventDefault(); upsert.mutate(); }} className="auth-form">
        <label>Country code<input required maxLength={2} value={countryCode} onChange={(e) => setCountryCode(e.target.value.toUpperCase())} /></label>
        <label>Country name<input required value={countryName} onChange={(e) => setCountryName(e.target.value)} /></label>
        <label>Base fee (USD)<input required type="number" step="0.01" value={baseFee} onChange={(e) => setBaseFee(e.target.value)} /></label>
        <label>Per kg fee (USD)<input required type="number" step="0.01" value={perKgFee} onChange={(e) => setPerKgFee(e.target.value)} /></label>
        <label>Customs rate %<input type="number" step="0.01" value={customsRate} onChange={(e) => setCustomsRate(e.target.value)} /></label>
        <label>Estimated min days<input type="number" value={minDays} onChange={(e) => setMinDays(Number(e.target.value))} /></label>
        <label>Estimated max days<input type="number" value={maxDays} onChange={(e) => setMaxDays(Number(e.target.value))} /></label>
        <button type="submit" disabled={upsert.isPending}>Save Rule</button>
      </form>
    </div>
  );
}

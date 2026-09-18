import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../../lib/apiClient";

export function AdminDiscountCodesPage() {
  const queryClient = useQueryClient();
  const { data: codes, isLoading } = useQuery({
    queryKey: ["discount-codes"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/settings/discount-codes", {});
      if (error) throw error;
      return data;
    },
  });

  const [code, setCode] = useState("");
  const [type, setType] = useState<"percent" | "fixed">("percent");
  const [value, setValue] = useState("");
  const [usageLimit, setUsageLimit] = useState("");

  const create = useMutation({
    mutationFn: async () => {
      const { error } = await apiClient.POST("/admin/settings/discount-codes", {
        body: { code, type, value, usage_limit: usageLimit ? Number(usageLimit) : undefined },
      });
      if (error) throw error;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["discount-codes"] });
      setCode(""); setValue(""); setUsageLimit("");
    },
  });

  const toggle = useMutation({
    mutationFn: async (id: string) => {
      const { error } = await apiClient.POST("/admin/settings/discount-codes/{discount_id}/toggle-active", { params: { path: { discount_id: id } } });
      if (error) throw error;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["discount-codes"] }),
  });

  if (isLoading) return <div className="page">Loading...</div>;

  return (
    <div className="page">
      <h1>Discount Codes</h1>
      <table className="page-table">
        <thead><tr><th>Code</th><th>Type</th><th>Value</th><th>Used</th><th>Status</th><th /></tr></thead>
        <tbody>
          {codes?.map((c) => (
            <tr key={c.id}>
              <td>{c.code}</td><td>{c.type}</td><td>{c.value}</td>
              <td>{c.times_used}{c.usage_limit ? ` / ${c.usage_limit}` : ""}</td>
              <td><span className="badge">{c.status}</span></td>
              <td><button type="button" onClick={() => toggle.mutate(c.id)}>{c.is_enabled ? "Disable" : "Enable"}</button></td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Create Discount Code</h2>
      <form onSubmit={(e) => { e.preventDefault(); create.mutate(); }} className="auth-form">
        <label>Code<input required value={code} onChange={(e) => setCode(e.target.value.toUpperCase())} /></label>
        <label>Type
          <select value={type} onChange={(e) => setType(e.target.value as typeof type)}>
            <option value="percent">Percent</option>
            <option value="fixed">Fixed (USD)</option>
          </select>
        </label>
        <label>Value<input required type="number" step="0.01" value={value} onChange={(e) => setValue(e.target.value)} /></label>
        <label>Usage limit (optional)<input type="number" value={usageLimit} onChange={(e) => setUsageLimit(e.target.value)} /></label>
        <button type="submit" disabled={create.isPending}>Create</button>
      </form>
    </div>
  );
}

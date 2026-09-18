import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../../lib/apiClient";

export function AdminExchangeRatePage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["exchange-rate"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/admin/settings/exchange-rate", {});
      if (error) throw error;
      return data;
    },
  });
  const [rate, setRate] = useState("");

  useEffect(() => { if (data) setRate(data.rate); }, [data]);

  const update = useMutation({
    mutationFn: async () => {
      const { error } = await apiClient.PUT("/admin/settings/exchange-rate", { body: { rate } });
      if (error) throw error;
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["exchange-rate"] }),
  });

  if (isLoading) return <div className="page">Loading...</div>;

  return (
    <div className="page narrow">
      <h1>Exchange Rate</h1>
      {data && <p className="muted">Last updated by {data.updated_by_name} on {new Date(data.updated_at).toLocaleString()}</p>}
      <form onSubmit={(e) => { e.preventDefault(); update.mutate(); }} className="auth-form">
        <label>USD → KES rate<input required type="number" step="0.0001" value={rate} onChange={(e) => setRate(e.target.value)} /></label>
        <button type="submit" disabled={update.isPending}>Save</button>
      </form>
    </div>
  );
}

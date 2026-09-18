import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router";
import { apiClient } from "../../lib/apiClient";

export function TrackingPage() {
  const { trackingNumber } = useParams<{ trackingNumber: string }>();
  const { data: tracking, isLoading, isError } = useQuery({
    queryKey: ["tracking", trackingNumber],
    enabled: !!trackingNumber,
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/track/{tracking_number}", {
        params: { path: { tracking_number: trackingNumber! } },
      });
      if (error) throw error;
      return data;
    },
  });

  if (isLoading) return <div className="page">Loading...</div>;
  if (isError || !tracking) return <div className="page">We couldn't find a shipment with that tracking number.</div>;

  return (
    <div className="page">
      <h1>Tracking {tracking.tracking_number}</h1>
      <p className="badge">{tracking.status.replaceAll("_", " ")}</p>
      {tracking.delivery_estimate && (
        <p>Estimated delivery: {tracking.delivery_estimate.min_days}-{tracking.delivery_estimate.max_days} days from dispatch</p>
      )}

      {tracking.packages.length > 1 && (
        <>
          <h2>Packages</h2>
          <ul className="order-item-list">
            {tracking.packages.map((p) => (
              <li key={p.package_code}>
                <span>{p.package_code}</span>
                <span className="badge">{p.status.replaceAll("_", " ")}</span>
              </li>
            ))}
          </ul>
        </>
      )}

      <h2>Timeline</h2>
      <ol className="milestone-list">
        {tracking.events.map((e) => (
          <li key={e.id}>
            <p className="milestone-label">{e.label}</p>
            <p className="muted">{new Date(e.occurred_at).toLocaleString()} {e.location ? `- ${e.location}` : ""}</p>
          </li>
        ))}
        {tracking.events.length === 0 && <li>No updates yet.</li>}
      </ol>
    </div>
  );
}

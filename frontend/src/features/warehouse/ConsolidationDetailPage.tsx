import { useState } from "react";
import { useParams } from "react-router";
import {
  getErrorDetail,
  useArriveKenya,
  useConsolidation,
  useMarkDeparted,
  useMarkInTransit,
  useMarkReadyForExport,
  useRemovePackageFromConsolidation,
  useReportConsolidationException,
  useTransitUpdate,
} from "./hooks";

const EXCEPTION_TYPES = [
  "SHIPMENT_DELAYED",
  "CUSTOMS_QUERY",
  "CUSTOMS_HOLD",
  "CUSTOMS_ISSUE",
  "PACKAGE_MISSING",
  "PACKAGE_DAMAGED",
];

export function ConsolidationDetailPage() {
  const { consolidationId } = useParams<{ consolidationId: string }>();
  const { data: consolidation, isLoading } = useConsolidation(consolidationId);
  const removePackage = useRemovePackageFromConsolidation(consolidationId!);
  const readyForExport = useMarkReadyForExport(consolidationId!);
  const depart = useMarkDeparted(consolidationId!);
  const markInTransit = useMarkInTransit(consolidationId!);
  const transitUpdate = useTransitUpdate(consolidationId!);
  const arriveKenya = useArriveKenya(consolidationId!);
  const reportException = useReportConsolidationException(consolidationId!);

  const [carrier, setCarrier] = useState("");
  const [carrierRef, setCarrierRef] = useState("");
  const [location, setLocation] = useState("");
  const [exceptionType, setExceptionType] = useState(EXCEPTION_TYPES[0]);
  const [exceptionNotes, setExceptionNotes] = useState("");

  if (isLoading) return <div className="page">Loading...</div>;
  if (!consolidation) return <div className="page">Consolidation not found.</div>;

  const isOpen = consolidation.status === "OPEN";

  return (
    <div className="page">
      <h1>Consolidation {consolidation.consolidation_code}</h1>
      <p className="badge">{consolidation.status.replaceAll("_", " ")}</p>
      {consolidation.shipment_code && <p className="muted">Shipment: <strong>{consolidation.shipment_code}</strong></p>}
      <p className="muted">
        {consolidation.total_weight_grams} g · {consolidation.total_volume_cbm} m³
        {consolidation.freight_method ? ` · ${consolidation.freight_method}` : ""}
        {consolidation.freight_provider ? ` (${consolidation.freight_provider})` : ""}
      </p>
      {consolidation.carrier && (
        <p className="muted">
          Carrier: {consolidation.carrier} {consolidation.carrier_tracking_reference ? `(${consolidation.carrier_tracking_reference})` : ""}
          {consolidation.current_location ? ` · Currently: ${consolidation.current_location}` : ""}
        </p>
      )}
      {consolidation.departure_date && <p className="muted">Departed {new Date(consolidation.departure_date).toLocaleString()}</p>}
      {consolidation.arrival_date && <p className="muted">Arrived {new Date(consolidation.arrival_date).toLocaleString()}</p>}

      <div className="link-row" style={{ marginTop: "1rem" }}>
        {consolidation.status === "OPEN" && (
          <button type="button" disabled={readyForExport.isPending || consolidation.package_count === 0} onClick={() => readyForExport.mutate()}>
            {readyForExport.isPending ? "Marking..." : "Mark Ready for Export"}
          </button>
        )}
        {consolidation.status === "READY_FOR_EXPORT" && (
          <button type="button" disabled={depart.isPending} onClick={() => depart.mutate()}>
            {depart.isPending ? "Marking..." : "Mark Departed"}
          </button>
        )}
        {consolidation.status === "IN_TRANSIT" && (
          <button type="button" disabled={arriveKenya.isPending} onClick={() => arriveKenya.mutate()}>
            {arriveKenya.isPending ? "Marking..." : "Mark Arrived in Kenya"}
          </button>
        )}
      </div>
      {readyForExport.isError && <p className="error">{getErrorDetail(readyForExport.error) ?? "Could not update status."}</p>}
      {depart.isError && <p className="error">{getErrorDetail(depart.error) ?? "Could not update status."}</p>}
      {arriveKenya.isError && <p className="error">{getErrorDetail(arriveKenya.error) ?? "Could not update status."}</p>}

      {consolidation.status === "DEPARTED" && (
        <>
          <h2>Confirm Carrier &amp; Transit</h2>
          <form
            className="link-row"
            onSubmit={(e) => {
              e.preventDefault();
              markInTransit.mutate({ carrier: carrier || undefined, carrierTrackingReference: carrierRef || undefined, currentLocation: location || undefined });
            }}
          >
            <input placeholder="Carrier" value={carrier} onChange={(e) => setCarrier(e.target.value)} />
            <input placeholder="Carrier tracking reference" value={carrierRef} onChange={(e) => setCarrierRef(e.target.value)} />
            <input placeholder="Current location" value={location} onChange={(e) => setLocation(e.target.value)} />
            <button type="submit" disabled={markInTransit.isPending}>{markInTransit.isPending ? "Saving..." : "Mark In Transit"}</button>
          </form>
          {markInTransit.isError && <p className="error">{getErrorDetail(markInTransit.error) ?? "Could not mark in transit."}</p>}
        </>
      )}

      {consolidation.status === "IN_TRANSIT" && (
        <>
          <h2>Transit Update</h2>
          <form
            className="link-row"
            onSubmit={(e) => { e.preventDefault(); transitUpdate.mutate({ currentLocation: location || undefined }); }}
          >
            <input placeholder="Current location" value={location} onChange={(e) => setLocation(e.target.value)} />
            <button type="submit" disabled={transitUpdate.isPending}>{transitUpdate.isPending ? "Saving..." : "Save Update"}</button>
          </form>
          {transitUpdate.isError && <p className="error">{getErrorDetail(transitUpdate.error) ?? "Could not save update."}</p>}
        </>
      )}

      <h2>Report Exception</h2>
      <form
        className="link-row"
        onSubmit={(e) => {
          e.preventDefault();
          reportException.mutate(
            { exceptionType, severity: "HIGH", description: exceptionNotes || undefined },
            { onSuccess: () => setExceptionNotes("") }
          );
        }}
      >
        <select value={exceptionType} onChange={(e) => setExceptionType(e.target.value)}>
          {EXCEPTION_TYPES.map((t) => <option key={t} value={t}>{t.replaceAll("_", " ")}</option>)}
        </select>
        <input placeholder="Description" value={exceptionNotes} onChange={(e) => setExceptionNotes(e.target.value)} />
        <button type="submit" disabled={reportException.isPending}>{reportException.isPending ? "Reporting..." : "Report Exception"}</button>
      </form>
      {reportException.isError && <p className="error">{getErrorDetail(reportException.error) ?? "Could not report exception."}</p>}
      {reportException.isSuccess && <p className="muted">Exception reported.</p>}

      <h2>Packages ({consolidation.package_count})</h2>
      <table className="page-table">
        <thead><tr><th>Package</th><th>Tracking #</th><th>Status</th><th>Weight</th>{isOpen && <th></th>}</tr></thead>
        <tbody>
          {consolidation.packages.map((p) => (
            <tr key={p.id}>
              <td>{p.package_code}</td>
              <td>{p.tracking_number}</td>
              <td><span className="badge">{p.status.replaceAll("_", " ")}</span></td>
              <td>{p.weight_grams != null ? `${p.weight_grams} g` : "-"}</td>
              {isOpen && (
                <td>
                  <button type="button" className="danger" disabled={removePackage.isPending} onClick={() => removePackage.mutate(p.id)}>
                    Remove
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
      {consolidation.packages.length === 0 && <p>No packages in this consolidation yet.</p>}
      {removePackage.isError && <p className="error">{getErrorDetail(removePackage.error) ?? "Could not remove package."}</p>}
    </div>
  );
}

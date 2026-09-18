import { useEffect, useState } from "react";
import { Link } from "react-router";
import {
  getErrorDetail,
  useAddPackageToConsolidation,
  useConsolidations,
  useCreateConsolidation,
  usePackages,
} from "./hooks";

// Lists every package that has passed QC and is waiting to be batched, and
// lets staff assign each one into an open consolidation - creating one
// first if none is open yet.
export function ConsolidationQueuePage() {
  const { data: packagesPage, isLoading } = usePackages({ status: "READY_FOR_CONSOLIDATION", page: 1 });
  const { data: openConsolidations } = useConsolidations({ status: "OPEN", page: 1 });
  const createConsolidation = useCreateConsolidation();

  const [selectedConsolidationId, setSelectedConsolidationId] = useState("");

  useEffect(() => {
    if (!selectedConsolidationId && openConsolidations?.consolidations.length) {
      setSelectedConsolidationId(openConsolidations.consolidations[0].id);
    }
  }, [openConsolidations, selectedConsolidationId]);

  useEffect(() => {
    if (createConsolidation.data) setSelectedConsolidationId(createConsolidation.data.id);
  }, [createConsolidation.data]);

  const addPackage = useAddPackageToConsolidation(selectedConsolidationId);

  return (
    <div className="page">
      <h1>Consolidation Queue</h1>
      <p className="muted">Packages that have passed QC and are ready to be grouped into a freight batch.</p>

      <div className="filter-bar">
        <select value={selectedConsolidationId} onChange={(e) => setSelectedConsolidationId(e.target.value)}>
          <option value="">Select a consolidation...</option>
          {openConsolidations?.consolidations.map((c) => (
            <option key={c.id} value={c.id}>{c.consolidation_code} ({c.package_count} packages)</option>
          ))}
        </select>
        <button type="button" disabled={createConsolidation.isPending} onClick={() => createConsolidation.mutate({})}>
          {createConsolidation.isPending ? "Creating..." : "New Consolidation"}
        </button>
        {selectedConsolidationId && <Link to={`/warehouse/consolidations/${selectedConsolidationId}`}>View selected →</Link>}
      </div>
      {addPackage.isError && <p className="error">{getErrorDetail(addPackage.error) ?? "Could not add package."}</p>}

      {isLoading ? <p>Loading...</p> : (
        <table className="page-table">
          <thead><tr><th>Package</th><th>Tracking #</th><th>Weight</th><th></th></tr></thead>
          <tbody>
            {packagesPage?.packages.map((p) => (
              <tr key={p.id}>
                <td>{p.package_code}</td>
                <td>{p.tracking_number}</td>
                <td>{p.weight_grams != null ? `${p.weight_grams} g` : "-"}</td>
                <td>
                  <button
                    type="button"
                    disabled={!selectedConsolidationId || addPackage.isPending}
                    onClick={() => addPackage.mutate(p.id)}
                  >
                    Add to Consolidation
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {packagesPage?.packages.length === 0 && <p>No packages waiting for consolidation.</p>}
    </div>
  );
}

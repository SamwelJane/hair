import { useState } from "react";
import { Link } from "react-router";
import { useConsolidations } from "./hooks";

const STATUSES = ["OPEN", "READY_FOR_EXPORT", "DEPARTED", "IN_TRANSIT", "ARRIVED", "CLOSED"];

export function ConsolidationsListPage() {
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const { data, isLoading } = useConsolidations({ status: status || undefined, page });

  return (
    <div className="page">
      <h1>Consolidations</h1>
      <div className="filter-bar">
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s.replaceAll("_", " ")}</option>)}
        </select>
      </div>

      {isLoading ? <p>Loading...</p> : (
        <table className="page-table">
          <thead><tr><th>Code</th><th>Status</th><th>Packages</th><th>Weight</th><th>Volume</th></tr></thead>
          <tbody>
            {data?.consolidations.map((c) => (
              <tr key={c.id}>
                <td><Link to={`/warehouse/consolidations/${c.id}`}>{c.consolidation_code}</Link></td>
                <td><span className="badge">{c.status.replaceAll("_", " ")}</span></td>
                <td>{c.package_count}</td>
                <td>{c.total_weight_grams} g</td>
                <td>{c.total_volume_cbm} m³</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {data?.consolidations.length === 0 && <p>No consolidations found.</p>}

      {data && data.total > data.page_size && (
        <div className="pagination">
          <button type="button" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>Previous</button>
          <span>Page {page}</span>
          <button type="button" disabled={page * data.page_size >= data.total} onClick={() => setPage((p) => p + 1)}>Next</button>
        </div>
      )}
    </div>
  );
}

import { useState } from "react";
import { Link } from "react-router";
import { usePackages } from "./hooks";

const STATUSES = [
  "EXPECTED",
  "RECEIVED",
  "READY_FOR_CONSOLIDATION",
  "CONSOLIDATED",
  "IN_TRANSIT",
  "AT_CUSTOMS_KENYA",
  "READY_FOR_DELIVERY",
  "DELIVERED",
  "EXCEPTION",
];

export function PackageRegistryPage() {
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const { data, isLoading } = usePackages({ q: q || undefined, status: status || undefined, page });

  return (
    <div className="page">
      <h1>Package Registry</h1>
      <div className="filter-bar">
        <input
          placeholder="Search by package code"
          value={q}
          onChange={(e) => { setQ(e.target.value); setPage(1); }}
        />
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s.replaceAll("_", " ")}</option>)}
        </select>
      </div>

      {isLoading ? <p>Loading...</p> : (
        <table className="page-table">
          <thead>
            <tr><th>Package</th><th>Tracking #</th><th>Status</th><th>QC</th><th>Weight</th></tr>
          </thead>
          <tbody>
            {data?.packages.map((p) => (
              <tr key={p.id}>
                <td><Link to={`/warehouse/packages/${p.id}`}>{p.package_code}</Link></td>
                <td>{p.tracking_number}</td>
                <td><span className="badge">{p.status.replaceAll("_", " ")}</span></td>
                <td>{p.qc_status}</td>
                <td>{p.weight_grams != null ? `${p.weight_grams} g` : "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {data?.packages.length === 0 && <p>No packages found.</p>}

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

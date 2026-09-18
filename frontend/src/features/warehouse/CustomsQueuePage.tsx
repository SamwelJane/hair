import { useState } from "react";
import { Link } from "react-router";
import { useCustomsDeclarations } from "./hooks";

const STATUSES = ["PREPARING", "DECLARED", "QUERY_RAISED", "CLEARED"];

export function CustomsQueuePage() {
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const { data, isLoading } = useCustomsDeclarations({ status: status || undefined, page });

  return (
    <div className="page">
      <h1>Customs</h1>
      <div className="filter-bar">
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s.replaceAll("_", " ")}</option>)}
        </select>
      </div>

      {isLoading ? <p>Loading...</p> : (
        <table className="page-table">
          <thead><tr><th>Consolidation</th><th>HS Code</th><th>Declared Value</th><th>Status</th></tr></thead>
          <tbody>
            {data?.declarations.map((d) => (
              <tr key={d.id}>
                <td><Link to={`/warehouse/customs/${d.id}`}>{d.consolidation_code ?? d.id}</Link></td>
                <td>{d.hs_code ?? "-"}</td>
                <td>{d.declared_value_usd != null ? `$${d.declared_value_usd}` : "-"}</td>
                <td><span className="badge">{d.status.replaceAll("_", " ")}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {data?.declarations.length === 0 && <p>No customs declarations found.</p>}

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

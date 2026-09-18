import { useState } from "react";
import { downloadAuditLogExport, useAuditLogs } from "./hooks";

export function AdminAuditLogsPage() {
  const [action, setAction] = useState("");
  const [entityType, setEntityType] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [page, setPage] = useState(1);

  const filters = { action: action || undefined, entity_type: entityType || undefined, from: from || undefined, to: to || undefined, page };
  const { data, isLoading } = useAuditLogs(filters);

  return (
    <div className="page">
      <div className="link-row" style={{ justifyContent: "space-between" }}>
        <h1>Audit Logs</h1>
        <button type="button" onClick={() => void downloadAuditLogExport(filters)}>Export CSV</button>
      </div>

      <div className="filter-bar">
        <input placeholder="Action contains..." value={action} onChange={(e) => { setAction(e.target.value); setPage(1); }} />
        <select value={entityType} onChange={(e) => { setEntityType(e.target.value); setPage(1); }}>
          <option value="">All entity types</option>
          {data?.entity_types.map((et) => <option key={et} value={et}>{et}</option>)}
        </select>
        <input type="date" value={from} onChange={(e) => { setFrom(e.target.value); setPage(1); }} />
        <input type="date" value={to} onChange={(e) => { setTo(e.target.value); setPage(1); }} />
      </div>

      {isLoading ? <p>Loading...</p> : (
        <table className="page-table">
          <thead><tr><th>When</th><th>Actor</th><th>Action</th><th>Entity</th><th>Details</th></tr></thead>
          <tbody>
            {data?.items.map((log) => (
              <tr key={log.id} className={log.action.startsWith("FRAUD_FLAG") ? "flagged-row" : ""}>
                <td>{new Date(log.created_at).toLocaleString()}</td>
                <td>{log.user_email ?? "system"}</td>
                <td>{log.action}</td>
                <td>{log.entity_type}:{log.entity_id.slice(0, 8)}</td>
                <td className="muted">{log.metadata ? JSON.stringify(log.metadata) : ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {data?.items.length === 0 && <p>No audit log entries match your filters.</p>}

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

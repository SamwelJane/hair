import { useState } from "react";
import { Link } from "react-router";
import { useExternalShipments } from "./hooks";

export function ExternalShipmentsListPage() {
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const { data, isLoading } = useExternalShipments({ q: q || undefined, page });

  return (
    <div className="page">
      <h1>External Shipments</h1>
      <div className="filter-bar">
        <input
          placeholder="Search by tracking number or phone"
          value={q}
          onChange={(e) => { setQ(e.target.value); setPage(1); }}
        />
        <Link to="/warehouse/external-shipments/new"><button type="button">New External Shipment</button></Link>
      </div>

      {isLoading ? <p>Loading...</p> : (
        <table className="page-table">
          <thead><tr><th>Tracking #</th><th>Customer</th><th>Phone</th><th>Status</th></tr></thead>
          <tbody>
            {data?.external_shipments.map((s) => (
              <tr key={s.id}>
                <td><Link to={`/warehouse/external-shipments/${s.id}`}>{s.tracking_number}</Link></td>
                <td>{s.customer_name}</td>
                <td>{s.customer_phone}</td>
                <td><span className="badge">{s.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {data?.external_shipments.length === 0 && <p>No external shipments found.</p>}

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

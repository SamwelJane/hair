import { Link } from "react-router";
import { useWarehouseDashboard } from "./hooks";

export function WarehouseDashboardPage() {
  const { data: kpis, isLoading } = useWarehouseDashboard();

  if (isLoading) return <div className="page">Loading...</div>;

  return (
    <div className="page">
      <h1>Dashboard</h1>

      <h2>Needs Action</h2>
      <div className="product-grid">
        <Tile label="Pending QC" value={kpis?.pending_qc} />
        <Tile label="Pending Weighing" value={kpis?.pending_weighing} />
        <Tile label="Pending Labeling" value={kpis?.pending_labeling} />
        <Tile label="Exceptions" value={kpis?.exceptions} />
      </div>

      <h2 style={{ marginTop: "1.5rem" }}>In Progress</h2>
      <div className="product-grid">
        <Tile label="Ready for Consolidation" value={kpis?.ready_for_consolidation} />
        <Tile label="Active Consolidations" value={kpis?.active_consolidations} />
        <Tile label="Consolidated" value={kpis?.consolidated} />
      </div>

      <h2 style={{ marginTop: "1.5rem" }}>Completed</h2>
      <div className="product-grid">
        <Tile label="Received Today" value={kpis?.received_today} />
        <Tile label="Damaged Packages" value={kpis?.damaged} />
      </div>

      <p style={{ marginTop: "1.5rem" }} className="link-row">
        <Link to="/warehouse/receive">Receive a package →</Link>
        <Link to="/warehouse/consolidation-queue">Consolidation queue →</Link>
      </p>
    </div>
  );
}

function Tile({ label, value }: { label: string; value: number | undefined }) {
  return (
    <div className="product-card">
      <div style={{ padding: "1rem" }}>
        <p className="muted">{label}</p>
        <p className="total">{value ?? 0}</p>
      </div>
    </div>
  );
}

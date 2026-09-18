import { Link, Outlet } from "react-router";
import { useAuth } from "../lib/auth/AuthContext";

// One shared shell for both WAREHOUSE (Vietnam) and KENYA_OPS staff, nav
// filtered by role - mirrors AdminLayout/SupplierLayout's pattern. WAREHOUSE
// has read-only access to Customs (declared/cleared there, but only
// KENYA_OPS/ADMIN/STAFF can actually act on it - see
// backend/app/core/permissions.py).
const WAREHOUSE_LINKS = [
  { href: "/warehouse", label: "Dashboard" },
  { href: "/warehouse/receive", label: "Receive Package" },
  { href: "/warehouse/external-shipments/new", label: "New External Shipment" },
  { href: "/warehouse/external-shipments", label: "External Shipments" },
  { href: "/warehouse/packages", label: "Package Registry" },
  { href: "/warehouse/consolidation-queue", label: "Consolidation Queue" },
  { href: "/warehouse/consolidations", label: "Consolidations" },
  { href: "/warehouse/customs", label: "Customs" },
];

const KENYA_OPS_LINKS = [
  { href: "/warehouse", label: "Dashboard" },
  { href: "/warehouse/external-shipments", label: "External Shipments" },
  { href: "/warehouse/packages", label: "Package Registry" },
  { href: "/warehouse/consolidations", label: "Consolidations" },
  { href: "/warehouse/customs", label: "Customs" },
];

export function WarehouseLayout() {
  const { user, logout } = useAuth();
  const links = user?.role === "KENYA_OPS" ? KENYA_OPS_LINKS : WAREHOUSE_LINKS;

  return (
    <div className="app-shell">
      <header className="site-header">
        <Link to="/warehouse" className="brand">
          {user?.role === "KENYA_OPS" ? "Kenya Operations" : "Cherubim Warehouse"}
        </Link>
        <nav>
          <span className="muted">{user?.email} ({user?.role})</span>
          <button type="button" className="link-button" onClick={() => void logout()}>Sign out</button>
        </nav>
      </header>
      <nav className="admin-subnav">
        {links.map((link) => <Link key={link.href} to={link.href}>{link.label}</Link>)}
      </nav>
      <main className="site-main">
        <Outlet />
      </main>
    </div>
  );
}

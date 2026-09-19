import { NavLink, Outlet } from "react-router";
import { useAuth } from "../lib/auth/AuthContext";

const WAREHOUSE_LINKS = [
  { href: "/warehouse", label: "📊 Dashboard", end: true },
  { href: "/warehouse/receive", label: "📥 Receive Package" },
  { href: "/warehouse/packages", label: "📦 Package Registry" },
  { href: "/warehouse/external-shipments/new", label: "➕ New External Shipment" },
  { href: "/warehouse/external-shipments", label: "🚢 External Shipments" },
  { href: "/warehouse/consolidation-queue", label: "🗂️ Consolidation Queue" },
  { href: "/warehouse/consolidations", label: "📋 Consolidations" },
  { href: "/warehouse/customs", label: "🏛️ Customs" },
  { href: "/warehouse", label: "Dashboard", end: true },
  { href: "/warehouse/receive", label: "Receive Package" },
  { href: "/warehouse/packages", label: "Package Registry" },
  { href: "/warehouse/external-shipments/new", label: "New External Shipment" },
  { href: "/warehouse/external-shipments", label: "External Shipments" },
  { href: "/warehouse/consolidation-queue", label: "Consolidation Queue" },
  { href: "/warehouse/consolidations", label: "Consolidations" },
  { href: "/warehouse/customs", label: "Customs" },
];

const KENYA_OPS_LINKS = [
  { href: "/warehouse", label: "📊 Dashboard", end: true },
  { href: "/warehouse/external-shipments", label: "🚢 External Shipments" },
  { href: "/warehouse/packages", label: "📦 Package Registry" },
  { href: "/warehouse/consolidations", label: "📋 Consolidations" },
  { href: "/warehouse/customs", label: "🏛️ Customs" },
  { href: "/warehouse", label: "Dashboard", end: true },
  { href: "/warehouse/external-shipments", label: "External Shipments" },
  { href: "/warehouse/packages", label: "Package Registry" },
  { href: "/warehouse/consolidations", label: "Consolidations" },
  { href: "/warehouse/customs", label: "Customs" },
];

/** Warehouse / Kenya Ops portal — left sidebar navigation layout.
 *
 * WAREHOUSE role = Vietnam fulfilment (receive, QC, consolidate, ship).
 * KENYA_OPS role = Kenya inbound (customs, delivery, exception management).
 * Nav is filtered by role — each sees only what's relevant to their station.
 */
export function WarehouseLayout() {
  const { user, logout } = useAuth();
  const links = user?.role === "KENYA_OPS" ? KENYA_OPS_LINKS : WAREHOUSE_LINKS;
  const portalTitle = user?.role === "KENYA_OPS" ? "Kenya Operations" : "Cherubim Warehouse";

  return (
    <div className="portal-shell">
      {/* ── Left sidebar ─────────────────────────────────────────────────── */}
      <aside className="portal-sidebar">
        <div className="portal-sidebar__brand">
          <span>Hiar Business</span>
          <small>{portalTitle}</small>
        </div>

        <nav className="portal-sidebar__nav" aria-label="Warehouse navigation">
          {links.map((link) => (
            <NavLink
              key={link.href}
              to={link.href}
              end={link.end}
              className={({ isActive }) =>
                ["portal-sidebar__link", isActive ? "portal-sidebar__link--active" : ""].join(" ").trim()
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="portal-sidebar__footer">
          <span className="portal-sidebar__user">{user?.email}</span>
          <span className="portal-sidebar__role">{user?.role}</span>
          <button type="button" className="portal-sidebar__signout" onClick={() => void logout()}>
            Sign out
          </button>
        </div>
      </aside>

      {/* ── Main content area ────────────────────────────────────────────── */}
      <main className="portal-main">
        <Outlet />
      </main>
    </div>
  );
}

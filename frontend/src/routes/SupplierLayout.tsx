import { NavLink, Outlet } from "react-router";
import { useAuth } from "../lib/auth/AuthContext";

const LINKS = [
  { href: "/supplier/orders", label: "My Orders" },
  { href: "/supplier/products", label: "My Products" },
  { href: "/supplier/promotions", label: "Promotions" },
];

/** Supplier portal — left sidebar navigation layout. */
export function SupplierLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="portal-shell">
      {/* ── Left sidebar ─────────────────────────────────────────────────── */}
      <aside className="portal-sidebar">
        <div className="portal-sidebar__brand">
          <span>Hiar Business</span>
          <small>Supplier Portal</small>
        </div>

        <nav className="portal-sidebar__nav" aria-label="Supplier navigation">
          {LINKS.map((link) => (
            <NavLink
              key={link.href}
              to={link.href}
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

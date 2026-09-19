import { NavLink, Outlet } from "react-router";
import { useAuth } from "../lib/auth/AuthContext";

const LINKS = [
  { href: "/admin", label: "📊 Dashboard", end: true },
  { href: "/admin/orders", label: "🛒 Orders" },
  { href: "/admin/payments", label: "💳 Payments" },
  { href: "/admin/promotions", label: "🎯 Promotions" },
  { href: "/admin/products", label: "💇 Products" },
  { href: "/admin/categories", label: "🏷️ Categories" },
  { href: "/admin/suppliers", label: "🏭 Suppliers" },
  { href: "/admin/homepage/banners", label: "🖼️ Homepage Banners" },
  { href: "/admin/homepage/products", label: "⭐ Featured Products" },
  { href: "/admin/returns", label: "↩️ Returns" },
  { href: "/admin/reviews", label: "⭐ Reviews" },
  { href: "/admin/analytics", label: "📈 Analytics" },
  { href: "/admin/users", label: "👥 Users" },
  { href: "/admin/audit-logs", label: "🔍 Audit Logs" },
  { href: "/admin/settings/pricing", label: "⚙️ Pricing" },
  { href: "/admin/settings/exchange-rate", label: "💱 Exchange Rate" },
  { href: "/admin/settings/shipping-rules", label: "🚚 Shipping Rules" },
  { href: "/admin/settings/discount-codes", label: "🎟️ Discount Codes" },
  { href: "/admin", label: "Dashboard", end: true },
  { href: "/admin/orders", label: "Orders" },
  { href: "/admin/payments", label: "Payments" },
  { href: "/admin/promotions", label: "Promotions" },
  { href: "/admin/products", label: "Products" },
  { href: "/admin/categories", label: "Categories" },
  { href: "/admin/suppliers", label: "Suppliers" },
  { href: "/admin/homepage/banners", label: "Homepage Banners" },
  { href: "/admin/homepage/products", label: "Featured Products" },
  { href: "/admin/returns", label: "Returns" },
  { href: "/admin/reviews", label: "Reviews" },
  { href: "/admin/analytics", label: "Analytics" },
  { href: "/admin/users", label: "Users" },
  { href: "/admin/audit-logs", label: "Audit Logs" },
  { href: "/admin/settings/pricing", label: "Pricing" },
  { href: "/admin/settings/exchange-rate", label: "Exchange Rate" },
  { href: "/admin/settings/shipping-rules", label: "Shipping Rules" },
  { href: "/admin/settings/discount-codes", label: "Discount Codes" },
];

/** Admin portal — left sidebar navigation layout. */
export function AdminLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="portal-shell">
      {/* ── Left sidebar ─────────────────────────────────────────────────── */}
      <aside className="portal-sidebar">
        <div className="portal-sidebar__brand">
          <span>Hiar Business</span>
          <small>Admin</small>
        </div>

        <nav className="portal-sidebar__nav" aria-label="Admin navigation">
          {LINKS.map((link) => (
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

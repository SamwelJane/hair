import { Link, Outlet } from "react-router";
import { useAuth } from "../lib/auth/AuthContext";

const LINKS = [
  { href: "/admin", label: "Dashboard" },
  { href: "/admin/products", label: "Products" },
  { href: "/admin/categories", label: "Categories" },
  { href: "/admin/homepage/banners", label: "Homepage Banners" },
  { href: "/admin/homepage/products", label: "Homepage Products" },
  { href: "/admin/suppliers", label: "Suppliers" },
  { href: "/admin/orders", label: "Orders" },
  { href: "/admin/returns", label: "Returns" },
  { href: "/admin/reviews", label: "Reviews" },
  { href: "/admin/payments", label: "Payments" },
  { href: "/admin/analytics", label: "Analytics" },
  { href: "/admin/audit-logs", label: "Audit Logs" },
  { href: "/admin/users", label: "Users" },
  { href: "/admin/settings/exchange-rate", label: "Exchange Rate" },
  { href: "/admin/settings/pricing", label: "Pricing Settings" },
  { href: "/admin/settings/shipping-rules", label: "Shipping Rules" },
  { href: "/admin/settings/discount-codes", label: "Discount Codes" },
];

export function AdminLayout() {
  const { user, logout } = useAuth();
  return (
    <div className="app-shell">
      <header className="site-header">
        <Link to="/admin" className="brand">Hiar Business Admin</Link>
        <nav>
          <span className="muted">{user?.email} ({user?.role})</span>
          <button type="button" className="link-button" onClick={() => void logout()}>Sign out</button>
        </nav>
      </header>
      <nav className="admin-subnav">
        {LINKS.map((link) => <Link key={link.href} to={link.href}>{link.label}</Link>)}
      </nav>
      <main className="site-main">
        <Outlet />
      </main>
    </div>
  );
}

import { useState } from "react";
import { Link, Outlet, useNavigate } from "react-router";
import { useAuth } from "../lib/auth/AuthContext";
import { useCart } from "../features/cart/hooks";

const ADMIN_ROLES = ["ADMIN", "STAFF"];
const WAREHOUSE_PORTAL_ROLES = ["WAREHOUSE", "KENYA_OPS"];

export function StorefrontLayout() {
  const { user, isAuthenticated, logout } = useAuth();
  const { data: cart } = useCart();
  const itemCount = cart?.items.reduce((sum, i) => sum + i.quantity, 0) ?? 0;
  const navigate = useNavigate();
  const [search, setSearch] = useState("");

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    navigate(search ? `/products?q=${encodeURIComponent(search)}` : "/products");
  }

  return (
    <div className="app-shell">
      <header className="site-header">
        <Link to="/" className="brand">Hiar Business</Link>
        <form className="site-search" onSubmit={handleSearch}>
          <input
            type="search"
            placeholder="Search products..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </form>
        <nav>
          <Link to="/products">Shop</Link>
          <Link to="/cart">Cart{itemCount > 0 ? ` (${itemCount})` : ""}</Link>
          {isAuthenticated ? (
            <>
              {user?.role === "SUPPLIER" && <Link to="/supplier">Supplier Portal</Link>}
              {user && WAREHOUSE_PORTAL_ROLES.includes(user.role) && <Link to="/warehouse">Warehouse</Link>}
              {user && ADMIN_ROLES.includes(user.role) && <Link to="/admin">Admin</Link>}
              <Link to="/account">{user?.name ?? "Account"}</Link>
              <button type="button" className="link-button" onClick={() => void logout()}>Log out</button>
            </>
          ) : (
            <Link to="/login">Log in</Link>
          )}
        </nav>
      </header>
      <main className="site-main">
        <Outlet />
      </main>
      <footer className="site-footer">
        <p>&copy; {new Date().getFullYear()} Hiar Business</p>
      </footer>
    </div>
  );
}

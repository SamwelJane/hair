import { Link, Outlet } from "react-router";
import { useAuth } from "../lib/auth/AuthContext";

export function SupplierLayout() {
  const { user, logout } = useAuth();
  return (
    <div className="app-shell">
      <header className="site-header">
        <Link to="/supplier" className="brand">Supplier Portal</Link>
        <nav>
          <Link to="/supplier/orders">Orders</Link>
          <Link to="/supplier/products">Products</Link>
          <span className="muted">{user?.email}</span>
          <button type="button" className="link-button" onClick={() => void logout()}>Log out</button>
        </nav>
      </header>
      <main className="site-main">
        <Outlet />
      </main>
    </div>
  );
}

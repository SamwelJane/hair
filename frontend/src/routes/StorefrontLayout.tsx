import { useState } from "react";
import { Link, Outlet, useNavigate } from "react-router";
import { useAuth } from "../lib/auth/AuthContext";
import { useCart } from "../features/cart/hooks";

const ADMIN_ROLES = ["ADMIN", "STAFF"];
const WAREHOUSE_PORTAL_ROLES = ["WAREHOUSE", "KENYA_OPS"];

/** Storefront — top navigation bar.
 *
 * Whitelabeling rules (per spec):
 *  • No supplier names, supplier links, or "filter by supplier" anywhere
 *  • No internal fulfilment details visible to customers
 *  • Lang switcher placeholder for i18n (en / sw / fr)
 */
export function StorefrontLayout() {
  const { user, isAuthenticated, logout } = useAuth();
  const { data: cart } = useCart();
  const itemCount = cart?.items.reduce((sum, i) => sum + i.quantity, 0) ?? 0;
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    navigate(search ? `/products?q=${encodeURIComponent(search)}` : "/products");
    setMenuOpen(false);
  }

  return (
    <div className="sf-shell">
      {/* ── Top navigation bar ─────────────────────────────────────────────── */}
      <header className="sf-topnav">
        <div className="sf-topnav__inner">
          {/* Brand */}
          <Link to="/" className="sf-topnav__brand">
            <span className="sf-topnav__brand-text">Hiar Business</span>
          </Link>

          {/* Search bar */}
          <form className="sf-topnav__search" onSubmit={handleSearch}>
            <input
              type="search"
              placeholder="Search wigs, extensions, bulk hair…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Search products"
            />
            <button type="submit" aria-label="Search">🔍</button>
          </form>

          {/* Right actions */}
          <nav className="sf-topnav__actions" aria-label="Site navigation">
            <Link to="/products">Shop</Link>
            <Link to="/cart" aria-label={`Cart, ${itemCount} items`}>
              🛒{itemCount > 0 && <span className="sf-topnav__badge">{itemCount}</span>}
            </Link>

            {isAuthenticated ? (
              <>
                {/* Portal shortcuts — only for staff roles, never in customer view */}
                {user?.role === "SUPPLIER" && <Link to="/supplier">Supplier Portal</Link>}
                {user && WAREHOUSE_PORTAL_ROLES.includes(user.role) && <Link to="/warehouse">Warehouse</Link>}
                {user && ADMIN_ROLES.includes(user.role) && <Link to="/admin">Admin</Link>}
                <Link to="/account">{user?.name ?? "Account"}</Link>
                <button type="button" className="sf-topnav__link-btn" onClick={() => void logout()}>
                  Log out
                </button>
              </>
            ) : (
              <Link to="/login">Log in</Link>
            )}
          </nav>

          {/* Mobile hamburger */}
          <button
            type="button"
            className="sf-topnav__hamburger"
            aria-label="Toggle menu"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((o) => !o)}
          >
            {menuOpen ? "✕" : "☰"}
          </button>
        </div>

        {/* Mobile drawer */}
        {menuOpen && (
          <nav className="sf-topnav__mobile-drawer" aria-label="Mobile navigation">
            <form className="sf-topnav__search" onSubmit={handleSearch}>
              <input
                type="search"
                placeholder="Search products…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              <button type="submit">Search</button>
            </form>
            <Link to="/products" onClick={() => setMenuOpen(false)}>Shop</Link>
            <Link to="/cart" onClick={() => setMenuOpen(false)}>
              Cart{itemCount > 0 ? ` (${itemCount})` : ""}
            </Link>
            {isAuthenticated ? (
              <>
                <Link to="/account" onClick={() => setMenuOpen(false)}>My Account</Link>
                <button type="button" className="sf-topnav__link-btn" onClick={() => { void logout(); setMenuOpen(false); }}>
                  Log out
                </button>
              </>
            ) : (
              <Link to="/login" onClick={() => setMenuOpen(false)}>Log in</Link>
            )}
          </nav>
        )}
      </header>

      {/* ── Page content ────────────────────────────────────────────────────── */}
      <main className="sf-main">
        <Outlet />
      </main>

      {/* ── Footer ──────────────────────────────────────────────────────────── */}
      <footer className="sf-footer">
        <div className="sf-footer__inner">
          <div className="sf-footer__col">
            <strong>Hiar Business</strong>
            <p>Premium Vietnamese hair delivered to Kenya.</p>
          </div>
          <div className="sf-footer__col">
            <strong>Shop</strong>
            <Link to="/products">All Products</Link>
            <Link to="/products?category=Wigs">Wigs</Link>
            <Link to="/products?category=Extensions">Extensions</Link>
            <Link to="/products?category=Bulk+Hair">Bulk Hair</Link>
          </div>
          <div className="sf-footer__col">
            <strong>Help</strong>
            <Link to="/track/:trackingNumber">Track Order</Link>
            <Link to="/login">My Account</Link>
          </div>
          <div className="sf-footer__col">
            <strong>Payment</strong>
            <p>Equity Bank Paybill: <strong>247247</strong></p>
            <p>Account: <strong>0310173604563</strong></p>
          </div>
        </div>
        <p className="sf-footer__copy">&copy; {new Date().getFullYear()} Hiar Business. All rights reserved.</p>
      </footer>
    </div>
  );
}

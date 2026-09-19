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
            <button type="submit" aria-label="Search">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            </button>
          </form>

          {/* Right actions */}
          <nav className="sf-topnav__actions" aria-label="Site navigation">
            <Link to="/products">Shop</Link>
            <Link to="/cart" aria-label={`Cart, ${itemCount} items`} style={{ display: "inline-flex", alignItems: "center", gap: "0.25rem" }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path></svg>
              {itemCount > 0 && <span className="sf-topnav__badge">{itemCount}</span>}
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
            {menuOpen ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
            )}
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
            <strong>Support</strong>
            <Link to="/track">Track Order</Link>
            <Link to="/login">My Account</Link>
          </div>
          <div className="sf-footer__col">
            <strong>Contact</strong>
            <p>support@hiarbusiness.com</p>
            <p>Nairobi, Kenya</p>
          </div>
        </div>
        <p className="sf-footer__copy">&copy; 2026 Hiar Business Ltd. All rights reserved.</p>
      </footer>
    </div>
  );
}

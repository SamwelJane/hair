import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";
import { useAuth, AuthRequestError } from "../../lib/auth/AuthContext";
import { useMergeGuestCartOnLogin } from "../cart/hooks";
import { getGuestCartToken } from "../../lib/cart/guestCartToken";

export function LoginPage() {
  const { login } = useAuth();
  const { login, user } = useAuth();
  const mergeCart = useMergeGuestCartOnLogin();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
  function getDestinationForRole(role?: string) {
    const callbackUrl = searchParams.get("callbackUrl");
    if (callbackUrl) return decodeURIComponent(callbackUrl);
    if (role === "ADMIN" || role === "STAFF") return "/admin";
    if (role === "SUPPLIER") return "/supplier";
    if (role === "WAREHOUSE" || role === "KENYA_OPS") return "/warehouse";
    return "/account";
  }

  async function performLogin(targetEmail: string, targetPass: string) {
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      await login(targetEmail, targetPass);
      if (getGuestCartToken()) await mergeCart.mutateAsync().catch(() => undefined);
      const callbackUrl = searchParams.get("callbackUrl");
      navigate(callbackUrl ? decodeURIComponent(callbackUrl) : "/account");
      // Wait a tick for user state to populate if needed
      setTimeout(() => {
        const dest = getDestinationForRole(user?.role);
        navigate(dest);
      }, 100);
    } catch (err) {
      setError(err instanceof AuthRequestError ? err.message : "Login failed. Please try again.");
      setError(err instanceof AuthRequestError ? err.message : "Login failed. Please check credentials.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await performLogin(email, password);
  }

  return (
    <div className="page narrow">
      <h1>Log in</h1>
      <h1>Sign In to Hiar Business</h1>
      <p className="muted">Enter your account credentials or select a role below for instant access.</p>

      {/* Quick Access Role Buttons for Testing */}
      <div style={{ margin: "1.25rem 0", padding: "1rem", background: "#f5f0eb", borderRadius: "8px", border: "1px solid #e4dcd6" }}>
        <p style={{ fontWeight: 700, fontSize: "0.85rem", margin: "0 0 0.5rem", color: "#2b2320" }}>⚡ Instant Demo Access (One-Click):</p>
        <p style={{ fontWeight: 700, fontSize: "0.85rem", margin: "0 0 0.5rem", color: "#2b2320" }}>Instant Demo Access (One-Click):</p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
          <button
            type="button"
            className="btn btn--outline"
            style={{ fontSize: "0.78rem", padding: "0.4rem" }}
            onClick={() => { setEmail("admin@hiarbusiness.com"); setPassword("AdminPass123!"); void performLogin("admin@hiarbusiness.com", "AdminPass123!"); }}
          >
            👑 Admin Portal
            Admin Portal
          </button>
          <button
            type="button"
            className="btn btn--outline"
            style={{ fontSize: "0.78rem", padding: "0.4rem" }}
            onClick={() => { setEmail("orders@hanoiluxehair.vn"); setPassword("SupplierPOC2025!"); void performLogin("orders@hanoiluxehair.vn", "SupplierPOC2025!"); }}
          >
            🏭 Supplier Portal
            Supplier Portal
          </button>
          <button
            type="button"
            className="btn btn--outline"
            style={{ fontSize: "0.78rem", padding: "0.4rem" }}
            onClick={() => { setEmail("warehouse@cherubim.vn"); setPassword("WarehousePass123!"); void performLogin("warehouse@cherubim.vn", "WarehousePass123!"); }}
          >
            📦 Warehouse Portal
            Warehouse Portal
          </button>
          <button
            type="button"
            className="btn btn--outline"
            style={{ fontSize: "0.78rem", padding: "0.4rem" }}
            onClick={() => { setEmail("customer@example.com"); setPassword("CustomerPass123!"); void performLogin("customer@example.com", "CustomerPass123!"); }}
          >
            🛍️ Customer Store
            Customer Store
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="auth-form">
        <label>Email<input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} /></label>
        <label>Password<input required type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={submitting}>{submitting ? "Signing in..." : "Log in"}</button>
      </form>
      <p>Don't have an account? <Link to="/register">Create one</Link></p>
      <p style={{ marginTop: "1rem" }}>Don't have an account? <Link to="/register">Create one</Link></p>
    </div>
  );
}

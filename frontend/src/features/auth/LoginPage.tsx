import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";
import { useAuth, AuthRequestError } from "../../lib/auth/AuthContext";
import { useMergeGuestCartOnLogin } from "../cart/hooks";
import { getGuestCartToken } from "../../lib/cart/guestCartToken";

export function LoginPage() {
  const { login } = useAuth();
  const mergeCart = useMergeGuestCartOnLogin();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      if (getGuestCartToken()) await mergeCart.mutateAsync().catch(() => undefined);
      const callbackUrl = searchParams.get("callbackUrl");
      navigate(callbackUrl ? decodeURIComponent(callbackUrl) : "/account");
    } catch (err) {
      setError(err instanceof AuthRequestError ? err.message : "Login failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page narrow">
      <h1>Log in</h1>
      <form onSubmit={handleSubmit} className="auth-form">
        <label>Email<input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} /></label>
        <label>Password<input required type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={submitting}>{submitting ? "Signing in..." : "Log in"}</button>
      </form>
      <p>Don't have an account? <Link to="/register">Create one</Link></p>
    </div>
  );
}

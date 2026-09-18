import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { useAuth, AuthRequestError } from "../../lib/auth/AuthContext";
import { useMergeGuestCartOnLogin } from "../cart/hooks";
import { getGuestCartToken } from "../../lib/cart/guestCartToken";

export function RegisterPage() {
  const { register } = useAuth();
  const mergeCart = useMergeGuestCartOnLogin();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(name, email, password);
      if (getGuestCartToken()) await mergeCart.mutateAsync().catch(() => undefined);
      navigate("/account");
    } catch (err) {
      setError(err instanceof AuthRequestError ? err.message : "Registration failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page narrow">
      <h1>Create an account</h1>
      <form onSubmit={handleSubmit} className="auth-form">
        <label>Name<input required value={name} onChange={(e) => setName(e.target.value)} /></label>
        <label>Email<input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} /></label>
        <label>Password<input required type="password" minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} /></label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={submitting}>{submitting ? "Creating account..." : "Create account"}</button>
      </form>
      <p>Already have an account? <Link to="/login">Log in</Link></p>
    </div>
  );
}

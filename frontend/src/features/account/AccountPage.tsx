import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { useAuth } from "../../lib/auth/AuthContext";
import { downloadAccountExport, useDeactivateAccount } from "./hooks";

export function AccountPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const deactivate = useDeactivateAccount();
  const [confirming, setConfirming] = useState(false);

  async function handleDeactivate() {
    await deactivate.mutateAsync();
    await logout();
    navigate("/");
  }

  return (
    <div className="page narrow">
      <h1>My Account</h1>
      <p>Signed in as {user?.email}</p>

      <div className="link-row">
        <Link to="/account/orders">View Order History →</Link>
        <Link to="/account/addresses">Manage Addresses →</Link>
      </div>

      <div className="callout">
        <h2>Your Data</h2>
        <p>You can download a copy of your account, order, and review data, or deactivate your account at any time.</p>
        <div className="link-row">
          <button type="button" onClick={() => void downloadAccountExport()}>Export My Data</button>
          {!confirming ? (
            <button type="button" className="danger" onClick={() => setConfirming(true)}>Deactivate My Account</button>
          ) : (
            <>
              <span>Are you sure?</span>
              <button type="button" className="danger" disabled={deactivate.isPending} onClick={() => void handleDeactivate()}>
                Yes, deactivate
              </button>
              <button type="button" onClick={() => setConfirming(false)}>Cancel</button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

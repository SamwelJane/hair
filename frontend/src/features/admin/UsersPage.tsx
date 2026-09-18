import { useState } from "react";
import { useAdminUsers, useCreateUser, useToggleUserActive } from "./hooks";

export function AdminUsersPage() {
  const { data: users, isLoading } = useAdminUsers();
  const createUser = useCreateUser();
  const toggleActive = useToggleUserActive();

  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [role, setRole] = useState<"ADMIN" | "STAFF" | "SUPPLIER" | "CUSTOMER" | "WAREHOUSE" | "KENYA_OPS">("STAFF");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createUser.mutateAsync({ email, name, role, password });
      setEmail(""); setName(""); setPassword("");
    } catch {
      setError("Could not create user - email may already be registered.");
    }
  }

  if (isLoading) return <div className="page">Loading...</div>;

  return (
    <div className="page">
      <h1>Users</h1>
      <table className="page-table">
        <thead><tr><th>Email</th><th>Name</th><th>Role</th><th>Status</th><th /></tr></thead>
        <tbody>
          {users?.map((u) => (
            <tr key={u.id}>
              <td>{u.email}</td><td>{u.name}</td><td>{u.role}</td>
              <td>{u.is_active ? "Active" : "Deactivated"}</td>
              <td><button type="button" className={u.is_active ? "danger" : ""} onClick={() => toggleActive.mutate(u.id)}>{u.is_active ? "Deactivate" : "Activate"}</button></td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Create User</h2>
      <form onSubmit={handleCreate} className="auth-form">
        <label>Email<input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} /></label>
        <label>Name<input required value={name} onChange={(e) => setName(e.target.value)} /></label>
        <label>Role
          <select value={role} onChange={(e) => setRole(e.target.value as typeof role)}>
            <option value="STAFF">Staff</option>
            <option value="ADMIN">Admin</option>
            <option value="SUPPLIER">Supplier</option>
            <option value="CUSTOMER">Customer</option>
            <option value="WAREHOUSE">Vietnam Warehouse</option>
            <option value="KENYA_OPS">Kenya Ops</option>
          </select>
        </label>
        <label>Password<input required type="password" minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} /></label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={createUser.isPending}>Create User</button>
      </form>
    </div>
  );
}

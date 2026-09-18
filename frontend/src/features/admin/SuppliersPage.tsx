import { useState } from "react";
import { Link } from "react-router";
import { useAdminSuppliers, useCreateSupplier } from "./hooks";

export function AdminSuppliersPage() {
  const { data: suppliers, isLoading } = useAdminSuppliers();
  const createSupplier = useCreateSupplier();
  const [name, setName] = useState("");
  const [country, setCountry] = useState("");
  const [email, setEmail] = useState("");
  const [whatsapp, setWhatsapp] = useState("");
  const [margin, setMargin] = useState("0");
  const [tempPassword, setTempPassword] = useState("");

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    await createSupplier.mutateAsync({
      name, country, email, whatsapp_number: whatsapp, default_margin_pct: margin,
      temporary_password: tempPassword || undefined,
    });
    setName(""); setCountry(""); setEmail(""); setWhatsapp(""); setMargin("0"); setTempPassword("");
  }

  if (isLoading) return <div className="page">Loading...</div>;

  return (
    <div className="page">
      <h1>Suppliers</h1>
      <table className="page-table">
        <thead><tr><th>Name</th><th>Country</th><th>Products</th><th>Login</th><th /></tr></thead>
        <tbody>
          {suppliers?.map((s) => (
            <tr key={s.id}>
              <td>{s.name}</td>
              <td>{s.country}</td>
              <td>{s.product_count}</td>
              <td>{s.user_id ? "Linked" : "Not linked"}</td>
              <td><Link to={`/admin/suppliers/${s.id}`}>View</Link></td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Add Supplier</h2>
      <form onSubmit={handleCreate} className="auth-form">
        <label>Name<input required value={name} onChange={(e) => setName(e.target.value)} /></label>
        <label>Country<input required maxLength={2} value={country} onChange={(e) => setCountry(e.target.value.toUpperCase())} /></label>
        <label>Email<input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} /></label>
        <label>WhatsApp number<input required value={whatsapp} onChange={(e) => setWhatsapp(e.target.value)} /></label>
        <label>Default margin %<input type="number" step="0.01" value={margin} onChange={(e) => setMargin(e.target.value)} /></label>
        <label>Temporary password (optional, creates a supplier login)<input value={tempPassword} onChange={(e) => setTempPassword(e.target.value)} /></label>
        <button type="submit" disabled={createSupplier.isPending}>Create Supplier</button>
      </form>
    </div>
  );
}

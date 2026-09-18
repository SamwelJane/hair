import { useState } from "react";
import { useAddresses, useCreateAddress, useDeleteAddress, useSetDefaultAddress } from "./hooks";

export function AddressesPage() {
  const { data: addresses, isLoading } = useAddresses();
  const createAddress = useCreateAddress();
  const deleteAddress = useDeleteAddress();
  const setDefault = useSetDefaultAddress();

  const [label, setLabel] = useState("");
  const [fullName, setFullName] = useState("");
  const [line1, setLine1] = useState("");
  const [line2, setLine2] = useState("");
  const [city, setCity] = useState("");
  const [countryCode, setCountryCode] = useState("");
  const [postalCode, setPostalCode] = useState("");
  const [phone, setPhone] = useState("");
  const [isDefault, setIsDefault] = useState(false);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    await createAddress.mutateAsync({
      label: label || undefined,
      full_name: fullName,
      line1,
      line2: line2 || undefined,
      city,
      country_code: countryCode.toUpperCase(),
      postal_code: postalCode || undefined,
      phone,
      is_default: isDefault,
    });
    setLabel(""); setFullName(""); setLine1(""); setLine2(""); setCity(""); setCountryCode(""); setPostalCode(""); setPhone(""); setIsDefault(false);
  }

  return (
    <div className="page narrow">
      <h1>Saved Addresses</h1>

      {isLoading && <p>Loading...</p>}
      <div className="address-list">
        {addresses?.map((a) => (
          <div key={a.id} className="address-card">
            <p><strong>{a.label || a.full_name}</strong> {a.is_default && <span className="badge">Default</span>}</p>
            <p className="muted">
              {a.full_name} · {a.line1}{a.line2 ? `, ${a.line2}` : ""}, {a.city}, {a.country_code} {a.postal_code ?? ""} · {a.phone}
            </p>
            <div className="link-row">
              {!a.is_default && (
                <button type="button" onClick={() => setDefault.mutate(a.id)}>Set as default</button>
              )}
              <button type="button" className="danger" onClick={() => deleteAddress.mutate(a.id)}>Delete</button>
            </div>
          </div>
        ))}
        {addresses?.length === 0 && <p>No saved addresses yet.</p>}
      </div>

      <h2>Add Address</h2>
      <form onSubmit={handleAdd} className="auth-form">
        <label>Label (e.g. Home, Office)<input value={label} onChange={(e) => setLabel(e.target.value)} /></label>
        <label>Full name<input required value={fullName} onChange={(e) => setFullName(e.target.value)} /></label>
        <label>Address line 1<input required value={line1} onChange={(e) => setLine1(e.target.value)} /></label>
        <label>Address line 2<input value={line2} onChange={(e) => setLine2(e.target.value)} /></label>
        <label>City<input required value={city} onChange={(e) => setCity(e.target.value)} /></label>
        <label>Country code<input required maxLength={2} value={countryCode} onChange={(e) => setCountryCode(e.target.value)} /></label>
        <label>Postal code<input value={postalCode} onChange={(e) => setPostalCode(e.target.value)} /></label>
        <label>Phone<input required value={phone} onChange={(e) => setPhone(e.target.value)} /></label>
        <label className="checkbox-label">
          <input type="checkbox" checked={isDefault} onChange={(e) => setIsDefault(e.target.checked)} />
          Set as default address
        </label>
        <button type="submit" disabled={createAddress.isPending}>Save Address</button>
      </form>
    </div>
  );
}

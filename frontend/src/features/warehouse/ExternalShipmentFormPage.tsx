import { useState } from "react";
import { Link } from "react-router";
import { getErrorDetail, useCreateExternalShipment } from "./hooks";

export function ExternalShipmentFormPage() {
  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [customerEmail, setCustomerEmail] = useState("");
  const [supplierReference, setSupplierReference] = useState("");
  const [notes, setNotes] = useState("");
  const [weightGrams, setWeightGrams] = useState("");
  const create = useCreateExternalShipment();

  return (
    <div className="page">
      <h1>New External Shipment</h1>
      <p className="muted">
        For customers who bought directly from a Vietnamese supplier outside the platform (WhatsApp, Facebook, etc.) - no
        platform account is required.
      </p>
      <form
        className="address-card"
        onSubmit={(e) => {
          e.preventDefault();
          create.mutate({
            customerName,
            customerPhone,
            customerEmail: customerEmail || undefined,
            supplierReference: supplierReference || undefined,
            notes: notes || undefined,
            weightGrams: weightGrams ? Number(weightGrams) : undefined,
          });
        }}
      >
        <input required placeholder="Customer name" value={customerName} onChange={(e) => setCustomerName(e.target.value)} />
        <input
          required
          placeholder="Customer phone"
          value={customerPhone}
          onChange={(e) => setCustomerPhone(e.target.value)}
          style={{ marginTop: "0.75rem" }}
        />
        <input
          type="email"
          placeholder="Customer email (optional)"
          value={customerEmail}
          onChange={(e) => setCustomerEmail(e.target.value)}
          style={{ marginTop: "0.75rem" }}
        />
        <input
          placeholder="Supplier reference (optional)"
          value={supplierReference}
          onChange={(e) => setSupplierReference(e.target.value)}
          style={{ marginTop: "0.75rem" }}
        />
        <input
          type="number"
          placeholder="Weight (grams, optional)"
          value={weightGrams}
          onChange={(e) => setWeightGrams(e.target.value)}
          style={{ marginTop: "0.75rem" }}
        />
        <input
          placeholder="Notes (optional)"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          style={{ marginTop: "0.75rem", width: "100%" }}
        />
        <button type="submit" disabled={create.isPending} style={{ marginTop: "0.75rem" }}>
          {create.isPending ? "Creating..." : "Create External Shipment"}
        </button>
      </form>

      {create.isError && <p className="error">{getErrorDetail(create.error) ?? "Could not create this shipment."}</p>}
      {create.isSuccess && create.data && (
        <div className="callout" style={{ marginTop: "1rem" }}>
          <p>Created shipment with tracking number <strong>{create.data.tracking_number}</strong>.</p>
          <p><Link to={`/warehouse/external-shipments/${create.data.id}`}>View shipment →</Link></p>
        </div>
      )}
    </div>
  );
}

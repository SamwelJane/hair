import { useRef, useState } from "react";
import { Link } from "react-router";
import { getErrorDetail, useReceivePackage } from "./hooks";

// Optimized for scanning: the tracking-number field autofocuses and a
// barcode scanner's trailing Enter submits the form directly, matching the
// "large scan fields, minimal typing" warehouse-workflow requirement.
export function ReceivePackagePage() {
  const [trackingNumber, setTrackingNumber] = useState("");
  const [weightGrams, setWeightGrams] = useState("");
  const [condition, setCondition] = useState<"" | "GOOD" | "DAMAGED">("");
  const [notes, setNotes] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const receive = useReceivePackage();

  function reset() {
    setTrackingNumber("");
    setWeightGrams("");
    setCondition("");
    setNotes("");
    inputRef.current?.focus();
  }

  return (
    <div className="page">
      <h1>Receive Package</h1>
      <form
        className="address-card"
        onSubmit={(e) => {
          e.preventDefault();
          receive.mutate(
            {
              trackingNumber: trackingNumber.trim(),
              weightGrams: weightGrams ? Number(weightGrams) : undefined,
              condition: condition || undefined,
              notes: notes || undefined,
            },
            { onSuccess: reset }
          );
        }}
      >
        <input
          ref={inputRef}
          autoFocus
          required
          placeholder="Scan or type tracking number"
          value={trackingNumber}
          onChange={(e) => setTrackingNumber(e.target.value)}
          style={{ fontSize: "1.25rem", padding: "0.75rem" }}
        />
        <div className="link-row" style={{ marginTop: "0.75rem" }}>
          <input
            type="number"
            placeholder="Weight (grams)"
            value={weightGrams}
            onChange={(e) => setWeightGrams(e.target.value)}
          />
          <select value={condition} onChange={(e) => setCondition(e.target.value as "" | "GOOD" | "DAMAGED")}>
            <option value="">Condition (optional)</option>
            <option value="GOOD">Good</option>
            <option value="DAMAGED">Damaged</option>
          </select>
        </div>
        <input
          placeholder="Notes (optional)"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          style={{ marginTop: "0.75rem", width: "100%" }}
        />
        <button type="submit" disabled={receive.isPending} style={{ marginTop: "0.75rem" }}>
          {receive.isPending ? "Receiving..." : "Receive Package"}
        </button>
      </form>

      {receive.isError && <p className="error">{getErrorDetail(receive.error) ?? "Could not receive this package."}</p>}
      {receive.isSuccess && receive.data && (
        <div className="callout" style={{ marginTop: "1rem" }}>
          <p>
            Received <strong>{receive.data.package_code}</strong> for tracking number{" "}
            <strong>{receive.data.tracking_number}</strong>.
          </p>
          <p><Link to={`/warehouse/packages/${receive.data.id}`}>View package →</Link></p>
        </div>
      )}
    </div>
  );
}

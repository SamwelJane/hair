import { useRef, useState } from "react";
import { Link } from "react-router";
import { getErrorDetail, useReceivePackage } from "./hooks";

/**
 * Receive Package — warehouse staff scan / enter a package on arrival.
 *
 * Weight logic (per spec):
 *  - Warehouse enters weight in GRAMS (physical scale reading)
 *  - The UI shows the auto-converted KG in real-time beside the input
 *  - Kg is computed server-side on save (weight_kg = grams / 1000)
 *  - No CBM / dimensions captured — platform charges $60/kg, not volumetric
 *
 * UX: tracking-number field autofocuses; a barcode scanner's trailing
 * Enter key submits the form directly (warehouse scan-first workflow).
 */
export function ReceivePackagePage() {
  const [trackingNumber, setTrackingNumber] = useState("");
  const [weightGrams, setWeightGrams] = useState("");
  const [condition, setCondition] = useState<"" | "GOOD" | "DAMAGED">("");
  const [notes, setNotes] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const receive = useReceivePackage();

  // Live kg conversion — purely cosmetic, server always recomputes
  const gramsNum = weightGrams ? Number(weightGrams) : null;
  const kgDisplay = gramsNum != null && gramsNum > 0
    ? (gramsNum / 1000).toFixed(3)
    : null;

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
        className="receive-form card"
        onSubmit={(e) => {
          e.preventDefault();
          receive.mutate(
            {
              trackingNumber: trackingNumber.trim(),
              weightGrams: gramsNum ?? undefined,
              condition: condition || undefined,
              notes: notes || undefined,
            },
            { onSuccess: reset }
          );
        }}
      >
        {/* Tracking Number — large for barcode scan */}
        <label className="form-label form-label--lg">
          Tracking Number
          <input
            ref={inputRef}
            autoFocus
            required
            className="receive-form__tracking"
            placeholder="Scan or type tracking number…"
            value={trackingNumber}
            onChange={(e) => setTrackingNumber(e.target.value)}
          />
        </label>

        {/* Weight — grams input with live kg display */}
        <label className="form-label">
          Weight
          <div className="weight-input-group">
            <input
              type="number"
              min={1}
              step={1}
              className="weight-input-group__grams"
              placeholder="Enter grams (e.g. 1500)"
              value={weightGrams}
              onChange={(e) => setWeightGrams(e.target.value)}
            />
            <span className="weight-input-group__unit">g</span>
            {kgDisplay && (
              <span className="weight-input-group__kg-badge">
                = <strong>{kgDisplay} kg</strong>
              </span>
            )}
          </div>
          <small className="form-hint">
            Enter the physical scale reading in grams. Kg is computed automatically.
            No CBM or dimensions needed — platform charges by weight only.
          </small>
        </label>

        {/* Condition */}
        <label className="form-label">
          Condition
          <select value={condition} onChange={(e) => setCondition(e.target.value as "" | "GOOD" | "DAMAGED")}>
            <option value="">Select condition (optional)</option>
            <option value="GOOD">Good — no visible damage</option>
            <option value="DAMAGED">Damaged — visible damage noted</option>
          </select>
        </label>

        {/* Notes */}
        <label className="form-label">
          Notes (optional)
          <input
            type="text"
            placeholder="e.g. Box slightly dented, contents appear intact"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </label>

        <button type="submit" className="btn btn--primary btn--lg" disabled={receive.isPending}>
          {receive.isPending ? "Receiving…" : "Receive Package"}
        </button>
      </form>

      {/* ── Error ─────────────────────────────────────────────────────────── */}
      {receive.isError && (
        <div className="callout callout--error" style={{ marginTop: "1rem" }}>
          <p>{getErrorDetail(receive.error) ?? "Could not receive this package. Check the tracking number and try again."}</p>
        </div>
      )}

      {/* ── Success ───────────────────────────────────────────────────────── */}
      {receive.isSuccess && receive.data && (
        <div className="callout callout--success" style={{ marginTop: "1rem" }}>
          <p>
            Received <strong>{receive.data.package_code}</strong> — tracking{" "}
            <strong>{receive.data.tracking_number}</strong>
          </p>
          {receive.data.weight_kg && (
            <p>
              Weight: <strong>{receive.data.weight_grams} g</strong>{" "}
              <span className="muted">({receive.data.weight_kg} kg)</span>
            </p>
          )}
          {receive.data.weight_kg == null && receive.data.weight_grams == null && (
            <p className="muted">Weight not recorded — use the weigh endpoint to add it later.</p>
          )}
          <p>
            <Link to={`/warehouse/packages/${receive.data.id}`}>View package →</Link>
          </p>
        </div>
      )}
    </div>
  );
}

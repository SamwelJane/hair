import { useState } from "react";
import { useParams } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { tokenStore } from "../../lib/auth/tokenStore";
import {
  getErrorDetail,
  usePackage,
  usePrintLabel,
  useQCPackage,
  useReprintLabel,
  useWeighPackage,
} from "./hooks";

export function PackageDetailPage() {
  const { packageId } = useParams<{ packageId: string }>();
  const { data: pkg, isLoading } = usePackage(packageId);
  const queryClient = useQueryClient();

  const qc = useQCPackage(packageId!);
  const [qcStatus, setQcStatus] = useState<"PENDING" | "PASSED" | "FAILED">("PASSED");
  const [qcCondition, setQcCondition] = useState<"" | "GOOD" | "DAMAGED">("");
  const [qcNotes, setQcNotes] = useState("");

  const weigh = useWeighPackage(packageId!);
  const [weightGrams, setWeightGrams] = useState("");
  const [lengthCm, setLengthCm] = useState("");
  const [widthCm, setWidthCm] = useState("");
  const [heightCm, setHeightCm] = useState("");

  const printLabel = usePrintLabel(packageId!);
  const reprintLabel = useReprintLabel(packageId!);

  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoError, setPhotoError] = useState<string | null>(null);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);

  if (isLoading) return <div className="page">Loading...</div>;
  if (!pkg) return <div className="page">Package not found.</div>;

  async function uploadPhoto(e: React.FormEvent) {
    e.preventDefault();
    if (!photoFile) return;
    setUploadingPhoto(true);
    setPhotoError(null);
    try {
      const formData = new FormData();
      formData.append("file", photoFile);
      const token = tokenStore.getState().accessToken;
      const resp = await fetch(`${tokenStore.apiBaseUrl}/warehouse/packages/${packageId}/photos`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });
      if (!resp.ok) {
        const body = await resp.json().catch(() => null);
        throw new Error(body?.detail ?? "Photo upload failed.");
      }
      setPhotoFile(null);
      await queryClient.invalidateQueries({ queryKey: ["warehouse-package", packageId] });
    } catch (err) {
      setPhotoError(err instanceof Error ? err.message : "Photo upload failed.");
    } finally {
      setUploadingPhoto(false);
    }
  }

  return (
    <div className="page">
      <h1>Package {pkg.package_code}</h1>
      <p className="badge">{pkg.status.replaceAll("_", " ")}</p>
      <p>Tracking number: <strong>{pkg.tracking_number}</strong></p>
      <p className="muted">
        QC: {pkg.qc_status} {pkg.condition ? `· Condition: ${pkg.condition}` : ""} {pkg.weight_grams != null ? `· ${pkg.weight_grams} g` : ""}
        {pkg.weight_kg != null ? ` · ${pkg.weight_kg} kg` : ""}
      </p>
      {pkg.notes && <p className="muted">Notes: {pkg.notes}</p>}

      <h2>Quality Control</h2>
      <form
        className="link-row"
        onSubmit={(e) => {
          e.preventDefault();
          qc.mutate({ qcStatus, condition: qcCondition || undefined, notes: qcNotes || undefined });
        }}
      >
        <select value={qcStatus} onChange={(e) => setQcStatus(e.target.value as "PENDING" | "PASSED" | "FAILED")}>
          <option value="PASSED">Passed</option>
          <option value="FAILED">Failed</option>
          <option value="PENDING">Pending</option>
        </select>
        <select value={qcCondition} onChange={(e) => setQcCondition(e.target.value as "" | "GOOD" | "DAMAGED")}>
          <option value="">Condition unchanged</option>
          <option value="GOOD">Good</option>
          <option value="DAMAGED">Damaged</option>
        </select>
        <input placeholder="QC notes" value={qcNotes} onChange={(e) => setQcNotes(e.target.value)} />
        <button type="submit" disabled={qc.isPending}>Record QC</button>
      </form>
      {qc.isError && <p className="error">{getErrorDetail(qc.error) ?? "Could not record QC."}</p>}

      <h2>Weighing</h2>
      <form
        className="link-row"
        onSubmit={(e) => {
          e.preventDefault();
          weigh.mutate({
            weightGrams: Number(weightGrams),
            lengthCm: lengthCm || undefined,
            widthCm: widthCm || undefined,
            heightCm: heightCm || undefined,
          });
        }}
      >
        <input type="number" required placeholder="Weight (g)" value={weightGrams} onChange={(e) => setWeightGrams(e.target.value)} />
        <input placeholder="Length (cm)" value={lengthCm} onChange={(e) => setLengthCm(e.target.value)} />
        <input placeholder="Width (cm)" value={widthCm} onChange={(e) => setWidthCm(e.target.value)} />
        <input placeholder="Height (cm)" value={heightCm} onChange={(e) => setHeightCm(e.target.value)} />
        <button type="submit" disabled={weigh.isPending}>Save</button>
      </form>
      {weigh.isError && <p className="error">{getErrorDetail(weigh.error) ?? "Could not save weight."}</p>}

      <h2>Photos</h2>
      <div className="link-row">
        {pkg.photo_urls?.map((url) => (
          <img key={url} src={url} alt="Package" style={{ width: 96, height: 96, objectFit: "cover" }} />
        ))}
        {(!pkg.photo_urls || pkg.photo_urls.length === 0) && <p className="muted">No photos yet.</p>}
      </div>
      <form className="link-row" onSubmit={(e) => void uploadPhoto(e)}>
        <input type="file" accept="image/*" onChange={(e) => setPhotoFile(e.target.files?.[0] ?? null)} />
        <button type="submit" disabled={!photoFile || uploadingPhoto}>{uploadingPhoto ? "Uploading..." : "Upload Photo"}</button>
      </form>
      {photoError && <p className="error">{photoError}</p>}

      <h2>Label</h2>
      {!pkg.label_printed_at ? (
        <button type="button" onClick={() => printLabel.mutate()} disabled={printLabel.isPending}>
          {printLabel.isPending ? "Printing..." : "Print Label"}
        </button>
      ) : (
        <button type="button" onClick={() => reprintLabel.mutate()} disabled={reprintLabel.isPending}>
          {reprintLabel.isPending ? "Reprinting..." : `Reprint Label (${pkg.label_reprint_count} reprint${pkg.label_reprint_count === 1 ? "" : "s"} so far)`}
        </button>
      )}
      {printLabel.isError && <p className="error">{getErrorDetail(printLabel.error) ?? "Could not print label."}</p>}
      {reprintLabel.isError && <p className="error">{getErrorDetail(reprintLabel.error) ?? "Could not reprint label."}</p>}
      {(printLabel.data ?? reprintLabel.data) && <LabelPreview label={(reprintLabel.data ?? printLabel.data)!} />}
    </div>
  );
}

function LabelPreview({ label }: { label: { package_code: string; tracking_number: string; masked_customer_name: string; destination: string; weight_grams: number | null; qr_url: string } }) {
  return (
    <div className="callout" style={{ marginTop: "1rem", maxWidth: 320 }}>
      <p><strong>Cherubim Express</strong> · Vietnam → Kenya</p>
      <p>Tracking: <strong>{label.tracking_number}</strong></p>
      <p>Package: {label.package_code}</p>
      <p>To: {label.masked_customer_name}, {label.destination}</p>
      {label.weight_grams != null && <p>Weight: {label.weight_grams} g</p>}
      <p className="muted">Scan to track: {label.qr_url}</p>
    </div>
  );
}

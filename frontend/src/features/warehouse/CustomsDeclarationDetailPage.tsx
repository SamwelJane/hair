import { useState } from "react";
import { useParams } from "react-router";
import { getErrorDetail, useClearCustoms, useCustomsDeclaration, useDeclareCustoms, useRaiseCustomsQuery } from "./hooks";

export function CustomsDeclarationDetailPage() {
  const { declarationId } = useParams<{ declarationId: string }>();
  const { data: declaration, isLoading } = useCustomsDeclaration(declarationId);
  const declare = useDeclareCustoms(declarationId!);
  const raiseQuery = useRaiseCustomsQuery(declarationId!);
  const clear = useClearCustoms(declarationId!);

  const [hsCode, setHsCode] = useState("");
  const [declaredValue, setDeclaredValue] = useState("");
  const [duty, setDuty] = useState("");
  const [vat, setVat] = useState("");
  const [queryNote, setQueryNote] = useState("");

  if (isLoading) return <div className="page">Loading...</div>;
  if (!declaration) return <div className="page">Customs declaration not found.</div>;

  return (
    <div className="page">
      <h1>Customs Declaration</h1>
      <p className="badge">{declaration.status.replaceAll("_", " ")}</p>
      {declaration.consolidation_code && <p className="muted">Consolidation: {declaration.consolidation_code}</p>}
      {declaration.hs_code && (
        <p className="muted">
          HS {declaration.hs_code} · Declared ${declaration.declared_value_usd} · Duty ${declaration.duty_usd} · VAT ${declaration.vat_usd}
        </p>
      )}
      {declaration.notes && <p className="muted">Notes: {declaration.notes}</p>}

      {declaration.status === "PREPARING" && (
        <>
          <h2>Declare</h2>
          <form
            className="link-row"
            onSubmit={(e) => {
              e.preventDefault();
              declare.mutate({ hsCode, declaredValueUsd: declaredValue, dutyUsd: duty || undefined, vatUsd: vat || undefined });
            }}
          >
            <input required placeholder="HS code" value={hsCode} onChange={(e) => setHsCode(e.target.value)} />
            <input required placeholder="Declared value (USD)" value={declaredValue} onChange={(e) => setDeclaredValue(e.target.value)} />
            <input placeholder="Duty (USD)" value={duty} onChange={(e) => setDuty(e.target.value)} />
            <input placeholder="VAT (USD)" value={vat} onChange={(e) => setVat(e.target.value)} />
            <button type="submit" disabled={declare.isPending}>{declare.isPending ? "Saving..." : "Submit Declaration"}</button>
          </form>
          {declare.isError && <p className="error">{getErrorDetail(declare.error) ?? "Could not declare."}</p>}
        </>
      )}

      {declaration.status === "DECLARED" && (
        <>
          <h2>Actions</h2>
          <form
            className="link-row"
            onSubmit={(e) => { e.preventDefault(); raiseQuery.mutate(queryNote, { onSuccess: () => setQueryNote("") }); }}
          >
            <input required placeholder="Query note" value={queryNote} onChange={(e) => setQueryNote(e.target.value)} />
            <button type="submit" disabled={raiseQuery.isPending}>{raiseQuery.isPending ? "Saving..." : "Raise Query"}</button>
          </form>
          {raiseQuery.isError && <p className="error">{getErrorDetail(raiseQuery.error) ?? "Could not raise query."}</p>}

          <button type="button" style={{ marginTop: "0.75rem" }} disabled={clear.isPending} onClick={() => clear.mutate()}>
            {clear.isPending ? "Clearing..." : "Clear Customs"}
          </button>
        </>
      )}

      {declaration.status === "QUERY_RAISED" && (
        <>
          <h2>Query Outstanding</h2>
          <button type="button" disabled={clear.isPending} onClick={() => clear.mutate()}>
            {clear.isPending ? "Clearing..." : "Clear Customs"}
          </button>
        </>
      )}
      {clear.isError && <p className="error">{getErrorDetail(clear.error) ?? "Could not clear customs."}</p>}
      {declaration.status === "CLEARED" && <p className="muted">Cleared - packages are ready for delivery.</p>}
    </div>
  );
}

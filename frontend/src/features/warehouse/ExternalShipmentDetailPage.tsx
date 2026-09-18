import { useParams } from "react-router";
import { useExternalShipment } from "./hooks";

export function ExternalShipmentDetailPage() {
  const { shipmentId } = useParams<{ shipmentId: string }>();
  const { data: shipment, isLoading } = useExternalShipment(shipmentId);

  if (isLoading) return <div className="page">Loading...</div>;
  if (!shipment) return <div className="page">External shipment not found.</div>;

  return (
    <div className="page">
      <h1>External Shipment</h1>
      <p className="badge">{shipment.status}</p>
      <p>Tracking number: <strong>{shipment.tracking_number}</strong></p>
      <p>{shipment.customer_name} · {shipment.customer_phone}{shipment.customer_email ? ` · ${shipment.customer_email}` : ""}</p>
      {shipment.supplier_reference && <p className="muted">Supplier reference: {shipment.supplier_reference}</p>}
      {shipment.notes && <p className="muted">Notes: {shipment.notes}</p>}
      <p className="muted">Created {new Date(shipment.created_at).toLocaleString()}</p>
    </div>
  );
}

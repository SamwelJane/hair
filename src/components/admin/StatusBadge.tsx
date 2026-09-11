const STATUS_STYLES: Record<string, string> = {
  PENDING_PAYMENT: "bg-admin-warning-soft text-admin-warning",
  PAID: "bg-admin-good-soft text-admin-good",
  SENT_TO_SUPPLIER: "bg-admin-accent/15 text-admin-accent",
  SUPPLIER_PROCESSING: "bg-admin-accent/15 text-admin-accent",
  READY_FOR_PICKUP: "bg-admin-accent/15 text-admin-accent",
  RECEIVED_AT_OFFICE: "bg-admin-accent/15 text-admin-accent",
  SHIPPED_INTERNATIONALLY: "bg-admin-good-soft text-admin-good",
  IN_TRANSIT: "bg-admin-good-soft text-admin-good",
  DELIVERED: "bg-admin-good-soft text-admin-good",
  CANCELLED: "bg-admin-critical-soft text-admin-critical",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${STATUS_STYLES[status] ?? "bg-admin-surface-2 text-admin-muted"}`}>
      {status.replaceAll("_", " ")}
    </span>
  );
}

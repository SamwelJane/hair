// Client-side display groupings only — mirrors src/lib/orders/state-machine.ts's
// CLIENT_STEPPER_GROUPS from the old app. The FastAPI backend remains the
// source of truth for valid transitions; this is UI presentation only.
export const ORDER_STATUS_VALUES = [
  "PENDING_PAYMENT",
  "PAID",
  "SENT_TO_SUPPLIER",
  "SUPPLIER_PROCESSING",
  "READY_FOR_PICKUP",
  "RECEIVED_AT_OFFICE",
  "SHIPPED_INTERNATIONALLY",
  "IN_TRANSIT",
  "DELIVERED",
  "CANCELLED",
] as const;

export type OrderStatus = (typeof ORDER_STATUS_VALUES)[number];

export const CLIENT_STEPPER_GROUPS: { label: string; statuses: OrderStatus[] }[] = [
  { label: "Order received", statuses: ["PENDING_PAYMENT", "PAID"] },
  { label: "In production", statuses: ["SENT_TO_SUPPLIER", "SUPPLIER_PROCESSING"] },
  { label: "Ready to ship", statuses: ["READY_FOR_PICKUP", "RECEIVED_AT_OFFICE"] },
  { label: "On the way", statuses: ["SHIPPED_INTERNATIONALLY", "IN_TRANSIT"] },
  { label: "Delivered", statuses: ["DELIVERED"] },
];

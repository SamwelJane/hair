import type { OrderStatus } from "@/generated/prisma/client";

// Canonical backend status flow. The client-facing stepper and the internal
// supplier timeline (see mockups) are presentation-layer groupings of this
// single enum, not separate status fields.
const TRANSITIONS: Record<OrderStatus, OrderStatus[]> = {
  PENDING_PAYMENT: ["PAID", "CANCELLED"],
  PAID: ["SENT_TO_SUPPLIER", "CANCELLED"],
  SENT_TO_SUPPLIER: ["SUPPLIER_PROCESSING", "CANCELLED"],
  SUPPLIER_PROCESSING: ["READY_FOR_PICKUP", "CANCELLED"],
  READY_FOR_PICKUP: ["RECEIVED_AT_OFFICE", "CANCELLED"],
  RECEIVED_AT_OFFICE: ["SHIPPED_INTERNATIONALLY", "CANCELLED"],
  SHIPPED_INTERNATIONALLY: ["IN_TRANSIT"],
  IN_TRANSIT: ["DELIVERED"],
  DELIVERED: [],
  CANCELLED: [],
};

export function canTransition(from: OrderStatus, to: OrderStatus): boolean {
  return TRANSITIONS[from]?.includes(to) ?? false;
}

export function assertValidTransition(from: OrderStatus, to: OrderStatus): void {
  if (!canTransition(from, to)) {
    throw new Error(`Invalid order status transition: ${from} -> ${to}`);
  }
}

// Groupings used to render the client-facing stepper from the mockup
// (Order Received -> Payment Confirmed -> Processing -> In Warehouse -> Shipping -> Out for Delivery).
export const CLIENT_STEPPER_GROUPS: { label: string; statuses: OrderStatus[] }[] = [
  { label: "Order Received", statuses: ["PENDING_PAYMENT"] },
  { label: "Payment Confirmed", statuses: ["PAID"] },
  { label: "Processing", statuses: ["SENT_TO_SUPPLIER", "SUPPLIER_PROCESSING", "READY_FOR_PICKUP"] },
  { label: "In Warehouse", statuses: ["RECEIVED_AT_OFFICE"] },
  { label: "Shipping", statuses: ["SHIPPED_INTERNATIONALLY"] },
  { label: "Out for Delivery", statuses: ["IN_TRANSIT", "DELIVERED"] },
];

// Groupings used to render the internal supplier timeline from the admin mockup
// (Order Created -> Sent to Supplier -> In Production -> Pending Quality Check -> Ready for Dispatch).
export const SUPPLIER_TIMELINE_GROUPS: { label: string; statuses: OrderStatus[] }[] = [
  { label: "Order Created", statuses: ["PENDING_PAYMENT", "PAID"] },
  { label: "Sent to Supplier", statuses: ["SENT_TO_SUPPLIER"] },
  { label: "In Production", statuses: ["SUPPLIER_PROCESSING"] },
  { label: "Pending Quality Check", statuses: ["READY_FOR_PICKUP"] },
  { label: "Ready for Dispatch", statuses: ["RECEIVED_AT_OFFICE"] },
];

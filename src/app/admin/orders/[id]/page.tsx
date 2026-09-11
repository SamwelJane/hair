import { notFound } from "next/navigation";
import { db } from "@/lib/db";
import { requireAdminSession } from "@/lib/auth/require-admin";
import { transitionOrderStatus } from "@/lib/orders/transition";
import { canTransition } from "@/lib/orders/state-machine";
import { generateTrackingNumber } from "@/lib/shipping/tracking-number";
import { logAudit } from "@/lib/security/audit";
import { StatusBadge } from "@/components/admin/StatusBadge";
import type { OrderStatus } from "@/generated/prisma/client";
import { revalidatePath } from "next/cache";

const ALL_STATUSES: OrderStatus[] = [
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
];

export default async function AdminOrderDetailPage({ params }: { params: Promise<{ id: string }> }) {
  await requireAdminSession();
  const { id } = await params;

  const order = await db.order.findUnique({
    where: { id },
    include: {
      user: true,
      items: { include: { product: true, variant: true } },
      statusHistory: { orderBy: { createdAt: "asc" }, include: { changedBy: true } },
      supplierOrders: { include: { supplier: true } },
      payments: true,
      shipment: { include: { milestones: { orderBy: { occurredAt: "asc" } } } },
    },
  });

  if (!order) notFound();

  async function updateStatus(formData: FormData) {
    "use server";
    const adminSession = await requireAdminSession();
    const toStatus = formData.get("toStatus") as OrderStatus;
    const note = formData.get("note") as string;
    await transitionOrderStatus(id, toStatus, adminSession.user.id, note || undefined);
    revalidatePath(`/admin/orders/${id}`);
  }

  async function createShipment(formData: FormData) {
    "use server";
    const adminSession = await requireAdminSession();
    const originOfficeLocation = formData.get("originOfficeLocation") as string;

    const trackingNumber = await generateTrackingNumber();
    const shipment = await db.shipment.create({
      data: { orderId: id, trackingNumber, originOfficeLocation, status: "preparing" },
    });

    await logAudit({
      userId: adminSession.user.id,
      action: "CREATE_SHIPMENT",
      entityType: "Shipment",
      entityId: shipment.id,
      metadata: { orderId: id, trackingNumber },
    });

    revalidatePath(`/admin/orders/${id}`);
  }

  async function addMilestone(formData: FormData) {
    "use server";
    const adminSession = await requireAdminSession();
    const shipmentId = formData.get("shipmentId") as string;
    const label = formData.get("label") as string;
    const location = formData.get("location") as string;

    await logAudit({
      userId: adminSession.user.id,
      action: "ADD_SHIPMENT_MILESTONE",
      entityType: "Shipment",
      entityId: shipmentId,
      metadata: { label, location },
    });

    await db.shipmentMilestone.create({
      data: { shipmentId, label, location: location || undefined, createdById: adminSession.user.id },
    });

    revalidatePath(`/admin/orders/${id}`);
  }

  const nextStatuses = ALL_STATUSES.filter((s) => canTransition(order.status, s));

  return (
    <div className="mx-auto max-w-4xl p-6 text-admin-ink">
      <h1 className="text-2xl font-semibold">Order {order.orderNumber}</h1>
      <p className="text-sm text-admin-muted">
        Customer: {order.user.name} ({order.user.email})
      </p>
      <div className="mt-2">
        <StatusBadge status={order.status} />
      </div>
      <p className="mt-2 text-sm">
        Total: ${order.totalAmountUsd.toString()} (KES {order.totalAmountKes?.toString() ?? "-"})
      </p>

      <h2 className="mt-6 text-lg font-semibold">Items</h2>
      <ul className="mt-2 flex flex-col gap-1 text-sm">
        {order.items.map((item) => (
          <li key={item.id}>
            {item.quantity}x {item.product.name} {item.variant ? `(${item.variant.length ?? ""})` : ""} - $
            {item.lineTotalUsd.toString()}
          </li>
        ))}
      </ul>

      {order.supplierOrders.length > 0 && (
        <>
          <h2 className="mt-6 text-lg font-semibold">Supplier Orders</h2>
          <ul className="mt-2 flex flex-col gap-1 text-sm">
            {order.supplierOrders.map((so) => (
              <li key={so.id}>
                {so.supplier.name}: {so.status}
              </li>
            ))}
          </ul>
        </>
      )}

      <h2 className="mt-6 text-lg font-semibold">Status Timeline</h2>
      <ul className="mt-2 flex flex-col gap-2 text-sm">
        {order.statusHistory.map((h) => (
          <li key={h.id} className="border-b border-admin-border/60 pb-2">
            <span className="font-medium">{h.toStatus}</span> -{" "}
            {h.createdAt.toLocaleString()} {h.changedBy ? `by ${h.changedBy.name}` : ""}
            {h.note && <p className="text-admin-muted">{h.note}</p>}
          </li>
        ))}
      </ul>

      <h2 className="mt-6 text-lg font-semibold">Shipment</h2>
      {!order.shipment ? (
        order.status === "RECEIVED_AT_OFFICE" ? (
          <form action={createShipment} className="mt-2 flex flex-col gap-3 rounded border border-admin-border bg-admin-surface p-4 text-sm">
            <input
              name="originOfficeLocation"
              placeholder="Office location (e.g. Nairobi HQ)"
              className="rounded border border-admin-border bg-admin-bg px-3 py-2 text-admin-ink"
            />
            <button type="submit" className="rounded bg-admin-accent px-4 py-2 text-white hover:opacity-90">
              Create Shipment
            </button>
          </form>
        ) : (
          <p className="mt-2 text-sm text-admin-muted">
            Shipment can be created once the order reaches &quot;Received at Office&quot;.
          </p>
        )
      ) : (
        <div className="mt-2 rounded border border-admin-border bg-admin-surface p-4 text-sm">
          <p>
            Tracking number: <strong>{order.shipment.trackingNumber}</strong> ·{" "}
            <a href={`/track/${order.shipment.trackingNumber}`} className="text-admin-accent underline">
              Public tracking page
            </a>
          </p>
          <ul className="mt-3 flex flex-col gap-1">
            {order.shipment.milestones.map((m) => (
              <li key={m.id}>
                {m.occurredAt.toLocaleString()} - {m.label} {m.location ? `(${m.location})` : ""}
              </li>
            ))}
          </ul>
          <form action={addMilestone} className="mt-4 flex flex-col gap-2">
            <input type="hidden" name="shipmentId" value={order.shipment.id} />
            <input name="label" placeholder="Milestone (e.g. Shipped, In Transit)" required className="rounded border border-admin-border bg-admin-bg px-3 py-2 text-admin-ink" />
            <input name="location" placeholder="Location (optional)" className="rounded border border-admin-border bg-admin-bg px-3 py-2 text-admin-ink" />
            <button type="submit" className="rounded bg-admin-accent px-4 py-2 text-white hover:opacity-90">
              Add Milestone
            </button>
          </form>
        </div>
      )}

      {nextStatuses.length > 0 && (
        <form action={updateStatus} className="mt-6 flex flex-col gap-3 rounded border border-admin-border bg-admin-surface p-4 text-sm">
          <h2 className="text-lg font-semibold">Update Status</h2>
          <select name="toStatus" required className="rounded border border-admin-border bg-admin-bg px-3 py-2 text-admin-ink">
            {nextStatuses.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <input name="note" placeholder="Note (optional)" className="rounded border border-admin-border bg-admin-bg px-3 py-2 text-admin-ink" />
          <button type="submit" className="rounded bg-admin-accent px-4 py-2 text-white hover:opacity-90">
            Update Status
          </button>
        </form>
      )}
    </div>
  );
}

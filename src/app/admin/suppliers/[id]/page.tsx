import { notFound } from "next/navigation";
import Link from "next/link";
import { db } from "@/lib/db";
import { requireAdminSession } from "@/lib/auth/require-admin";
import { getSupplierPerformance } from "@/lib/suppliers/performance";
import { logAudit } from "@/lib/security/audit";
import type { SupplierOrderStatus } from "@/generated/prisma/client";
import { revalidatePath } from "next/cache";

const NEXT_STATUS: Record<SupplierOrderStatus, SupplierOrderStatus | null> = {
  SENT: "ACKNOWLEDGED",
  ACKNOWLEDGED: "IN_PRODUCTION",
  IN_PRODUCTION: "READY",
  READY: null,
};

export default async function AdminSupplierDetailPage({ params }: { params: Promise<{ id: string }> }) {
  await requireAdminSession();
  const { id } = await params;

  const supplier = await db.supplier.findUnique({ where: { id } });
  if (!supplier) notFound();

  async function advanceSupplierOrder(formData: FormData) {
    "use server";
    const session = await requireAdminSession();
    const supplierOrderId = formData.get("supplierOrderId") as string;

    const so = await db.supplierOrder.findUniqueOrThrow({ where: { id: supplierOrderId } });
    const next = NEXT_STATUS[so.status];
    if (!next) return;

    await db.supplierOrder.update({
      where: { id: supplierOrderId },
      data: { status: next, confirmedAt: next === "READY" ? new Date() : so.confirmedAt },
    });

    await logAudit({
      userId: session.user.id,
      action: "ADVANCE_SUPPLIER_ORDER",
      entityType: "SupplierOrder",
      entityId: supplierOrderId,
      metadata: { from: so.status, to: next },
    });

    revalidatePath(`/admin/suppliers/${id}`);
  }

  const [performance, supplierOrders] = await Promise.all([
    getSupplierPerformance(id),
    db.supplierOrder.findMany({
      where: { supplierId: id },
      include: { order: { include: { user: true } } },
      orderBy: { sentAt: "desc" },
    }),
  ]);

  const pending = supplierOrders.filter((so) => so.status !== "READY");

  return (
    <div className="mx-auto max-w-4xl p-6 text-admin-ink">
      <Link href="/admin/suppliers" className="text-sm text-admin-accent underline">
        ← All Suppliers
      </Link>
      <h1 className="mt-2 text-2xl font-semibold">{supplier.name}</h1>
      <p className="text-sm text-admin-muted">
        {supplier.country} · {supplier.email} · {supplier.whatsappNumber}
      </p>

      <h2 className="mt-6 text-lg font-semibold">Performance</h2>
      <dl className="mt-2 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
        <div>
          <dt className="text-admin-muted">Total Orders</dt>
          <dd className="text-lg font-semibold">{performance.totalOrders}</dd>
        </div>
        <div>
          <dt className="text-admin-muted">Completed</dt>
          <dd className="text-lg font-semibold">{performance.completedOrders}</dd>
        </div>
        <div>
          <dt className="text-admin-muted">Avg Processing Time</dt>
          <dd className="text-lg font-semibold">
            {performance.avgProcessingDays !== null ? `${performance.avgProcessingDays}d` : "-"}
          </dd>
        </div>
        <div>
          <dt className="text-admin-muted">On-Time Rate</dt>
          <dd className="text-lg font-semibold">
            {performance.onTimeRatePct !== null ? `${performance.onTimeRatePct}%` : "-"}
          </dd>
        </div>
      </dl>

      <h2 className="mt-8 text-lg font-semibold">Pending Orders</h2>
      <table className="mt-2 w-full text-left text-sm">
        <thead>
          <tr className="border-b border-admin-border text-admin-muted">
            <th className="py-2">Order</th>
            <th>Customer</th>
            <th>Status</th>
            <th>Sent</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {pending.map((so) => (
            <tr key={so.id} className="border-b border-admin-border/60">
              <td className="py-2">
                <Link href={`/admin/orders/${so.order.id}`} className="text-admin-accent underline">
                  {so.order.orderNumber}
                </Link>
              </td>
              <td>{so.order.user.email}</td>
              <td>{so.status}</td>
              <td>{so.sentAt.toLocaleDateString()}</td>
              <td>
                <form action={advanceSupplierOrder}>
                  <input type="hidden" name="supplierOrderId" value={so.id} />
                  <button type="submit" className="rounded bg-admin-accent px-3 py-1 text-xs text-white hover:opacity-90">
                    Mark {NEXT_STATUS[so.status]}
                  </button>
                </form>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {pending.length === 0 && <p className="mt-2 text-sm text-admin-muted">No pending orders.</p>}
    </div>
  );
}

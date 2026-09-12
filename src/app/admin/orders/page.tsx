import Link from "next/link";
import { db } from "@/lib/db";
import { requireAdminSession } from "@/lib/auth/require-admin";
import { StatusBadge } from "@/components/admin/StatusBadge";

export default async function AdminOrdersPage() {
  await requireAdminSession();
  const orders = await db.order.findMany({
    include: { user: true, supplierOrders: { include: { supplier: true } } },
    orderBy: { createdAt: "desc" },
  });

  return (
    <div className="mx-auto max-w-5xl p-6 text-admin-ink">
      <h1 className="text-2xl font-semibold">Orders</h1>

      <table className="mt-6 w-full text-left text-sm">
        <thead>
          <tr className="border-b border-admin-border text-admin-muted">
            <th className="py-2">Order</th>
            <th>Customer</th>
            <th>Supplier(s)</th>
            <th>Status</th>
            <th>Total (USD)</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {orders.map((o) => (
            <tr key={o.id} className="border-b border-admin-border/60">
              <td className="py-2">{o.orderNumber}</td>
              <td>{o.user.email}</td>
              <td>{o.supplierOrders.map((so) => so.supplier.name).join(", ") || "-"}</td>
              <td><StatusBadge status={o.status} /></td>
              <td>${o.totalAmountUsd.toString()}</td>
              <td>
                <Link href={`/admin/orders/${o.id}`} className="text-admin-accent underline">
                  View
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

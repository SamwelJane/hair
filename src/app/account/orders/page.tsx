import Link from "next/link";
import { auth } from "@/auth";
import { db } from "@/lib/db";
import { SiteHeader } from "@/components/storefront/SiteHeader";
import { SiteFooter } from "@/components/storefront/SiteFooter";

export default async function AccountOrdersPage() {
  const session = await auth();
  const orders = await db.order.findMany({
    where: { userId: session!.user.id },
    orderBy: { createdAt: "desc" },
  });

  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-3xl flex-1 px-6 py-10">
        <h1 className="text-2xl font-semibold text-brand-ink">Order History</h1>
        <ul className="mt-6 flex flex-col gap-3">
          {orders.map((o) => (
            <li key={o.id} className="flex items-center justify-between rounded border border-brand-border bg-brand-surface p-4 text-sm">
              <div>
                <p className="font-medium text-brand-ink">{o.orderNumber}</p>
                <p className="text-brand-muted">{o.status}</p>
              </div>
              <div className="flex items-center gap-4">
                <p className="text-brand-ink">${o.totalAmountUsd.toString()}</p>
                <Link href={`/account/orders/${o.orderNumber}`} className="text-brand-accent underline">
                  View
                </Link>
              </div>
            </li>
          ))}
          {orders.length === 0 && <p className="text-sm text-brand-muted">No orders yet.</p>}
        </ul>
      </main>
      <SiteFooter />
    </>
  );
}

import { notFound } from "next/navigation";
import { auth } from "@/auth";
import { db } from "@/lib/db";
import { SiteHeader } from "@/components/storefront/SiteHeader";
import { SiteFooter } from "@/components/storefront/SiteFooter";
import { OrderStepper } from "@/components/storefront/OrderStepper";

export default async function AccountOrderDetailPage({
  params,
}: {
  params: Promise<{ orderNumber: string }>;
}) {
  const { orderNumber } = await params;
  const session = await auth();

  const order = await db.order.findUnique({
    where: { orderNumber },
    include: { items: { include: { product: true, variant: true } }, shipment: true },
  });

  if (!order || order.userId !== session?.user?.id) notFound();

  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-2xl flex-1 px-6 py-10">
        <h1 className="text-2xl font-semibold text-brand-ink">Order {order.orderNumber}</h1>

        <div className="mt-4">
          {order.status === "CANCELLED" ? (
            <span className="rounded-full bg-brand-danger/10 px-3 py-1 text-xs text-brand-danger">Cancelled</span>
          ) : (
            <OrderStepper status={order.status} />
          )}
        </div>

        <ul className="mt-6 flex flex-col gap-2 text-sm text-brand-ink">
          {order.items.map((item) => (
            <li key={item.id} className="flex justify-between">
              <span>
                {item.quantity}x {item.product.name} {item.variant?.length ? `(${item.variant.length})` : ""}
              </span>
              <span>${item.lineTotalUsd.toString()}</span>
            </li>
          ))}
        </ul>

        <p className="mt-4 text-lg font-semibold text-brand-ink">Total: ${order.totalAmountUsd.toString()}</p>

        {order.shipment && (
          <p className="mt-4 text-sm text-brand-ink">
            Tracking number:{" "}
            <a href={`/track/${order.shipment.trackingNumber}`} className="text-brand-accent underline">
              {order.shipment.trackingNumber}
            </a>
          </p>
        )}
      </main>
      <SiteFooter />
    </>
  );
}

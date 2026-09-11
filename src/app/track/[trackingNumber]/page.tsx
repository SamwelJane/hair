import { notFound } from "next/navigation";
import { SiteHeader } from "@/components/storefront/SiteHeader";
import { SiteFooter } from "@/components/storefront/SiteFooter";
import { db } from "@/lib/db";
import { getDeliveryEstimate } from "@/lib/shipping/estimator";

export default async function TrackingPage({
  params,
}: {
  params: Promise<{ trackingNumber: string }>;
}) {
  const { trackingNumber } = await params;

  const shipment = await db.shipment.findUnique({
    where: { trackingNumber },
    include: { milestones: { orderBy: { occurredAt: "asc" } }, order: true },
  });

  if (!shipment) notFound();

  const estimate = await getDeliveryEstimate(shipment.order.shippingCountry);

  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-2xl flex-1 px-6 py-10">
        <h1 className="text-2xl font-semibold text-brand-ink">Tracking {shipment.trackingNumber}</h1>
        <p className="mt-2 text-sm text-brand-muted">Status: {shipment.status}</p>
        {estimate && (
          <p className="text-sm text-brand-muted">
            Estimated delivery: {estimate.minDays}-{estimate.maxDays} days from dispatch
          </p>
        )}

        <ol className="mt-6 flex flex-col gap-3 border-l border-brand-border pl-4 text-sm">
          {shipment.milestones.map((m) => (
            <li key={m.id} className="relative">
              <span className="absolute -left-[21px] top-1 h-2 w-2 rounded-full bg-brand-accent" />
              <p className="font-medium text-brand-ink">{m.label}</p>
              <p className="text-xs text-brand-muted">
                {m.occurredAt.toLocaleString()} {m.location ? `- ${m.location}` : ""}
              </p>
            </li>
          ))}
          {shipment.milestones.length === 0 && (
            <li className="text-brand-muted">No updates yet.</li>
          )}
        </ol>
      </main>
      <SiteFooter />
    </>
  );
}

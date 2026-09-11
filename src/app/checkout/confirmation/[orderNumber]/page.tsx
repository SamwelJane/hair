import Link from "next/link";
import { notFound } from "next/navigation";
import { SiteHeader } from "@/components/storefront/SiteHeader";
import { SiteFooter } from "@/components/storefront/SiteFooter";
import { auth } from "@/auth";
import { db } from "@/lib/db";
import { BANK_TRANSFER_DETAILS } from "@/lib/payments/bank-transfer/adapter";

export default async function OrderConfirmationPage({
  params,
}: {
  params: Promise<{ orderNumber: string }>;
}) {
  const { orderNumber } = await params;
  const session = await auth();

  const order = await db.order.findUnique({
    where: { orderNumber },
    include: { items: { include: { product: true } }, payments: true },
  });

  if (!order || order.userId !== session?.user?.id) notFound();

  const payment = order.payments[order.payments.length - 1];

  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-2xl flex-1 px-6 py-10">
        <p className="text-sm font-medium text-brand-accent">✓ Order placed</p>
        <h1 className="text-2xl font-semibold text-brand-ink">Thank you! Order {order.orderNumber}</h1>
        <p className="mt-2 text-sm text-brand-muted">Status: {order.status}</p>

        <ul className="mt-6 flex flex-col gap-2 text-sm text-brand-ink">
          {order.items.map((item) => (
            <li key={item.id} className="flex justify-between">
              <span>
                {item.quantity}x {item.product.name}
              </span>
              <span>${item.lineTotalUsd.toString()}</span>
            </li>
          ))}
        </ul>

        <p className="mt-4 text-lg font-semibold text-brand-ink">
          Total: ${order.totalAmountUsd.toString()} (KES {order.totalAmountKes?.toString()})
        </p>

        {payment?.provider === "MPESA" && (
          <p className="mt-4 rounded border border-brand-border bg-brand-surface p-4 text-sm text-brand-ink">
            Check your phone to complete the M-Pesa payment for KES {order.totalAmountKes?.toString()}.
          </p>
        )}

        {payment?.provider === "BANK_TRANSFER" && (
          <div className="mt-4 rounded border border-brand-border bg-brand-surface p-4 text-sm text-brand-ink">
            <p className="font-medium">Bank Transfer Details</p>
            <p>Bank: {BANK_TRANSFER_DETAILS.bankName}</p>
            <p>Account name: {BANK_TRANSFER_DETAILS.accountName}</p>
            <p>Account number: {BANK_TRANSFER_DETAILS.accountNumber}</p>
            <p>Amount: KES {order.totalAmountKes?.toString()}</p>
            <p>Reference: {order.orderNumber}</p>
            <p className="mt-2 text-xs text-brand-muted">
              Your order will be marked paid once our team confirms receipt.
            </p>
          </div>
        )}

        <p className="mt-6 text-xs text-brand-muted">
          Track this order any time from your{" "}
          <Link href="/account/orders" className="text-brand-accent underline">
            account page
          </Link>
          .
        </p>
      </main>
      <SiteFooter />
    </>
  );
}

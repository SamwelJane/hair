import { db } from "@/lib/db";
import { requireAdminSession } from "@/lib/auth/require-admin";
import { confirmBankTransferPayment } from "@/lib/payments/bank-transfer/confirm";
import { revalidatePath } from "next/cache";

async function confirmPayment(formData: FormData) {
  "use server";
  const session = await requireAdminSession();
  const paymentId = formData.get("paymentId") as string;

  await confirmBankTransferPayment(paymentId, session.user.id);
  revalidatePath("/admin/payments");
}

export default async function AdminPaymentsPage() {
  await requireAdminSession();

  const pendingPayments = await db.payment.findMany({
    where: { provider: "BANK_TRANSFER", status: { in: ["INITIATED", "PENDING"] } },
    include: { order: { include: { user: true } } },
    orderBy: { createdAt: "desc" },
  });

  return (
    <div className="mx-auto max-w-4xl p-6 text-admin-ink">
      <h1 className="text-2xl font-semibold">Pending Bank Transfer Payments</h1>

      <table className="mt-6 w-full text-left text-sm">
        <thead>
          <tr className="border-b border-admin-border text-admin-muted">
            <th className="py-2">Order</th>
            <th>Customer</th>
            <th>Amount (KES)</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {pendingPayments.map((p) => (
            <tr key={p.id} className="border-b border-admin-border/60">
              <td className="py-2">{p.order.orderNumber}</td>
              <td>{p.order.user.email}</td>
              <td>{p.amountKes.toString()}</td>
              <td>
                <form action={confirmPayment}>
                  <input type="hidden" name="paymentId" value={p.id} />
                  <button type="submit" className="rounded bg-admin-good px-3 py-1 text-xs text-white hover:opacity-90">
                    Confirm Received
                  </button>
                </form>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {pendingPayments.length === 0 && (
        <p className="mt-4 text-sm text-admin-muted">No pending bank transfer payments.</p>
      )}
    </div>
  );
}

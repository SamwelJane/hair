import { db } from "@/lib/db";
import { rateLimit } from "@/lib/security/rate-limit";
import { logAudit } from "@/lib/security/audit";

export async function confirmBankTransferPayment(paymentId: string, adminUserId: string): Promise<void> {
  const limit = await rateLimit(`confirm-bank-transfer:${adminUserId}`, 30, 60);
  if (!limit.allowed) {
    throw new Error("Too many payment confirmations in a short time. Please slow down.");
  }

  const payment = await db.payment.findUniqueOrThrow({ where: { id: paymentId } });
  if (payment.provider !== "BANK_TRANSFER") {
    throw new Error("Not a bank transfer payment");
  }

  await db.$transaction(async (tx) => {
    await tx.payment.update({
      where: { id: payment.id },
      data: { status: "SUCCESS", confirmedById: adminUserId },
    });

    const order = await tx.order.findUniqueOrThrow({ where: { id: payment.orderId } });
    await tx.order.update({ where: { id: order.id }, data: { status: "PAID" } });
    await tx.orderStatusHistory.create({
      data: {
        orderId: order.id,
        fromStatus: order.status,
        toStatus: "PAID",
        changedById: adminUserId,
        note: "Bank transfer manually confirmed by admin",
      },
    });
  });

  await logAudit({
    userId: adminUserId,
    action: "CONFIRM_BANK_TRANSFER_PAYMENT",
    entityType: "Payment",
    entityId: payment.id,
    metadata: { orderId: payment.orderId, amountKes: payment.amountKes.toString() },
  });
}

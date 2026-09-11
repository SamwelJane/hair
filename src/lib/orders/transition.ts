import { db } from "@/lib/db";
import type { OrderStatus } from "@/generated/prisma/client";
import { assertValidTransition } from "./state-machine";
import { enqueueNotifySupplier } from "@/lib/queue/jobs/notify-supplier";
import { logAudit } from "@/lib/security/audit";

export async function transitionOrderStatus(
  orderId: string,
  toStatus: OrderStatus,
  actorUserId: string,
  note?: string
): Promise<void> {
  const order = await db.order.findUniqueOrThrow({
    where: { id: orderId },
    include: { items: { include: { product: true } } },
  });

  assertValidTransition(order.status, toStatus);

  await db.$transaction(async (tx) => {
    await tx.order.update({ where: { id: orderId }, data: { status: toStatus } });
    await tx.orderStatusHistory.create({
      data: { orderId, fromStatus: order.status, toStatus, changedById: actorUserId, note },
    });

    if (toStatus === "SENT_TO_SUPPLIER") {
      const supplierIds = [...new Set(order.items.map((item) => item.product.supplierId))];
      for (const supplierId of supplierIds) {
        const existing = await tx.supplierOrder.findFirst({ where: { orderId, supplierId } });
        if (!existing) {
          await tx.supplierOrder.create({ data: { orderId, supplierId, status: "SENT" } });
        }
      }
    }
  });

  if (toStatus === "SENT_TO_SUPPLIER") {
    const supplierOrders = await db.supplierOrder.findMany({ where: { orderId } });
    for (const so of supplierOrders) {
      await enqueueNotifySupplier(so.id);
    }
  }

  await logAudit({
    userId: actorUserId,
    action: "TRANSITION_ORDER_STATUS",
    entityType: "Order",
    entityId: orderId,
    metadata: { from: order.status, to: toStatus, note },
  });
}

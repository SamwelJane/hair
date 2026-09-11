import { db } from "@/lib/db";

export interface SupplierPerformance {
  totalOrders: number;
  completedOrders: number;
  avgProcessingDays: number | null;
  onTimeRatePct: number | null;
}

/**
 * Processing time is measured from when a SupplierOrder was sent to when it
 * was confirmed ready (confirmedAt). "On time" compares that duration against
 * the product's declared processingTimeDays (using the slowest product in
 * that supplier order as the bar to clear).
 */
export async function getSupplierPerformance(supplierId: string): Promise<SupplierPerformance> {
  const supplierOrders = await db.supplierOrder.findMany({
    where: { supplierId },
    include: {
      order: { include: { items: { where: {}, include: { product: true } } } },
    },
  });

  const completed = supplierOrders.filter((so) => so.confirmedAt);

  if (completed.length === 0) {
    return {
      totalOrders: supplierOrders.length,
      completedOrders: 0,
      avgProcessingDays: null,
      onTimeRatePct: null,
    };
  }

  let totalDays = 0;
  let onTimeCount = 0;

  for (const so of completed) {
    const days = (so.confirmedAt!.getTime() - so.sentAt.getTime()) / (1000 * 60 * 60 * 24);
    totalDays += days;

    const relevantItems = so.order.items.filter((item) => item.product.supplierId === supplierId);
    const expectedDays = Math.max(...relevantItems.map((i) => i.product.processingTimeDays), 0);
    if (days <= expectedDays) onTimeCount++;
  }

  return {
    totalOrders: supplierOrders.length,
    completedOrders: completed.length,
    avgProcessingDays: Math.round((totalDays / completed.length) * 10) / 10,
    onTimeRatePct: Math.round((onTimeCount / completed.length) * 1000) / 10,
  };
}

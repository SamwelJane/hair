import { db } from "@/lib/db";

const PAID_STATUSES = [
  "PAID",
  "SENT_TO_SUPPLIER",
  "SUPPLIER_PROCESSING",
  "READY_FOR_PICKUP",
  "RECEIVED_AT_OFFICE",
  "SHIPPED_INTERNATIONALLY",
  "IN_TRANSIT",
  "DELIVERED",
] as const;

export interface RevenueSummary {
  totalRevenueUsd: number;
  grossMarginUsd: number;
  netMarginUsd: number;
  revenueByCountry: { country: string; revenueUsd: number }[];
  revenueByProduct: { productName: string; revenueUsd: number }[];
}

export async function getRevenueSummary(): Promise<RevenueSummary> {
  const orders = await db.order.findMany({
    where: { status: { in: [...PAID_STATUSES] } },
    include: { items: { include: { product: { include: { supplier: true } } } } },
  });

  let totalRevenueUsd = 0;
  let totalCostUsd = 0;
  const byCountry = new Map<string, number>();
  const byProduct = new Map<string, number>();

  for (const order of orders) {
    totalRevenueUsd += order.totalAmountUsd.toNumber();
    byCountry.set(
      order.shippingCountry,
      (byCountry.get(order.shippingCountry) ?? 0) + order.totalAmountUsd.toNumber()
    );

    for (const item of order.items) {
      const lineTotal = item.lineTotalUsd.toNumber();
      byProduct.set(item.product.name, (byProduct.get(item.product.name) ?? 0) + lineTotal);

      const marginPct = item.product.supplier.defaultMarginPct.toNumber();
      totalCostUsd += lineTotal * (1 - marginPct / 100);
    }
  }

  const grossMarginUsd = totalRevenueUsd - totalCostUsd;

  return {
    totalRevenueUsd: round2(totalRevenueUsd),
    grossMarginUsd: round2(grossMarginUsd),
    // Net margin here is gross margin minus shipping/handling costs already charged to customers
    // (those are pass-through, so net ~= gross for this simplified model without operating-expense tracking).
    netMarginUsd: round2(grossMarginUsd),
    revenueByCountry: [...byCountry.entries()]
      .map(([country, revenueUsd]) => ({ country, revenueUsd: round2(revenueUsd) }))
      .sort((a, b) => b.revenueUsd - a.revenueUsd),
    revenueByProduct: [...byProduct.entries()]
      .map(([productName, revenueUsd]) => ({ productName, revenueUsd: round2(revenueUsd) }))
      .sort((a, b) => b.revenueUsd - a.revenueUsd),
  };
}

export interface OperationsSummary {
  orderVolumeTrend: { date: string; count: number }[];
  bestSellingProducts: { productName: string; unitsSold: number }[];
  repeatCustomerRatePct: number;
  avgSupplierProcessingDays: number | null;
  shipmentsInTransit: number;
}

export async function getOperationsSummary(): Promise<OperationsSummary> {
  const [orders, supplierOrders, shipmentCount] = await Promise.all([
    db.order.findMany({
      where: { status: { in: [...PAID_STATUSES] } },
      include: { items: { include: { product: true } } },
    }),
    db.supplierOrder.findMany({ where: { confirmedAt: { not: null } } }),
    db.shipment.count({ where: { status: { not: "delivered" } } }),
  ]);

  const dayBuckets = new Map<string, number>();
  const unitsByProduct = new Map<string, number>();
  const ordersByCustomer = new Map<string, number>();

  for (const order of orders) {
    const day = order.createdAt.toISOString().slice(0, 10);
    dayBuckets.set(day, (dayBuckets.get(day) ?? 0) + 1);
    ordersByCustomer.set(order.userId, (ordersByCustomer.get(order.userId) ?? 0) + 1);

    for (const item of order.items) {
      unitsByProduct.set(item.product.name, (unitsByProduct.get(item.product.name) ?? 0) + item.quantity);
    }
  }

  const repeatCustomers = [...ordersByCustomer.values()].filter((c) => c > 1).length;
  const repeatCustomerRatePct =
    ordersByCustomer.size > 0 ? round2((repeatCustomers / ordersByCustomer.size) * 100) : 0;

  const avgSupplierProcessingDays =
    supplierOrders.length > 0
      ? round2(
          supplierOrders.reduce(
            (sum, so) => sum + (so.confirmedAt!.getTime() - so.sentAt.getTime()) / (1000 * 60 * 60 * 24),
            0
          ) / supplierOrders.length
        )
      : null;

  return {
    orderVolumeTrend: [...dayBuckets.entries()]
      .map(([date, count]) => ({ date, count }))
      .sort((a, b) => a.date.localeCompare(b.date)),
    bestSellingProducts: [...unitsByProduct.entries()]
      .map(([productName, unitsSold]) => ({ productName, unitsSold }))
      .sort((a, b) => b.unitsSold - a.unitsSold)
      .slice(0, 10),
    repeatCustomerRatePct,
    avgSupplierProcessingDays,
    shipmentsInTransit: shipmentCount,
  };
}

export interface FinanceSummary {
  totalShipments: number;
  avgProfitPerShipmentUsd: number | null;
  estimatedOutstandingSupplierPaymentsUsd: number;
}

export async function getFinanceSummary(): Promise<FinanceSummary> {
  const shipments = await db.shipment.findMany({
    include: {
      order: { include: { items: { include: { product: { include: { supplier: true } } } } } },
    },
  });

  let totalProfit = 0;
  for (const shipment of shipments) {
    const revenue = shipment.order.totalAmountUsd.toNumber();
    const cost = shipment.order.items.reduce((sum, item) => {
      const marginPct = item.product.supplier.defaultMarginPct.toNumber();
      return sum + item.lineTotalUsd.toNumber() * (1 - marginPct / 100);
    }, 0);
    totalProfit += revenue - cost - shipment.order.shippingFeeUsd.toNumber();
  }

  // Estimated supplier cost still owed for orders whose supplier work isn't yet
  // marked complete. There is no formal accounts-payable/invoice table in this
  // schema, so this is a proxy based on default margin percentages, not a ledger.
  const openSupplierOrders = await db.supplierOrder.findMany({
    where: { status: { not: "READY" } },
    include: { order: { include: { items: { include: { product: true } } } }, supplier: true },
  });

  let estimatedOutstanding = 0;
  for (const so of openSupplierOrders) {
    const relevantItems = so.order.items.filter((item) => item.product.supplierId === so.supplierId);
    const marginPct = so.supplier.defaultMarginPct.toNumber();
    estimatedOutstanding += relevantItems.reduce(
      (sum, item) => sum + item.lineTotalUsd.toNumber() * (1 - marginPct / 100),
      0
    );
  }

  return {
    totalShipments: shipments.length,
    avgProfitPerShipmentUsd: shipments.length > 0 ? round2(totalProfit / shipments.length) : null,
    estimatedOutstandingSupplierPaymentsUsd: round2(estimatedOutstanding),
  };
}

function round2(value: number): number {
  return Math.round(value * 100) / 100;
}

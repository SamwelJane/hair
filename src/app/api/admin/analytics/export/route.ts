import { NextResponse } from "next/server";
import { requireAdminSession } from "@/lib/auth/require-admin";
import { getRevenueSummary, getOperationsSummary, getFinanceSummary } from "@/lib/analytics/queries";
import { toCsv } from "@/lib/analytics/csv";
import { db } from "@/lib/db";

export async function GET(request: Request) {
  try {
    await requireAdminSession();
  } catch {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const type = new URL(request.url).searchParams.get("type") ?? "revenue";
  let csv = "";
  let filename = "export.csv";

  if (type === "revenue") {
    const revenue = await getRevenueSummary();
    csv = toCsv(revenue.revenueByCountry.map((r) => ({ country: r.country, revenueUsd: r.revenueUsd })));
    filename = "revenue-by-country.csv";
  } else if (type === "products") {
    const revenue = await getRevenueSummary();
    csv = toCsv(revenue.revenueByProduct.map((r) => ({ product: r.productName, revenueUsd: r.revenueUsd })));
    filename = "revenue-by-product.csv";
  } else if (type === "operations") {
    const operations = await getOperationsSummary();
    csv = toCsv(operations.orderVolumeTrend.map((d) => ({ date: d.date, orders: d.count })));
    filename = "order-volume-trend.csv";
  } else if (type === "monthly") {
    const now = new Date();
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    const orders = await db.order.findMany({
      where: { createdAt: { gte: startOfMonth } },
      orderBy: { createdAt: "asc" },
    });
    csv = toCsv(
      orders.map((o) => ({
        orderNumber: o.orderNumber,
        date: o.createdAt.toISOString().slice(0, 10),
        status: o.status,
        totalUsd: o.totalAmountUsd.toString(),
        country: o.shippingCountry,
      }))
    );
    filename = `monthly-report-${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}.csv`;
  } else if (type === "finance") {
    const finance = await getFinanceSummary();
    csv = toCsv([
      { metric: "Total Shipments", value: finance.totalShipments },
      { metric: "Avg Profit per Shipment (USD)", value: finance.avgProfitPerShipmentUsd ?? 0 },
      {
        metric: "Estimated Outstanding Supplier Payments (USD)",
        value: finance.estimatedOutstandingSupplierPaymentsUsd,
      },
    ]);
    filename = "finance-summary.csv";
  }

  return new NextResponse(csv, {
    headers: {
      "Content-Type": "text/csv",
      "Content-Disposition": `attachment; filename="${filename}"`,
    },
  });
}

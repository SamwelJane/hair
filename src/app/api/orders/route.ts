import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { db } from "@/lib/db";
import { checkoutSchema } from "@/lib/validation/checkout";
import { calculateCartBreakdown } from "@/lib/pricing/cart-breakdown";
import { getUsdToKesRate, convertUsdToKes } from "@/lib/pricing/exchange-rate";
import { generateOrderNumber } from "@/lib/orders/order-number";
import { mpesaProvider } from "@/lib/payments/mpesa/adapter";
import { bankTransferProvider, BANK_TRANSFER_DETAILS } from "@/lib/payments/bank-transfer/adapter";
import { rateLimit } from "@/lib/security/rate-limit";
import { logAudit } from "@/lib/security/audit";

export async function POST(request: Request) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "You must be signed in to check out." }, { status: 401 });
  }

  const orderLimit = await rateLimit(`create-order:${session.user.id}`, 10, 10 * 60);
  if (!orderLimit.allowed) {
    return NextResponse.json(
      { error: "Too many checkout attempts. Please wait a few minutes and try again." },
      { status: 429 }
    );
  }

  const parsed = checkoutSchema.safeParse(await request.json());
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 });
  }
  const input = parsed.data;

  if (input.paymentMethod === "MPESA" && !input.mpesaPhone) {
    return NextResponse.json({ error: "Phone number is required for M-Pesa." }, { status: 400 });
  }

  if (input.paymentMethod === "MPESA" && input.mpesaPhone) {
    const stkLimit = await rateLimit(`stk-push:${input.mpesaPhone}`, 3, 10 * 60);
    if (!stkLimit.allowed) {
      return NextResponse.json(
        { error: "Too many M-Pesa prompts sent to this number recently. Please wait and try again." },
        { status: 429 }
      );
    }
  }

  let breakdown, resolvedLines;
  try {
    ({ breakdown, resolvedLines } = await calculateCartBreakdown(
      input.items,
      input.shippingAddress.countryCode,
      input.discountCode
    ));
  } catch (err) {
    return NextResponse.json({ error: (err as Error).message }, { status: 400 });
  }

  const exchangeRate = await getUsdToKesRate();
  const totalAmountKes = convertUsdToKes(breakdown.totalAmountUsd, exchangeRate);
  const orderNumber = generateOrderNumber();

  const order = await db.order.create({
    data: {
      orderNumber,
      userId: session.user.id,
      status: "PENDING_PAYMENT",
      subtotalUsd: breakdown.subtotalUsd,
      shippingFeeUsd: breakdown.shippingFeeUsd,
      handlingFeeUsd: breakdown.handlingFeeUsd,
      customsEstimateUsd: breakdown.customsEstimateUsd,
      totalAmountUsd: breakdown.totalAmountUsd,
      exchangeRateApplied: exchangeRate,
      totalAmountKes,
      shippingCountry: input.shippingAddress.countryCode,
      shippingAddress: input.shippingAddress,
      items: {
        create: resolvedLines.map((line) => ({
          productId: line.productId,
          variantId: line.variantId,
          quantity: line.quantity,
          unitPriceUsdAtPurchase: line.unitPriceUsd,
          lineTotalUsd: line.unitPriceUsd * line.quantity,
        })),
      },
      statusHistory: {
        create: [{ toStatus: "PENDING_PAYMENT", note: "Order created at checkout" }],
      },
    },
  });

  await logAudit({
    userId: session.user.id,
    action: "CREATE_ORDER",
    entityType: "Order",
    entityId: order.id,
    metadata: { totalAmountUsd: breakdown.totalAmountUsd, paymentMethod: input.paymentMethod },
  });

  let paymentInstructions: Record<string, unknown> = {};

  if (input.paymentMethod === "MPESA") {
    try {
      const result = await mpesaProvider.initiate({
        orderId: order.id,
        amountKes: totalAmountKes,
        phone: input.mpesaPhone,
      });
      await db.payment.create({
        data: {
          orderId: order.id,
          provider: "MPESA",
          providerRef: result.providerRef,
          amountKes: totalAmountKes,
          status: result.status,
        },
      });
      paymentInstructions = { message: "Check your phone to complete the M-Pesa payment." };
    } catch (err) {
      await db.payment.create({
        data: { orderId: order.id, provider: "MPESA", amountKes: totalAmountKes, status: "FAILED" },
      });
      paymentInstructions = {
        error: `M-Pesa is not configured yet in this environment: ${(err as Error).message}`,
      };

      // Basic fraud/abuse signal: repeated failed payment initiations from the
      // same account in a short window get flagged for admin review.
      const failureCount = await rateLimit(`mpesa-failures:${session.user.id}`, 3, 30 * 60);
      if (!failureCount.allowed) {
        await logAudit({
          userId: session.user.id,
          action: "FRAUD_FLAG_REPEATED_PAYMENT_FAILURES",
          entityType: "Order",
          entityId: order.id,
          metadata: { reason: "3+ failed M-Pesa initiations within 30 minutes" },
        });
      }
    }
  } else {
    const result = await bankTransferProvider.initiate({ orderId: order.id, amountKes: totalAmountKes });
    await db.payment.create({
      data: {
        orderId: order.id,
        provider: "BANK_TRANSFER",
        providerRef: result.providerRef,
        amountKes: totalAmountKes,
        status: result.status,
      },
    });
    paymentInstructions = { bankDetails: BANK_TRANSFER_DETAILS, amountKes: totalAmountKes };
  }

  return NextResponse.json({ orderNumber: order.orderNumber, paymentInstructions });
}

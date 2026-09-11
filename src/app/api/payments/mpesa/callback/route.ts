import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { rateLimit, getClientIp } from "@/lib/security/rate-limit";
import { logAudit } from "@/lib/security/audit";

interface DarajaCallbackItem {
  Name: string;
  Value?: string | number;
}

interface DarajaCallbackBody {
  Body: {
    stkCallback: {
      MerchantRequestID: string;
      CheckoutRequestID: string;
      ResultCode: number;
      ResultDesc: string;
      CallbackMetadata?: { Item: DarajaCallbackItem[] };
    };
  };
}

export async function POST(request: Request) {
  // This webhook has no shared-secret signature from Safaricom, so it's rate
  // limited per source IP as a basic abuse guard; the real trust anchor is
  // that we only act when CheckoutRequestID matches a payment we ourselves
  // initiated (see lookup below) - an attacker can't invent a valid ref.
  const ip = getClientIp(request);
  const limit = await rateLimit(`mpesa-callback:${ip}`, 60, 60);
  if (!limit.allowed) {
    return NextResponse.json({ ResultCode: 1, ResultDesc: "Rate limited" }, { status: 429 });
  }

  const payload = (await request.json()) as DarajaCallbackBody;
  const callback = payload.Body.stkCallback;

  const payment = await db.payment.findFirst({
    where: { provider: "MPESA", providerRef: callback.CheckoutRequestID },
  });

  if (!payment) {
    // Acknowledge anyway so Safaricom doesn't retry indefinitely on an unknown ref.
    return NextResponse.json({ ResultCode: 0, ResultDesc: "Accepted" });
  }

  const isSuccess = callback.ResultCode === 0;
  const receiptItem = callback.CallbackMetadata?.Item.find((i) => i.Name === "MpesaReceiptNumber");

  await db.$transaction(async (tx) => {
    await tx.payment.update({
      where: { id: payment.id },
      data: {
        status: isSuccess ? "SUCCESS" : "FAILED",
        providerRef: (receiptItem?.Value as string) ?? payment.providerRef,
        rawCallbackPayload: payload as unknown as object,
      },
    });

    if (isSuccess) {
      const order = await tx.order.findUniqueOrThrow({ where: { id: payment.orderId } });
      await tx.order.update({ where: { id: order.id }, data: { status: "PAID" } });
      await tx.orderStatusHistory.create({
        data: {
          orderId: order.id,
          fromStatus: order.status,
          toStatus: "PAID",
          note: `M-Pesa payment confirmed (${callback.ResultDesc})`,
        },
      });
    }
  });

  await logAudit({
    action: isSuccess ? "MPESA_PAYMENT_SUCCESS" : "MPESA_PAYMENT_FAILED",
    entityType: "Payment",
    entityId: payment.id,
    metadata: { resultDesc: callback.ResultDesc, orderId: payment.orderId },
  });

  return NextResponse.json({ ResultCode: 0, ResultDesc: "Accepted" });
}

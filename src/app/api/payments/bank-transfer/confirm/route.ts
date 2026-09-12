import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { isAdminRole } from "@/lib/auth/rbac";
import { confirmBankTransferPayment } from "@/lib/payments/bank-transfer/confirm";

export async function POST(request: Request) {
  const session = await auth();
  if (!session || !isAdminRole(session.user.role)) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const { paymentId } = (await request.json()) as { paymentId: string };

  try {
    await confirmBankTransferPayment(paymentId, session.user.id);
  } catch (err) {
    return NextResponse.json({ error: (err as Error).message }, { status: 400 });
  }

  return NextResponse.json({ ok: true });
}

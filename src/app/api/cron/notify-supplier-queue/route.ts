import { NextResponse } from "next/server";
import { drainNotifySupplierQueue } from "@/lib/queue/jobs/notify-supplier";

export async function GET(request: Request) {
  const authHeader = request.headers.get("authorization");
  if (process.env.CRON_SECRET && authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const result = await drainNotifySupplierQueue();
  return NextResponse.json(result);
}

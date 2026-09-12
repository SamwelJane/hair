import { redis } from "../redis-client";
import { db } from "@/lib/db";
import { sendEmail, supplierOrderEmail } from "@/lib/notifications/email";
import { sendWhatsApp, supplierOrderWhatsAppMessage } from "@/lib/notifications/whatsapp";

const QUEUE_KEY = "queue:notify-supplier";

export interface NotifySupplierJob {
  supplierOrderId: string;
}

export async function enqueueNotifySupplier(supplierOrderId: string): Promise<void> {
  await redis.rpush(QUEUE_KEY, JSON.stringify({ supplierOrderId } satisfies NotifySupplierJob));
}

async function processOne(job: NotifySupplierJob): Promise<void> {
  const supplierOrder = await db.supplierOrder.findUniqueOrThrow({
    where: { id: job.supplierOrderId },
    include: {
      supplier: true,
      order: { include: { items: { include: { product: true, variant: true } } } },
    },
  });

  const productLines = supplierOrder.order.items.map(
    (item) =>
      `${item.quantity}x ${item.product.name}${item.variant ? ` (${item.variant.length ?? ""} ${item.variant.color ?? ""})`.trim() : ""}`
  );

  const email = supplierOrderEmail({
    supplierName: supplierOrder.supplier.name,
    orderNumber: supplierOrder.order.orderNumber,
    productLines,
  });

  await sendEmail({ to: supplierOrder.supplier.email, subject: email.subject, html: email.html });

  await sendWhatsApp({
    to: supplierOrder.supplier.whatsappNumber,
    body: supplierOrderWhatsAppMessage({
      supplierName: supplierOrder.supplier.name,
      orderNumber: supplierOrder.order.orderNumber,
      productLines,
    }),
  });
}

/**
 * Drains the queue. Called from a Vercel Cron route rather than run as a
 * persistent worker, since Vercel serverless functions cannot stay resident.
 * Failed jobs are re-queued once for a retry on the next tick.
 */
export async function drainNotifySupplierQueue(maxJobs = 20): Promise<{ processed: number; failed: number }> {
  let processed = 0;
  let failed = 0;

  for (let i = 0; i < maxJobs; i++) {
    const raw = await redis.lpop(QUEUE_KEY);
    if (!raw) break;

    const job = JSON.parse(raw) as NotifySupplierJob & { _retried?: boolean };
    try {
      await processOne(job);
      processed++;
    } catch (err) {
      console.error("[notify-supplier] job failed:", err);
      failed++;
      if (!job._retried) {
        await redis.rpush(QUEUE_KEY, JSON.stringify({ ...job, _retried: true }));
      }
    }
  }

  return { processed, failed };
}

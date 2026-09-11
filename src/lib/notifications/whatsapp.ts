import twilio from "twilio";

function getClient() {
  const sid = process.env.TWILIO_ACCOUNT_SID;
  const token = process.env.TWILIO_AUTH_TOKEN;
  if (!sid || !token) return null;
  return twilio(sid, token);
}

export interface SendWhatsAppInput {
  to: string; // e.g. "+84900000001"
  body: string;
}

export async function sendWhatsApp(input: SendWhatsAppInput): Promise<void> {
  const client = getClient();
  if (!client) {
    console.warn("[whatsapp] Twilio not configured, skipping send:", input.to);
    return;
  }

  await client.messages.create({
    from: process.env.TWILIO_WHATSAPP_FROM ?? "whatsapp:+254712197226",
    to: `whatsapp:${input.to}`,
    body: input.body,
  });
}

export function customerOrderStatusWhatsAppMessage(params: { orderNumber: string; status: string; trackingNumber?: string }): string {
  const tracking = params.trackingNumber ? ` Tracking number: ${params.trackingNumber}.` : "";
  return `Hiar Business update: order ${params.orderNumber} is now ${params.status.replaceAll("_", " ").toLowerCase()}.${tracking}`;
}

export function supplierOrderWhatsAppMessage(params: {
  supplierName: string;
  orderNumber: string;
  productLines: string[];
}): string {
  return [
    `Hello ${params.supplierName}, new order to produce: ${params.orderNumber}.`,
    ...params.productLines.map((l) => `- ${l}`),
    "Please confirm receipt and expected completion time.",
  ].join("\n");
}

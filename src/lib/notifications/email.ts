import { Resend } from "resend";

export interface SendEmailInput {
  to: string;
  subject: string;
  html: string;
}

export async function sendEmail(input: SendEmailInput): Promise<void> {
  if (!process.env.RESEND_API_KEY) {
    console.warn("[email] RESEND_API_KEY not set, skipping send:", input.subject, "->", input.to);
    return;
  }

  const resend = new Resend(process.env.RESEND_API_KEY);
  await resend.emails.send({
    from: process.env.EMAIL_FROM ?? "orders@hiarbusiness.com",
    to: input.to,
    subject: input.subject,
    html: input.html,
  });
}

export function supplierOrderEmail(params: {
  supplierName: string;
  orderNumber: string;
  productLines: string[];
}): { subject: string; html: string } {
  return {
    subject: `New order to produce: ${params.orderNumber}`,
    html: `
      <p>Hello ${params.supplierName},</p>
      <p>A new order has been sent to you for production:</p>
      <ul>${params.productLines.map((line) => `<li>${line}</li>`).join("")}</ul>
      <p>Order reference: <strong>${params.orderNumber}</strong></p>
      <p>Please confirm receipt and expected completion time.</p>
    `,
  };
}

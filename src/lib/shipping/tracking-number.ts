import { db } from "@/lib/db";

function randomSuffix(length: number): string {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"; // no ambiguous chars (0/O, 1/I)
  let out = "";
  for (let i = 0; i < length; i++) {
    out += chars[Math.floor(Math.random() * chars.length)];
  }
  return out;
}

/** Generates a unique HB-YYYYMMDD-XXXXX tracking number, retrying on collision. */
export async function generateTrackingNumber(): Promise<string> {
  const now = new Date();
  const datePart = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, "0")}${String(
    now.getDate()
  ).padStart(2, "0")}`;

  for (let attempt = 0; attempt < 5; attempt++) {
    const candidate = `HB-${datePart}-${randomSuffix(5)}`;
    const existing = await db.shipment.findUnique({ where: { trackingNumber: candidate } });
    if (!existing) return candidate;
  }

  throw new Error("Failed to generate a unique tracking number after 5 attempts.");
}

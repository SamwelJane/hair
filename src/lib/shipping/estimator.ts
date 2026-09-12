import { db } from "@/lib/db";

export interface DeliveryEstimate {
  minDays: number;
  maxDays: number;
}

export async function getDeliveryEstimate(countryCode: string): Promise<DeliveryEstimate | null> {
  const rule = await db.countryShippingRule.findUnique({ where: { countryCode } });
  if (!rule) return null;

  return { minDays: rule.estimatedDaysMin, maxDays: rule.estimatedDaysMax };
}

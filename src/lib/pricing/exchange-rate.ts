import { db } from "@/lib/db";

/**
 * Reads the admin-set USD -> KES rate. There is no live FX API call here by design:
 * the admin sets the rate in /admin/settings/exchange-rate and that is the rate
 * charged to customers at checkout, regardless of the real market rate.
 */
export async function getUsdToKesRate(): Promise<number> {
  const rate = await db.exchangeRate.findUnique({
    where: { baseCurrency_targetCurrency: { baseCurrency: "USD", targetCurrency: "KES" } },
  });

  if (!rate) {
    throw new Error("No USD->KES exchange rate has been set by an admin yet.");
  }

  return rate.rate.toNumber();
}

export function convertUsdToKes(amountUsd: number, rate: number, adjustment = 4): number {
  return Math.round(amountUsd * (rate + adjustment) * 100) / 100;
}

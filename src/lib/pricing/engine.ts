import type { CountryShippingRule, DiscountCode } from "@/generated/prisma/client";

export interface PriceLineItem {
  unitPriceUsd: number;
  quantity: number;
}

export interface PriceBreakdown {
  subtotalUsd: number;
  shippingFeeUsd: number;
  handlingFeeUsd: number;
  customsEstimateUsd: number;
  discountUsd: number;
  totalAmountUsd: number;
  totalWeightGrams: number;
}

export interface CalculatePriceInput {
  items: PriceLineItem[];
  totalWeightGrams: number;
  shippingRule: Pick<CountryShippingRule, "baseFeeUsd" | "perKgFeeUsd" | "customsRatePct">;
  handlingFeeUsd?: number;
  discountCode?: Pick<DiscountCode, "type" | "value" | "minOrderUsd"> | null;
}

function toNumber(value: number | { toNumber(): number }): number {
  return typeof value === "number" ? value : value.toNumber();
}

/**
 * Total = (unit price * qty) + shipping + handling + customs - discount.
 * Shipping = baseFee + perKgFee * weight; customs = customsRatePct% of subtotal.
 */
export function calculatePrice(input: CalculatePriceInput): PriceBreakdown {
  const subtotalUsd = round2(
    input.items.reduce((sum, item) => sum + item.unitPriceUsd * item.quantity, 0)
  );

  const baseFee = toNumber(input.shippingRule.baseFeeUsd);
  const perKgFee = toNumber(input.shippingRule.perKgFeeUsd);
  const customsRatePct = toNumber(input.shippingRule.customsRatePct);

  const weightKg = input.totalWeightGrams / 1000;
  const shippingFeeUsd = round2(baseFee + perKgFee * weightKg);
  const handlingFeeUsd = round2(input.handlingFeeUsd ?? 0);
  const customsEstimateUsd = round2(subtotalUsd * (customsRatePct / 100));

  let discountUsd = 0;
  if (input.discountCode) {
    const minOrder = input.discountCode.minOrderUsd ? toNumber(input.discountCode.minOrderUsd) : 0;
    if (subtotalUsd >= minOrder) {
      const value = toNumber(input.discountCode.value);
      discountUsd =
        input.discountCode.type === "percent" ? round2(subtotalUsd * (value / 100)) : round2(value);
    }
  }

  const totalAmountUsd = round2(
    Math.max(0, subtotalUsd + shippingFeeUsd + handlingFeeUsd + customsEstimateUsd - discountUsd)
  );

  return {
    subtotalUsd,
    shippingFeeUsd,
    handlingFeeUsd,
    customsEstimateUsd,
    discountUsd,
    totalAmountUsd,
    totalWeightGrams: input.totalWeightGrams,
  };
}

function round2(value: number): number {
  return Math.round(value * 100) / 100;
}

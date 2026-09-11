import { db } from "@/lib/db";
import { calculatePrice, type PriceBreakdown } from "./engine";

export interface CartLineInput {
  productId: string;
  variantId?: string;
  quantity: number;
}

export interface ResolvedCartLine extends CartLineInput {
  unitPriceUsd: number;
  weightGrams: number;
}

export async function resolveCartLines(items: CartLineInput[]): Promise<ResolvedCartLine[]> {
  const resolved: ResolvedCartLine[] = [];

  for (const item of items) {
    const [product, variant] = await Promise.all([
      db.product.findUniqueOrThrow({ where: { id: item.productId } }),
      item.variantId ? db.productVariant.findUnique({ where: { id: item.variantId } }) : null,
    ]);

    resolved.push({
      ...item,
      unitPriceUsd: product.basePriceUsd.toNumber() + (variant?.priceDeltaUsd.toNumber() ?? 0),
      weightGrams: (variant?.weightOverrideGrams ?? product.baseWeightGrams) * item.quantity,
    });
  }

  return resolved;
}

export async function calculateCartBreakdown(
  items: CartLineInput[],
  countryCode: string,
  discountCode?: string
): Promise<{ breakdown: PriceBreakdown; resolvedLines: ResolvedCartLine[] }> {
  const [shippingRule, discount, resolvedLines] = await Promise.all([
    db.countryShippingRule.findUnique({ where: { countryCode } }),
    discountCode ? db.discountCode.findFirst({ where: { code: discountCode, active: true } }) : null,
    resolveCartLines(items),
  ]);

  if (!shippingRule) {
    throw new Error(`No shipping rule configured for country ${countryCode}`);
  }

  const breakdown = calculatePrice({
    items: resolvedLines.map((l) => ({ unitPriceUsd: l.unitPriceUsd, quantity: l.quantity })),
    totalWeightGrams: resolvedLines.reduce((sum, l) => sum + l.weightGrams, 0),
    shippingRule,
    discountCode: discount,
  });

  return { breakdown, resolvedLines };
}

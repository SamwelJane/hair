import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { calculatePrice } from "@/lib/pricing/engine";

interface CalculateRequestBody {
  productId: string;
  variantId?: string;
  quantity: number;
  countryCode: string;
  discountCode?: string;
}

export async function POST(request: Request) {
  const body = (await request.json()) as CalculateRequestBody;

  const [product, variant, shippingRule, discount] = await Promise.all([
    db.product.findUniqueOrThrow({ where: { id: body.productId } }),
    body.variantId ? db.productVariant.findUnique({ where: { id: body.variantId } }) : null,
    db.countryShippingRule.findUnique({ where: { countryCode: body.countryCode } }),
    body.discountCode
      ? db.discountCode.findFirst({ where: { code: body.discountCode, active: true } })
      : null,
  ]);

  if (!shippingRule) {
    return NextResponse.json(
      { error: `No shipping rule configured for country ${body.countryCode}` },
      { status: 400 }
    );
  }

  const unitPriceUsd = product.basePriceUsd.toNumber() + (variant?.priceDeltaUsd.toNumber() ?? 0);
  const weightGrams = (variant?.weightOverrideGrams ?? product.baseWeightGrams) * body.quantity;

  const breakdown = calculatePrice({
    items: [{ unitPriceUsd, quantity: body.quantity }],
    totalWeightGrams: weightGrams,
    shippingRule,
    discountCode: discount,
  });

  return NextResponse.json(breakdown);
}

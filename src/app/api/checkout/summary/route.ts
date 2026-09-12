import { NextResponse } from "next/server";
import { calculateCartBreakdown } from "@/lib/pricing/cart-breakdown";

interface SummaryRequestBody {
  items: { productId: string; variantId?: string; quantity: number }[];
  countryCode: string;
  discountCode?: string;
}

export async function POST(request: Request) {
  const body = (await request.json()) as SummaryRequestBody;

  try {
    const { breakdown } = await calculateCartBreakdown(body.items, body.countryCode, body.discountCode);
    return NextResponse.json(breakdown);
  } catch (err) {
    return NextResponse.json({ error: (err as Error).message }, { status: 400 });
  }
}

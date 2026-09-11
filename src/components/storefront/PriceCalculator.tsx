"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useCart } from "@/components/cart/CartProvider";

export interface VariantOption {
  id: string;
  label: string;
  priceDeltaUsd: number;
}

export interface CountryOption {
  code: string;
  name: string;
}

interface PriceBreakdown {
  subtotalUsd: number;
  shippingFeeUsd: number;
  handlingFeeUsd: number;
  customsEstimateUsd: number;
  discountUsd: number;
  totalAmountUsd: number;
}

export function PriceCalculator({
  productId,
  productSlug,
  productName,
  imageUrl,
  basePriceUsd,
  variants,
  countries,
}: {
  productId: string;
  productSlug: string;
  productName: string;
  imageUrl?: string;
  basePriceUsd: number;
  variants: VariantOption[];
  countries: CountryOption[];
}) {
  const router = useRouter();
  const { addItem } = useCart();
  const [variantId, setVariantId] = useState<string | undefined>(variants[0]?.id);
  const [quantity, setQuantity] = useState(1);
  const [countryCode, setCountryCode] = useState(countries[0]?.code ?? "US");
  const [discountCode, setDiscountCode] = useState("");
  const [breakdown, setBreakdown] = useState<PriceBreakdown | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetch("/api/pricing/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        productId,
        variantId,
        quantity,
        countryCode,
        discountCode: discountCode || undefined,
      }),
    })
      .then(async (res) => {
        if (!res.ok) throw new Error((await res.json()).error ?? "Failed to calculate price");
        return res.json();
      })
      .then((data) => {
        if (!cancelled) setBreakdown(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [productId, variantId, quantity, countryCode, discountCode]);

  return (
    <div className="flex flex-col gap-4">
      {variants.length > 0 && (
        <label className="flex flex-col gap-1 text-sm text-brand-ink">
          Variant
          <select
            value={variantId}
            onChange={(e) => setVariantId(e.target.value)}
            className="rounded border border-brand-border bg-brand-surface px-3 py-2"
          >
            {variants.map((v) => (
              <option key={v.id} value={v.id}>
                {v.label} {v.priceDeltaUsd ? `(+$${v.priceDeltaUsd.toFixed(2)})` : ""}
              </option>
            ))}
          </select>
        </label>
      )}

      <label className="flex flex-col gap-1 text-sm text-brand-ink">
        Quantity
        <input
          type="number"
          min={1}
          max={50}
          value={quantity}
          onChange={(e) => setQuantity(Math.max(1, Number(e.target.value)))}
          className="w-24 rounded border border-brand-border bg-brand-surface px-3 py-2"
        />
      </label>

      <label className="flex flex-col gap-1 text-sm text-brand-ink">
        Ship to
        <select
          value={countryCode}
          onChange={(e) => setCountryCode(e.target.value)}
          className="rounded border border-brand-border bg-brand-surface px-3 py-2"
        >
          {countries.map((c) => (
            <option key={c.code} value={c.code}>
              {c.name}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 text-sm text-brand-ink">
        Discount code
        <input
          type="text"
          value={discountCode}
          onChange={(e) => setDiscountCode(e.target.value)}
          placeholder="WELCOME10"
          className="rounded border border-brand-border bg-brand-surface px-3 py-2"
        />
      </label>

      <div className="rounded border border-brand-border bg-brand-surface p-4 text-sm">
        {error && <p className="text-brand-danger">{error}</p>}
        {!error && breakdown && (
          <dl className="flex flex-col gap-1">
            <Row label="Subtotal" value={breakdown.subtotalUsd} />
            <Row label="International Shipping" value={breakdown.shippingFeeUsd} />
            {breakdown.handlingFeeUsd > 0 && <Row label="Handling" value={breakdown.handlingFeeUsd} />}
            <Row label="Customs Estimate" value={breakdown.customsEstimateUsd} />
            {breakdown.discountUsd > 0 && <Row label="Discount" value={-breakdown.discountUsd} />}
            <div className="mt-2 flex justify-between border-t border-brand-border pt-2 text-base font-semibold text-brand-ink">
              <dt>Order Total</dt>
              <dd>${breakdown.totalAmountUsd.toFixed(2)}</dd>
            </div>
          </dl>
        )}
        {loading && !breakdown && <p className="text-brand-muted">Calculating...</p>}
      </div>

      <button
        type="button"
        disabled={!breakdown}
        onClick={() => {
          const variant = variants.find((v) => v.id === variantId);
          addItem({
            productId,
            variantId,
            slug: productSlug,
            name: productName,
            variantLabel: variant?.label,
            unitPriceUsd: basePriceUsd + (variant?.priceDeltaUsd ?? 0),
            imageUrl,
            quantity,
          });
          router.push("/cart");
        }}
        className="rounded-full bg-brand-accent px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-accent-hover disabled:opacity-50"
      >
        Add to Cart
      </button>
      <p className="text-xs text-brand-muted">Made-to-Order | Processing time varies by product</p>
    </div>
  );
}

function Row({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex justify-between text-brand-ink">
      <dt className="text-brand-muted">{label}</dt>
      <dd>${value.toFixed(2)}</dd>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useCart } from "@/components/cart/CartProvider";

interface CountryOption {
  code: string;
  name: string;
}

interface Breakdown {
  subtotalUsd: number;
  shippingFeeUsd: number;
  handlingFeeUsd: number;
  customsEstimateUsd: number;
  discountUsd: number;
  totalAmountUsd: number;
}

export function CheckoutForm({ countries }: { countries: CountryOption[] }) {
  const router = useRouter();
  const { items, clear } = useCart();

  const [countryCode, setCountryCode] = useState(countries[0]?.code ?? "US");
  const [discountCode, setDiscountCode] = useState("");
  const [breakdown, setBreakdown] = useState<Breakdown | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<"MPESA" | "BANK_TRANSFER">("MPESA");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (items.length === 0) return;
    fetch("/api/checkout/summary", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        items: items.map((i) => ({ productId: i.productId, variantId: i.variantId, quantity: i.quantity })),
        countryCode,
        discountCode: discountCode || undefined,
      }),
    })
      .then(async (res) => {
        if (!res.ok) throw new Error((await res.json()).error ?? "Failed to calculate total");
        return res.json();
      })
      .then(setBreakdown)
      .catch((err) => setError(err.message));
  }, [items, countryCode, discountCode]);

  async function handleSubmit(formData: FormData) {
    setSubmitting(true);
    setError(null);

    try {
      const res = await fetch("/api/orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: items.map((i) => ({ productId: i.productId, variantId: i.variantId, quantity: i.quantity })),
          shippingAddress: {
            fullName: formData.get("fullName"),
            line1: formData.get("line1"),
            line2: formData.get("line2") || undefined,
            city: formData.get("city"),
            countryCode,
            postalCode: formData.get("postalCode") || undefined,
            phone: formData.get("phone"),
          },
          discountCode: discountCode || undefined,
          paymentMethod,
          mpesaPhone: paymentMethod === "MPESA" ? formData.get("mpesaPhone") : undefined,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(JSON.stringify(data.error) ?? "Checkout failed");

      clear();
      router.push(`/checkout/confirmation/${data.orderNumber}`);
    } catch (err) {
      setError((err as Error).message);
      setSubmitting(false);
    }
  }

  if (items.length === 0) {
    return <p className="text-sm text-brand-muted">Your cart is empty.</p>;
  }

  return (
    <form action={handleSubmit} className="grid grid-cols-1 gap-8 md:grid-cols-2">
      <div className="flex flex-col gap-3 text-sm text-brand-ink">
        <h2 className="text-lg font-semibold">Shipping Address</h2>
        <input name="fullName" placeholder="Full name" required className="rounded border border-brand-border bg-brand-surface px-3 py-2" />
        <input name="line1" placeholder="Address line 1" required className="rounded border border-brand-border bg-brand-surface px-3 py-2" />
        <input name="line2" placeholder="Address line 2 (optional)" className="rounded border border-brand-border bg-brand-surface px-3 py-2" />
        <input name="city" placeholder="City" required className="rounded border border-brand-border bg-brand-surface px-3 py-2" />
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
        <input name="postalCode" placeholder="Postal code (optional)" className="rounded border border-brand-border bg-brand-surface px-3 py-2" />
        <input name="phone" placeholder="Contact phone" required className="rounded border border-brand-border bg-brand-surface px-3 py-2" />

        <h2 className="mt-4 text-lg font-semibold">Payment Method</h2>
        <label className="flex items-center gap-2">
          <input
            type="radio"
            checked={paymentMethod === "MPESA"}
            onChange={() => setPaymentMethod("MPESA")}
          />
          M-Pesa
        </label>
        {paymentMethod === "MPESA" && (
          <input
            name="mpesaPhone"
            placeholder="M-Pesa phone (2547XXXXXXXX)"
            required
            className="rounded border border-brand-border bg-brand-surface px-3 py-2"
          />
        )}
        <label className="flex items-center gap-2">
          <input
            type="radio"
            checked={paymentMethod === "BANK_TRANSFER"}
            onChange={() => setPaymentMethod("BANK_TRANSFER")}
          />
          Bank Transfer
        </label>

        <input
          type="text"
          value={discountCode}
          onChange={(e) => setDiscountCode(e.target.value)}
          placeholder="Discount code"
          className="mt-4 rounded border border-brand-border bg-brand-surface px-3 py-2"
        />
      </div>

      <div className="rounded-lg border border-brand-border bg-brand-surface p-5">
        <h2 className="text-lg font-semibold text-brand-ink">Order Summary</h2>
        <ul className="mt-3 flex flex-col gap-2 text-sm text-brand-ink">
          {items.map((item) => (
            <li key={`${item.productId}-${item.variantId ?? ""}`} className="flex justify-between">
              <span>
                {item.quantity}x {item.name} {item.variantLabel ? `(${item.variantLabel})` : ""}
              </span>
              <span>${(item.unitPriceUsd * item.quantity).toFixed(2)}</span>
            </li>
          ))}
        </ul>

        {breakdown && (
          <dl className="mt-4 flex flex-col gap-1 border-t border-brand-border pt-4 text-sm text-brand-ink">
            <Row label="Subtotal" value={breakdown.subtotalUsd} />
            <Row label="International Shipping" value={breakdown.shippingFeeUsd} />
            <Row label="Customs Estimate" value={breakdown.customsEstimateUsd} />
            {breakdown.discountUsd > 0 && <Row label="Discount" value={-breakdown.discountUsd} />}
            <div className="mt-2 flex justify-between border-t border-brand-border pt-2 text-base font-semibold">
              <dt>Total (USD)</dt>
              <dd className="text-brand-accent">${breakdown.totalAmountUsd.toFixed(2)}</dd>
            </div>
          </dl>
        )}

        {error && <p className="mt-3 text-sm text-brand-danger">{error}</p>}

        <button
          type="submit"
          disabled={submitting || !breakdown}
          className="mt-6 w-full rounded-full bg-brand-accent px-4 py-3 text-sm font-semibold text-white hover:bg-brand-accent-hover disabled:opacity-50"
        >
          {submitting ? "Placing order..." : "Place Order"}
        </button>
      </div>
    </form>
  );
}

function Row({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex justify-between">
      <dt className="text-brand-muted">{label}</dt>
      <dd>${value.toFixed(2)}</dd>
    </div>
  );
}

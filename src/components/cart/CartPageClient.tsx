"use client";

import Link from "next/link";
import Image from "next/image";
import { useCart } from "@/components/cart/CartProvider";

export function CartPageClient() {
  const { items, updateQuantity, removeItem } = useCart();
  const subtotal = items.reduce((sum, item) => sum + item.unitPriceUsd * item.quantity, 0);

  if (items.length === 0) {
    return (
      <p className="mt-6 text-sm text-brand-muted">
        Your cart is empty. <Link href="/products" className="text-brand-accent underline">Browse products</Link>.
      </p>
    );
  }

  return (
    <>
      <ul className="mt-6 flex flex-col gap-4">
        {items.map((item) => (
          <li
            key={`${item.productId}-${item.variantId ?? ""}`}
            className="flex items-center gap-4 rounded border border-brand-border bg-brand-surface p-4"
          >
            <div className="relative h-16 w-16 shrink-0 overflow-hidden rounded bg-brand-accent-soft">
              {item.imageUrl && (
                <Image src={item.imageUrl} alt={item.name} fill className="object-cover" />
              )}
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-brand-ink">{item.name}</p>
              {item.variantLabel && <p className="text-xs text-brand-muted">{item.variantLabel}</p>}
              <p className="text-sm text-brand-accent">${item.unitPriceUsd.toFixed(2)}</p>
            </div>
            <input
              type="number"
              min={1}
              max={50}
              value={item.quantity}
              onChange={(e) =>
                updateQuantity(item.productId, item.variantId, Math.max(1, Number(e.target.value)))
              }
              className="w-16 rounded border border-brand-border bg-brand-bg px-2 py-1 text-sm text-brand-ink"
            />
            <button
              type="button"
              onClick={() => removeItem(item.productId, item.variantId)}
              className="text-xs text-brand-danger"
            >
              Remove
            </button>
          </li>
        ))}
      </ul>

      <div className="mt-6 flex items-center justify-between border-t border-brand-border pt-4">
        <p className="text-sm text-brand-muted">Subtotal (before shipping/customs)</p>
        <p className="text-lg font-semibold text-brand-ink">${subtotal.toFixed(2)}</p>
      </div>

      <Link
        href="/checkout"
        className="mt-6 block w-full rounded-full bg-brand-accent px-4 py-3 text-center text-sm font-semibold text-white hover:bg-brand-accent-hover"
      >
        Proceed to Checkout
      </Link>
    </>
  );
}

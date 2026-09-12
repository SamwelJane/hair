"use client";

import Link from "next/link";
import { useCart } from "@/components/cart/CartProvider";

export function CartBadge() {
  const { items } = useCart();
  const count = items.reduce((sum, item) => sum + item.quantity, 0);

  return (
    <Link
      href="/cart"
      className="relative flex items-center gap-2 rounded-full bg-brand-ink px-3 py-2 text-xs font-medium text-brand-dark-ink"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="9" cy="21" r="1" />
        <circle cx="20" cy="21" r="1" />
        <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
      </svg>
      <span className="hidden sm:inline">Cart</span>
      {count > 0 && (
        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-brand-accent text-[11px] font-semibold text-white">
          {count}
        </span>
      )}
    </Link>
  );
}

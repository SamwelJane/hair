import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="bg-brand-dark px-6 py-10 text-sm text-brand-dark-ink">
      <div className="mx-auto grid max-w-6xl grid-cols-2 gap-8 sm:grid-cols-4">
        <div>
          <p className="text-base font-semibold">Hiar Business</p>
          <p className="mt-2 text-brand-dark-ink/70">
            Premium human hair extensions and wigs, sourced from Vietnam and shipped worldwide.
          </p>
        </div>
        <div>
          <p className="font-medium">Shop</p>
          <ul className="mt-2 flex flex-col gap-1 text-brand-dark-ink/70">
            <li><Link href="/products">All Products</Link></li>
            <li><Link href="/track">Track Order</Link></li>
          </ul>
        </div>
        <div>
          <p className="font-medium">Support</p>
          <ul className="mt-2 flex flex-col gap-1 text-brand-dark-ink/70">
            <li><Link href="/privacy">Privacy Policy</Link></li>
            <li>support@hiarbusiness.com</li>
          </ul>
        </div>
        <div>
          <p className="font-medium">We Accept</p>
          <ul className="mt-2 flex flex-col gap-1 text-brand-dark-ink/70">
            <li>M-Pesa</li>
            <li>Bank Transfer</li>
          </ul>
        </div>
      </div>
      <p className="mx-auto mt-8 max-w-6xl border-t border-white/10 pt-4 text-xs text-brand-dark-ink/50">
        &copy; {new Date().getFullYear()} Hiar Business. All rights reserved.
      </p>
    </footer>
  );
}

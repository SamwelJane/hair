import Link from "next/link";
import { auth, signOut } from "@/auth";
import { CartBadge } from "./CartBadge";

export async function SiteHeader() {
  const session = await auth();

  return (
    <header className="sticky top-0 z-10 bg-brand-surface">
      <div className="bg-brand-dark px-6 py-2 text-center text-xs text-brand-dark-ink">
        Free processing on orders over $150 &middot; Ships worldwide from Vietnam
      </div>

      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-4 border-b border-brand-border px-6 py-4">
        <Link href="/" className="flex items-center gap-2 text-lg font-semibold text-brand-ink">
          <span aria-hidden className="text-brand-accent">✦</span>
          Hiar Business
        </Link>

        <nav className="flex items-center gap-5 text-sm text-brand-ink">
          <Link href="/" className="hover:text-brand-accent">Home</Link>
          <Link href="/products" className="hover:text-brand-accent">Shop</Link>
          <Link href="/track" className="hover:text-brand-accent">Track Order</Link>
          <Link href="/privacy" className="hover:text-brand-accent">Privacy</Link>
        </nav>

        <form action="/products" method="get" className="order-last flex flex-1 basis-full sm:order-none sm:basis-auto sm:flex-1">
          <input
            type="text"
            name="q"
            placeholder="Search products..."
            className="w-full rounded-l-full border border-brand-border bg-brand-bg px-4 py-2 text-sm text-brand-ink placeholder:text-brand-muted focus:outline-none"
          />
          <button
            type="submit"
            aria-label="Search"
            className="rounded-r-full border border-l-0 border-brand-border bg-brand-surface px-3 text-brand-muted"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.35-4.35" />
            </svg>
          </button>
        </form>

        <div className="flex items-center gap-3">
          {session?.user ? (
            <>
              <Link href="/account" className="text-sm text-brand-ink hover:text-brand-accent">
                My Account
              </Link>
              <form
                action={async () => {
                  "use server";
                  await signOut({ redirectTo: "/" });
                }}
              >
                <button type="submit" className="text-sm text-brand-muted hover:text-brand-accent">
                  Sign out
                </button>
              </form>
            </>
          ) : (
            <Link href="/login" className="text-sm text-brand-ink hover:text-brand-accent">
              Sign in
            </Link>
          )}
          <CartBadge />
        </div>
      </div>
    </header>
  );
}

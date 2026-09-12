import { SiteHeader } from "@/components/storefront/SiteHeader";
import { SiteFooter } from "@/components/storefront/SiteFooter";
import { CartPageClient } from "@/components/cart/CartPageClient";

export default function CartPage() {
  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-3xl flex-1 px-6 py-10">
        <h1 className="text-2xl font-semibold text-brand-ink">Your Cart</h1>
        <CartPageClient />
      </main>
      <SiteFooter />
    </>
  );
}

import { SiteHeader } from "@/components/storefront/SiteHeader";
import { SiteFooter } from "@/components/storefront/SiteFooter";
import { CheckoutForm } from "@/components/checkout/CheckoutForm";
import { db } from "@/lib/db";

export default async function CheckoutPage() {
  const shippingRules = await db.countryShippingRule.findMany({ orderBy: { countryName: "asc" } });

  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-4xl flex-1 px-6 py-10">
        <h1 className="mb-8 text-2xl font-semibold text-brand-ink">Checkout</h1>
        <CheckoutForm countries={shippingRules.map((r) => ({ code: r.countryCode, name: r.countryName }))} />
      </main>
      <SiteFooter />
    </>
  );
}

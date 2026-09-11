import Link from "next/link";
import { auth } from "@/auth";
import { SiteHeader } from "@/components/storefront/SiteHeader";
import { SiteFooter } from "@/components/storefront/SiteFooter";

export default async function AccountPage() {
  const session = await auth();

  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-2xl flex-1 px-6 py-10">
        <h1 className="text-2xl font-semibold text-brand-ink">My Account</h1>
        <p className="mt-2 text-sm text-brand-muted">
          Signed in as {session?.user?.email}
        </p>

        <Link
          href="/account/orders"
          className="mt-6 inline-block rounded-full border border-brand-border bg-brand-surface px-5 py-2 text-sm font-medium text-brand-ink hover:border-brand-accent hover:text-brand-accent"
        >
          View Order History &rarr;
        </Link>
      </main>
      <SiteFooter />
    </>
  );
}

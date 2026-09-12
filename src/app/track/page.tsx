import { SiteHeader } from "@/components/storefront/SiteHeader";
import { SiteFooter } from "@/components/storefront/SiteFooter";
import { redirect } from "next/navigation";

async function goToTracking(formData: FormData) {
  "use server";
  const trackingNumber = (formData.get("trackingNumber") as string).trim();
  if (trackingNumber) redirect(`/track/${encodeURIComponent(trackingNumber)}`);
}

export default function TrackLandingPage() {
  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-md flex-1 px-6 py-16">
        <h1 className="text-2xl font-semibold text-brand-ink">Track Your Order</h1>
        <form action={goToTracking} className="mt-6 flex flex-col gap-3 text-sm">
          <input
            name="trackingNumber"
            placeholder="e.g. HB-20260906-AB3XZ"
            required
            className="rounded border border-brand-border bg-brand-surface px-3 py-2 text-brand-ink"
          />
          <button type="submit" className="rounded-full bg-brand-accent px-4 py-2 font-semibold text-white hover:bg-brand-accent-hover">
            Track
          </button>
        </form>
      </main>
      <SiteFooter />
    </>
  );
}

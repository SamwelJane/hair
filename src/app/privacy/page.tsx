import { SiteHeader } from "@/components/storefront/SiteHeader";
import { SiteFooter } from "@/components/storefront/SiteFooter";

export default function PrivacyPage() {
  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-2xl flex-1 px-6 py-10 text-sm leading-relaxed text-brand-muted">
        <h1 className="text-2xl font-semibold text-brand-ink">Data Privacy Notice</h1>

        <h2 className="mt-6 text-lg font-semibold text-brand-ink">What we collect</h2>
        <p className="mt-2">
          Your name, email, and password (stored as a secure hash, never in plain text) to run your
          account; your shipping address and phone number to deliver orders and prepare customs
          declarations; your order and payment history to fulfil orders and provide support. If you
          pay by M-Pesa, your phone number is passed to Safaricom to initiate the payment prompt and
          is not stored beyond the payment record&apos;s reference.
        </p>

        <h2 className="mt-6 text-lg font-semibold text-brand-ink">Who we share it with</h2>
        <p className="mt-2">
          Safaricom (to process M-Pesa payments), Cloudinary (product images only, no personal data),
          and Resend/Twilio (to notify our suppliers by email/WhatsApp when an order needs to be
          produced). Suppliers only ever see what product, variant, and quantity to produce - never
          your name, address, or contact details.
        </p>

        <h2 className="mt-6 text-lg font-semibold text-brand-ink">How long we keep it</h2>
        <p className="mt-2">
          For as long as your account is active, plus a reasonable period afterward for accounting
          and tax records.
        </p>

        <h2 className="mt-6 text-lg font-semibold text-brand-ink">Your rights</h2>
        <p className="mt-2">
          You can request a copy of your data, ask us to correct inaccurate information, or request
          deletion of your account (subject to retaining records required for tax/accounting
          compliance) by contacting support.
        </p>
      </main>
      <SiteFooter />
    </>
  );
}

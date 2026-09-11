const STEPS = [
  { label: "Order Received", icon: "🛒" },
  { label: "Payment Confirmed", icon: "▣" },
  { label: "Processing", icon: "▰" },
  { label: "In Warehouse", icon: "▤" },
  { label: "Shipping", icon: "◫" },
  { label: "Out for Delivery", icon: "▣" },
];

export function ProcessSteps() {
  return (
    <div className="flex flex-wrap items-center justify-between gap-6 border-y border-brand-border bg-brand-surface px-6 py-8" style={{ backgroundImage: "url(https://hebbkx1anhila5yf.public.blob.vercel-storage.com/tr-wvCMgyf50xiYsS7mzsVDFrnJWi3SGR.jpeg)", backgroundSize: "cover", backgroundPosition: "center", backgroundBlendMode: "soft-light" }}>
      {STEPS.map((step, i) => (
        <div key={step.label} className="flex flex-1 min-w-[110px] flex-col items-center gap-2 text-center">
          <span className="flex h-14 w-14 items-center justify-center rounded-full bg-brand-accent-soft text-2xl text-brand-accent">
            {step.icon}
          </span>
          <p className="text-xs font-medium text-brand-ink">{step.label}</p>
          {i < STEPS.length - 1 && <span className="hidden text-brand-border sm:block" aria-hidden />}
        </div>
      ))}
    </div>
  );
}

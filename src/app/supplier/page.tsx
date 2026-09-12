import Link from "next/link";
import { db } from "@/lib/db";
import { requireSupplierSession } from "@/lib/auth/require-supplier";

export default async function SupplierDashboardPage() {
  const session = await requireSupplierSession();
  const supplier = session.user.email
    ? await db.supplier.findFirst({ where: { email: session.user.email } })
    : null;

  if (!supplier) {
    return (
      <main className="min-h-screen bg-brand-bg px-6 py-12 text-brand-ink">
        <div className="mx-auto max-w-3xl rounded-3xl border border-brand-border bg-brand-surface p-8 shadow-sm">
          <p className="text-sm uppercase tracking-[0.2em] text-brand-muted">Supplier onboarding</p>
          <h1 className="mt-3 font-serif text-4xl">Your supplier account is pending setup.</h1>
          <p className="mt-4 max-w-xl leading-7 text-brand-muted">An administrator needs to link your account to a supplier profile before you can manage products and process orders.</p>
          <Link href="/" className="mt-6 inline-flex rounded-full bg-brand-accent px-5 py-3 text-sm font-semibold text-white">Return to storefront</Link>
        </div>
      </main>
    );
  }

  const [products, supplierOrders] = await Promise.all([
    db.product.findMany({ where: { supplierId: supplier.id }, include: { category: true }, orderBy: { updatedAt: "desc" } }),
    db.supplierOrder.findMany({ where: { supplierId: supplier.id }, include: { order: { include: { user: true, items: { include: { product: true, variant: true } } } } }, orderBy: { sentAt: "desc" } }),
  ]);

  return (
    <main className="min-h-screen bg-brand-bg px-4 py-8 text-brand-ink sm:px-8">
      <div className="mx-auto max-w-6xl">
        <header className="flex flex-col gap-5 border-b border-brand-border pb-8 sm:flex-row sm:items-end sm:justify-between">
          <div><p className="text-sm uppercase tracking-[0.2em] text-brand-muted">Supplier workspace</p><h1 className="mt-2 font-serif text-4xl">{supplier.name}</h1><p className="mt-2 text-brand-muted">{supplier.country} · {supplier.email}</p></div>
          <Link href="/" className="text-sm font-semibold text-brand-accent">View storefront →</Link>
        </header>
        <section className="mt-8 grid gap-4 sm:grid-cols-3">
          {[{ label: "Products", value: products.length }, { label: "Incoming orders", value: supplierOrders.length }, { label: "Account status", value: supplier.status }].map((stat) => <div key={stat.label} className="rounded-2xl border border-brand-border bg-brand-surface p-5"><p className="text-sm text-brand-muted">{stat.label}</p><p className="mt-2 text-2xl font-semibold capitalize">{stat.value}</p></div>)}
        </section>
        <div className="mt-8 grid gap-8 lg:grid-cols-[1fr_1.2fr]">
          <section className="rounded-2xl border border-brand-border bg-brand-surface p-6"><div className="flex items-center justify-between"><h2 className="font-serif text-2xl">Your products</h2><span className="text-sm text-brand-muted">{products.length} listings</span></div><div className="mt-5 flex flex-col divide-y divide-brand-border">{products.map((product) => <div key={product.id} className="flex items-center justify-between gap-4 py-4"><div><p className="font-medium">{product.name}</p><p className="text-sm text-brand-muted">{product.category.name} · {product.status}</p></div><p className="font-semibold">${product.basePriceUsd.toString()}</p></div>)}{products.length === 0 && <p className="py-6 text-sm text-brand-muted">No products have been assigned yet.</p>}</div></section>
          <section className="rounded-2xl border border-brand-border bg-brand-surface p-6"><div className="flex items-center justify-between"><h2 className="font-serif text-2xl">Incoming orders</h2><span className="text-sm text-brand-muted">Process in sequence</span></div><div className="mt-5 flex flex-col gap-4">{supplierOrders.map((supplierOrder) => <article key={supplierOrder.id} className="rounded-xl border border-brand-border p-4"><div className="flex items-center justify-between gap-3"><div><p className="font-semibold">{supplierOrder.order.orderNumber}</p><p className="text-sm text-brand-muted">{supplierOrder.order.user.name} · {supplierOrder.order.items.length} items</p></div><span className="rounded-full bg-brand-accent-soft px-3 py-1 text-xs font-semibold text-brand-accent">{supplierOrder.status.replaceAll("_", " ")}</span></div><p className="mt-3 text-sm text-brand-muted">{supplierOrder.order.items.map((item) => `${item.quantity}× ${item.product.name}`).join(", ")}</p></article>)}{supplierOrders.length === 0 && <p className="py-6 text-sm text-brand-muted">No approved orders are waiting for you.</p>}</div></section>
        </div>
      </div>
    </main>
  );
}

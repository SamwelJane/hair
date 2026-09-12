import Link from "next/link";
import { auth } from "@/auth";

const QUICK_LINKS = [
  { href: "/admin/orders", label: "Orders", desc: "Review and update order status" },
  { href: "/admin/products", label: "Products", desc: "Manage the catalog" },
  { href: "/admin/suppliers", label: "Suppliers", desc: "Performance and pending work" },
  { href: "/admin/payments", label: "Payments", desc: "Confirm bank transfers" },
  { href: "/admin/analytics", label: "Analytics", desc: "Revenue, operations, finance" },
  { href: "/admin/audit-logs", label: "Audit Logs", desc: "Security and accountability" },
];

export default async function AdminHomePage() {
  const session = await auth();

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold text-admin-ink">Admin Dashboard</h1>
      <p className="mt-2 text-sm text-admin-muted">
        Signed in as {session?.user?.email} ({session?.user?.role})
      </p>

      <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {QUICK_LINKS.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="rounded border border-admin-border bg-admin-surface p-4 hover:border-admin-accent"
          >
            <p className="font-medium text-admin-ink">{link.label}</p>
            <p className="mt-1 text-sm text-admin-muted">{link.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}

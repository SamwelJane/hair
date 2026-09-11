import Link from "next/link";
import { auth, signOut } from "@/auth";

const LINKS = [
  { href: "/admin", label: "Dashboard" },
  { href: "/admin/products", label: "Products" },
  { href: "/admin/suppliers", label: "Suppliers" },
  { href: "/admin/orders", label: "Orders" },
  { href: "/admin/payments", label: "Payments" },
  { href: "/admin/analytics", label: "Analytics" },
  { href: "/admin/audit-logs", label: "Audit Logs" },
  { href: "/admin/settings/exchange-rate", label: "Exchange Rate" },
];

export async function AdminNav() {
  const session = await auth();

  return (
    <div className="border-b border-admin-border bg-admin-surface">
      <div className="flex items-center justify-between px-6 py-3">
        <Link href="/admin" className="flex items-center gap-2 font-semibold text-admin-ink">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-admin-accent text-sm text-white">H</span>
          Hiar Business Admin
        </Link>
        <div className="flex items-center gap-3 text-sm text-admin-muted">
          <span>{session?.user?.email} ({session?.user?.role})</span>
          <form
            action={async () => {
              "use server";
              await signOut({ redirectTo: "/" });
            }}
          >
            <button type="submit" className="rounded border border-admin-border px-3 py-1 text-admin-ink hover:bg-admin-surface-2">
              Sign out
            </button>
          </form>
        </div>
      </div>
      <nav className="flex flex-wrap gap-1 px-6 pb-3 text-sm">
        {LINKS.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="rounded-full px-3 py-1.5 text-admin-muted hover:bg-admin-surface-2 hover:text-admin-ink"
          >
            {link.label}
          </Link>
        ))}
      </nav>
    </div>
  );
}

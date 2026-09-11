import Link from "next/link";
import { db } from "@/lib/db";
import { requireAdminSession } from "@/lib/auth/require-admin";
import { logAudit } from "@/lib/security/audit";
import { revalidatePath } from "next/cache";

async function createSupplier(formData: FormData) {
  "use server";
  const session = await requireAdminSession();

  const supplier = await db.supplier.create({
    data: {
      name: formData.get("name") as string,
      country: formData.get("country") as string,
      email: formData.get("email") as string,
      whatsappNumber: formData.get("whatsappNumber") as string,
      defaultMarginPct: Number(formData.get("defaultMarginPct") ?? 0),
    },
  });

  await logAudit({
    userId: session.user.id,
    action: "CREATE_SUPPLIER",
    entityType: "Supplier",
    entityId: supplier.id,
    metadata: { name: supplier.name },
  });

  revalidatePath("/admin/suppliers");
}

export default async function AdminSuppliersPage() {
  await requireAdminSession();
  const suppliers = await db.supplier.findMany({
    orderBy: { createdAt: "desc" },
    include: { _count: { select: { products: true, supplierOrders: true } } },
  });

  return (
    <div className="mx-auto max-w-4xl p-6 text-admin-ink">
      <h1 className="text-2xl font-semibold">Suppliers</h1>

      <table className="mt-6 w-full text-left text-sm">
        <thead>
          <tr className="border-b border-admin-border text-admin-muted">
            <th className="py-2">Name</th>
            <th>Country</th>
            <th>Margin</th>
            <th>Products</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {suppliers.map((s) => (
            <tr key={s.id} className="border-b border-admin-border/60">
              <td className="py-2">
                <Link href={`/admin/suppliers/${s.id}`} className="text-admin-accent underline">
                  {s.name}
                </Link>
              </td>
              <td>{s.country}</td>
              <td>{s.defaultMarginPct.toString()}%</td>
              <td>{s._count.products}</td>
              <td>{s.status}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2 className="mt-10 text-lg font-semibold">Add Supplier</h2>
      <form action={createSupplier} className="mt-4 flex flex-col gap-3 text-sm">
        <input name="name" placeholder="Supplier name" required className="rounded border border-admin-border bg-admin-surface px-3 py-2 text-admin-ink" />
        <input name="country" placeholder="Country" required className="rounded border border-admin-border bg-admin-surface px-3 py-2 text-admin-ink" />
        <input name="email" type="email" placeholder="Email" required className="rounded border border-admin-border bg-admin-surface px-3 py-2 text-admin-ink" />
        <input
          name="whatsappNumber"
          placeholder="WhatsApp number (+84...)"
          required
          className="rounded border border-admin-border bg-admin-surface px-3 py-2 text-admin-ink"
        />
        <input
          name="defaultMarginPct"
          type="number"
          step="0.01"
          placeholder="Default margin %"
          className="rounded border border-admin-border bg-admin-surface px-3 py-2 text-admin-ink"
        />
        <button type="submit" className="rounded bg-admin-accent px-4 py-2 text-white hover:opacity-90">
          Add Supplier
        </button>
      </form>
    </div>
  );
}

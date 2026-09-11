import Link from "next/link";
import { db } from "@/lib/db";
import { requireAdminSession } from "@/lib/auth/require-admin";

export default async function AdminProductsPage() {
  await requireAdminSession();
  const products = await db.product.findMany({
    include: { supplier: true, category: true },
    orderBy: { createdAt: "desc" },
  });

  return (
    <div className="mx-auto max-w-5xl p-6 text-admin-ink">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Products</h1>
        <Link href="/admin/products/new" className="rounded bg-admin-accent px-4 py-2 text-sm text-white hover:opacity-90">
          New Product
        </Link>
      </div>

      <table className="mt-6 w-full text-left text-sm">
        <thead>
          <tr className="border-b border-admin-border text-admin-muted">
            <th className="py-2">Name</th>
            <th>Category</th>
            <th>Supplier</th>
            <th>Price (USD)</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {products.map((p) => (
            <tr key={p.id} className="border-b border-admin-border/60">
              <td className="py-2">{p.name}</td>
              <td>{p.category.name}</td>
              <td>{p.supplier.name}</td>
              <td>${p.basePriceUsd.toString()}</td>
              <td>{p.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

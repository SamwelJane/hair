import { redirect } from "next/navigation";
import { db } from "@/lib/db";
import { requireAdminSession } from "@/lib/auth/require-admin";
import { logAudit } from "@/lib/security/audit";

function slugify(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

async function createProduct(formData: FormData) {
  "use server";
  const session = await requireAdminSession();

  const name = formData.get("name") as string;

  const product = await db.product.create({
    data: {
      name,
      slug: slugify(name),
      categoryId: formData.get("categoryId") as string,
      supplierId: formData.get("supplierId") as string,
      description: formData.get("description") as string,
      countryOfOrigin: formData.get("countryOfOrigin") as string,
      processingTimeDays: Number(formData.get("processingTimeDays") ?? 7),
      basePriceUsd: Number(formData.get("basePriceUsd")),
      baseWeightGrams: Number(formData.get("baseWeightGrams") ?? 200),
      status: "published",
    },
  });

  await logAudit({
    userId: session.user.id,
    action: "CREATE_PRODUCT",
    entityType: "Product",
    entityId: product.id,
    metadata: { name: product.name },
  });

  redirect("/admin/products");
}

export default async function NewProductPage() {
  await requireAdminSession();
  const [categories, suppliers] = await Promise.all([
    db.category.findMany({ orderBy: { name: "asc" } }),
    db.supplier.findMany({ orderBy: { name: "asc" } }),
  ]);

  const fieldClass = "rounded border border-admin-border bg-admin-surface px-3 py-2 text-admin-ink";

  return (
    <div className="mx-auto max-w-2xl p-6 text-admin-ink">
      <h1 className="text-2xl font-semibold">New Product</h1>
      <form action={createProduct} className="mt-6 flex flex-col gap-3 text-sm">
        <input name="name" placeholder="Product name" required className={fieldClass} />
        <textarea name="description" placeholder="Description" required className={fieldClass} />
        <select name="categoryId" required className={fieldClass}>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <select name="supplierId" required className={fieldClass}>
          {suppliers.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
        <input name="countryOfOrigin" placeholder="Country of origin" required className={fieldClass} />
        <input
          name="processingTimeDays"
          type="number"
          placeholder="Processing time (days)"
          defaultValue={7}
          className={fieldClass}
        />
        <input
          name="basePriceUsd"
          type="number"
          step="0.01"
          placeholder="Base price (USD)"
          required
          className={fieldClass}
        />
        <input
          name="baseWeightGrams"
          type="number"
          placeholder="Base weight (grams)"
          defaultValue={200}
          className={fieldClass}
        />
        <button type="submit" className="rounded bg-admin-accent px-4 py-2 text-white hover:opacity-90">
          Create Product
        </button>
      </form>
      <p className="mt-4 text-xs text-admin-muted">
        Variants and images can be added after creation (coming in a later phase).
      </p>
    </div>
  );
}

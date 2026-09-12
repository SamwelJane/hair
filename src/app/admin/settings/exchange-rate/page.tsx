import { db } from "@/lib/db";
import { requireAdminSession } from "@/lib/auth/require-admin";
import { revalidatePath } from "next/cache";

async function updateRate(formData: FormData) {
  "use server";
  const session = await requireAdminSession();

  const rate = Number(formData.get("rate"));

  const existing = await db.exchangeRate.findUnique({
    where: { baseCurrency_targetCurrency: { baseCurrency: "USD", targetCurrency: "KES" } },
  });

  await db.exchangeRate.upsert({
    where: { baseCurrency_targetCurrency: { baseCurrency: "USD", targetCurrency: "KES" } },
    update: { rate, updatedById: session.user.id },
    create: { baseCurrency: "USD", targetCurrency: "KES", rate, updatedById: session.user.id },
  });

  await db.auditLog.create({
    data: {
      userId: session.user.id,
      action: "UPDATE_EXCHANGE_RATE",
      entityType: "ExchangeRate",
      entityId: "USD_KES",
      metadata: { from: existing?.rate.toString() ?? null, to: rate },
    },
  });

  revalidatePath("/admin/settings/exchange-rate");
}

export default async function ExchangeRateSettingsPage() {
  await requireAdminSession();
  const rate = await db.exchangeRate.findUnique({
    where: { baseCurrency_targetCurrency: { baseCurrency: "USD", targetCurrency: "KES" } },
    include: { updatedBy: true },
  });

  return (
    <div className="mx-auto max-w-lg p-6 text-admin-ink">
      <h1 className="text-2xl font-semibold">USD → KES Exchange Rate</h1>
      <p className="mt-2 text-sm text-admin-muted">
        Customers are charged this rate at checkout for M-Pesa and bank transfer, regardless of
        the real market rate. There is no live FX API — you set it manually here.
      </p>

      {rate && (
        <p className="mt-4 text-sm">
          Current rate: <strong>1 USD = {rate.rate.toString()} KES</strong>
          <br />
          <span className="text-admin-muted">Last updated by {rate.updatedBy.name} on {rate.updatedAt.toLocaleString()}</span>
        </p>
      )}

      <form action={updateRate} className="mt-6 flex flex-col gap-3 text-sm">
        <label className="flex flex-col gap-1">
          New rate (1 USD = ? KES)
          <input
            name="rate"
            type="number"
            step="0.01"
            min="0"
            defaultValue={rate?.rate.toString()}
            required
            className="rounded border border-admin-border bg-admin-surface px-3 py-2 text-admin-ink"
          />
        </label>
        <button type="submit" className="rounded bg-admin-accent px-4 py-2 text-white hover:opacity-90">
          Update Rate
        </button>
      </form>
    </div>
  );
}

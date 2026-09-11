import { config as loadEnv } from "dotenv";
loadEnv({ path: ".env.local" });
loadEnv({ path: ".env" });

import { PrismaClient } from "../src/generated/prisma/client";
import { PrismaPg } from "@prisma/adapter-pg";
import bcrypt from "bcryptjs";

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL });
const db = new PrismaClient({ adapter });

async function main() {
  const passwordHash = await bcrypt.hash("password123", 10);

  const admin = await db.user.upsert({
    where: { email: "admin@hiarbusiness.com" },
    update: {},
    create: {
      email: "admin@hiarbusiness.com",
      passwordHash,
      name: "Admin User",
      role: "ADMIN",
    },
  });

  await db.user.upsert({
    where: { email: "staff@hiarbusiness.com" },
    update: {},
    create: {
      email: "staff@hiarbusiness.com",
      passwordHash,
      name: "Staff User",
      role: "STAFF",
    },
  });

  const customer = await db.user.upsert({
    where: { email: "customer@example.com" },
    update: {},
    create: {
      email: "customer@example.com",
      passwordHash,
      name: "Demo Customer",
      role: "CUSTOMER",
    },
  });

  const supplierA = await db.supplier.upsert({
    where: { id: "seed-supplier-a" },
    update: {},
    create: {
      id: "seed-supplier-a",
      name: "Golden Hair Vietnam Co.",
      country: "Vietnam",
      email: "orders@goldenhairvn.example.com",
      whatsappNumber: "+84900000001",
      defaultMarginPct: 30,
    },
  });

  const supplierB = await db.supplier.upsert({
    where: { id: "seed-supplier-b" },
    update: {},
    create: {
      id: "seed-supplier-b",
      name: "Lotus Tresses Ltd.",
      country: "Vietnam",
      email: "orders@lotustresses.example.com",
      whatsappNumber: "+84900000002",
      defaultMarginPct: 35,
    },
  });

  const wigsCategory = await db.category.upsert({
    where: { slug: "wigs" },
    update: {},
    create: { name: "Wigs", slug: "wigs" },
  });

  const bundlesCategory = await db.category.upsert({
    where: { slug: "bundles" },
    update: {},
    create: { name: "Hair Bundles", slug: "bundles" },
  });

  const products = [
    {
      slug: "luxury-body-wave-wig",
      name: "Luxury Body Wave Human Hair Wig",
      categoryId: wigsCategory.id,
      supplierId: supplierA.id,
      description: "Premium body wave lace wig, 100% human hair.",
      countryOfOrigin: "Vietnam",
      basePriceUsd: 150,
      baseWeightGrams: 250,
      status: "published",
    },
    {
      slug: "indian-straight-bundle",
      name: "Indian Straight Hair Bundle",
      categoryId: bundlesCategory.id,
      supplierId: supplierB.id,
      description: "Silky straight bundle, single donor.",
      countryOfOrigin: "Vietnam",
      basePriceUsd: 50,
      baseWeightGrams: 100,
      status: "published",
    },
    {
      slug: "deep-wave-bundle",
      name: "Deep Wave Bundle",
      categoryId: bundlesCategory.id,
      supplierId: supplierA.id,
      description: "Bouncy deep wave texture bundle.",
      countryOfOrigin: "Vietnam",
      basePriceUsd: 65,
      baseWeightGrams: 100,
      status: "published",
    },
  ];

  for (const p of products) {
    const product = await db.product.upsert({
      where: { slug: p.slug },
      update: {},
      create: p,
    });

    await db.productVariant.upsert({
      where: { sku: `${p.slug}-24IN` },
      update: {},
      create: {
        productId: product.id,
        sku: `${p.slug}-24IN`,
        length: "24 inches",
        density: "180%",
        color: "Natural Black",
        priceDeltaUsd: 0,
        stockQty: 20,
      },
    });
  }

  await db.discountCode.upsert({
    where: { code: "WELCOME10" },
    update: {},
    create: {
      code: "WELCOME10",
      type: "percent",
      value: 10,
      minOrderUsd: 50,
      usageLimit: 100,
      active: true,
    },
  });

  await db.countryShippingRule.upsert({
    where: { countryCode: "US" },
    update: {},
    create: {
      countryCode: "US",
      countryName: "United States",
      baseFeeUsd: 25,
      perKgFeeUsd: 10,
      customsRatePct: 5,
      estimatedDaysMin: 7,
      estimatedDaysMax: 14,
    },
  });

  await db.countryShippingRule.upsert({
    where: { countryCode: "KE" },
    update: {},
    create: {
      countryCode: "KE",
      countryName: "Kenya",
      baseFeeUsd: 10,
      perKgFeeUsd: 4,
      customsRatePct: 0,
      estimatedDaysMin: 3,
      estimatedDaysMax: 7,
    },
  });

  await db.exchangeRate.upsert({
    where: { baseCurrency_targetCurrency: { baseCurrency: "USD", targetCurrency: "KES" } },
    update: {},
    create: {
      baseCurrency: "USD",
      targetCurrency: "KES",
      rate: 129.5,
      updatedById: admin.id,
    },
  });

  const seededProduct = await db.product.findUniqueOrThrow({ where: { slug: "luxury-body-wave-wig" } });
  const seededVariant = await db.productVariant.findUniqueOrThrow({ where: { sku: "luxury-body-wave-wig-24IN" } });

  const order = await db.order.upsert({
    where: { orderNumber: "HB-DEMO-0001" },
    update: {},
    create: {
      orderNumber: "HB-DEMO-0001",
      userId: customer.id,
      status: "PAID",
      subtotalUsd: 150,
      shippingFeeUsd: 25,
      handlingFeeUsd: 0,
      customsEstimateUsd: 7.5,
      totalAmountUsd: 182.5,
      exchangeRateApplied: 129.5,
      totalAmountKes: 182.5 * 129.5,
      shippingCountry: "US",
      shippingAddress: { line1: "123 Demo St", city: "New York", country: "US" },
      items: {
        create: [
          {
            productId: seededProduct.id,
            variantId: seededVariant.id,
            quantity: 1,
            unitPriceUsdAtPurchase: 150,
            lineTotalUsd: 150,
          },
        ],
      },
      statusHistory: {
        create: [
          { toStatus: "PENDING_PAYMENT", note: "Order created" },
          { toStatus: "PAID", note: "Demo payment marked paid", changedById: admin.id },
        ],
      },
    },
  });

  console.log("Seed complete:", { admin: admin.email, order: order.orderNumber });
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await db.$disconnect();
  });

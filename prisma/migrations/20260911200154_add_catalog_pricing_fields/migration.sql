-- AlterTable
ALTER TABLE "products" ADD COLUMN     "accessoryType" TEXT,
ADD COLUMN     "color" TEXT,
ADD COLUMN     "hairLength" TEXT,
ADD COLUMN     "quality" TEXT,
ADD COLUMN     "texture" TEXT;

-- CreateTable
CREATE TABLE "pricing_settings" (
    "id" TEXT NOT NULL DEFAULT 'global',
    "commissionPct" DECIMAL(5,2) NOT NULL DEFAULT 10,
    "shippingPerKgUsd" DECIMAL(10,2) NOT NULL DEFAULT 60,
    "packagingFeeUsd" DECIMAL(10,2) NOT NULL DEFAULT 2,
    "kesAdjustment" DECIMAL(10,2) NOT NULL DEFAULT 4,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "pricing_settings_pkey" PRIMARY KEY ("id")
);

import { z } from "zod";

export const cartItemSchema = z.object({
  productId: z.string(),
  variantId: z.string().optional(),
  quantity: z.number().int().min(1).max(50),
});

export const shippingAddressSchema = z.object({
  fullName: z.string().min(1),
  line1: z.string().min(1),
  line2: z.string().optional(),
  city: z.string().min(1),
  countryCode: z.string().length(2),
  postalCode: z.string().optional(),
  phone: z.string().min(7),
});

export const checkoutSchema = z.object({
  items: z.array(cartItemSchema).min(1),
  shippingAddress: shippingAddressSchema,
  discountCode: z.string().optional(),
  paymentMethod: z.enum(["MPESA", "BANK_TRANSFER"]),
  mpesaPhone: z.string().optional(),
});

export type CheckoutInput = z.infer<typeof checkoutSchema>;

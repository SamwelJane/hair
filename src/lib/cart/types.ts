export interface CartItem {
  productId: string;
  variantId?: string;
  slug: string;
  name: string;
  variantLabel?: string;
  unitPriceUsd: number;
  imageUrl?: string;
  quantity: number;
}

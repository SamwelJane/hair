import * as SecureStore from "expo-secure-store";

// Mirrors frontend/src/lib/cart/guestCartToken.ts - the server mints/echoes
// this token via the X-Guest-Cart-Token response header (see
// backend/app/routers/cart.py::_resolve_cart) so an anonymous shopper's
// cart survives an app restart.
const GUEST_CART_TOKEN_KEY = "hiar_guest_cart_token";

export async function getGuestCartToken(): Promise<string | null> {
  return SecureStore.getItemAsync(GUEST_CART_TOKEN_KEY);
}

export async function setGuestCartToken(token: string | null): Promise<void> {
  if (token) await SecureStore.setItemAsync(GUEST_CART_TOKEN_KEY, token);
  else await SecureStore.deleteItemAsync(GUEST_CART_TOKEN_KEY);
}

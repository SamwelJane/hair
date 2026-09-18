// Mirrors the refresh-token storage pattern in lib/auth/tokenStore.ts - the
// server mints/echoes this token via the X-Guest-Cart-Token response header
// (see backend/app/routers/cart.py::_resolve_cart) so an anonymous
// shopper's cart survives a page reload.
const GUEST_CART_TOKEN_KEY = "hiar_guest_cart_token";

export function getGuestCartToken(): string | null {
  try {
    return localStorage.getItem(GUEST_CART_TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setGuestCartToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(GUEST_CART_TOKEN_KEY, token);
    else localStorage.removeItem(GUEST_CART_TOKEN_KEY);
  } catch {
    // ignore - cart just won't persist across reloads in this browser
  }
}

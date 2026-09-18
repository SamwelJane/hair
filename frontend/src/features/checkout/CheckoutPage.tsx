import { useState } from "react";
import { useNavigate } from "react-router";
import { useAuth } from "../../lib/auth/AuthContext";
import { useCart, useClearCart } from "../cart/hooks";
import { setGuestCartToken } from "../../lib/cart/guestCartToken";
import { useCheckoutSummary, useSubmitCheckout } from "./hooks";

export function CheckoutPage() {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const { data: cart } = useCart();
  const submit = useSubmitCheckout();
  const clearCart = useClearCart();

  const [fullName, setFullName] = useState(user?.name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [line1, setLine1] = useState("");
  const [line2, setLine2] = useState("");
  const [city, setCity] = useState("");
  const [countryCode, setCountryCode] = useState("KE");
  const [postalCode, setPostalCode] = useState("");
  const [phone, setPhone] = useState("");
  const [discountCode, setDiscountCode] = useState("");
  const [paymentMethod, setPaymentMethod] = useState<"MPESA" | "BANK_TRANSFER">("BANK_TRANSFER");
  const [mpesaPhone, setMpesaPhone] = useState("");

  const items = (cart?.items ?? []).map((i) => ({ product_id: i.product_id, variant_id: i.variant_id, quantity: i.quantity }));
  const summary = useCheckoutSummary(items, countryCode, discountCode);

  if (!cart || cart.items.length === 0) {
    return <div className="page">Your cart is empty.</div>;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const result = await submit.mutateAsync({
        items,
        shipping_address: {
          full_name: fullName,
          email: isAuthenticated ? undefined : email,
          line1,
          line2: line2 || undefined,
          city,
          country_code: countryCode,
          postal_code: postalCode || undefined,
          phone,
        },
        discount_code: discountCode || undefined,
        payment_method: paymentMethod,
        mpesa_phone: paymentMethod === "MPESA" ? mpesaPhone : undefined,
      });
      await clearCart.mutateAsync().catch(() => undefined);
      setGuestCartToken(null);
      navigate(`/checkout/confirmation/${result.order_number}`, {
        state: { paymentInstructions: result.payment_instructions, guestAccessToken: result.guest_access_token },
      });
    } catch {
      // surfaced via submit.isError below
    }
  }

  return (
    <div className="page checkout">
      <h1>Checkout</h1>
      <form onSubmit={handleSubmit} className="checkout-form">
        <fieldset>
          <legend>Shipping details</legend>
          <label>Full name<input required value={fullName} onChange={(e) => setFullName(e.target.value)} /></label>
          {!isAuthenticated && (
            <label>Email<input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} /></label>
          )}
          <label>Address line 1<input required value={line1} onChange={(e) => setLine1(e.target.value)} /></label>
          <label>Address line 2<input value={line2} onChange={(e) => setLine2(e.target.value)} /></label>
          <label>City<input required value={city} onChange={(e) => setCity(e.target.value)} /></label>
          <label>Country code
            <input required maxLength={2} value={countryCode} onChange={(e) => setCountryCode(e.target.value.toUpperCase())} />
          </label>
          <label>Postal code<input value={postalCode} onChange={(e) => setPostalCode(e.target.value)} /></label>
          <label>Phone<input required value={phone} onChange={(e) => setPhone(e.target.value)} /></label>
        </fieldset>

        <fieldset>
          <legend>Payment</legend>
          <label>
            <input type="radio" checked={paymentMethod === "BANK_TRANSFER"} onChange={() => setPaymentMethod("BANK_TRANSFER")} />
            Bank transfer
          </label>
          <label>
            <input type="radio" checked={paymentMethod === "MPESA"} onChange={() => setPaymentMethod("MPESA")} />
            M-Pesa
          </label>
          {paymentMethod === "MPESA" && (
            <label>M-Pesa phone<input required value={mpesaPhone} onChange={(e) => setMpesaPhone(e.target.value)} /></label>
          )}
        </fieldset>

        <label>Discount code<input value={discountCode} onChange={(e) => setDiscountCode(e.target.value)} /></label>

        {summary.data && (
          <div className="checkout-summary">
            <p>Subtotal: ${summary.data.subtotal_usd}</p>
            <p>Shipping: ${summary.data.shipping_fee_usd}</p>
            <p>Handling: ${summary.data.handling_fee_usd}</p>
            <p>Customs estimate: ${summary.data.customs_estimate_usd}</p>
            {Number(summary.data.discount_usd) > 0 && <p>Discount: -${summary.data.discount_usd}</p>}
            <p className="total">Total: ${summary.data.total_amount_usd}</p>
          </div>
        )}
        {summary.isError && <p className="error">Could not price this order for that address yet.</p>}

        {submit.isError && <p className="error">Checkout failed. Please check your details and try again.</p>}

        <button type="submit" disabled={submit.isPending}>
          {submit.isPending ? "Placing order..." : "Place Order"}
        </button>
      </form>
    </div>
  );
}

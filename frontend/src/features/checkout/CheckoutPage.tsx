import { useState } from "react";
import { useNavigate } from "react-router";
import { useAuth } from "../../lib/auth/AuthContext";
import { useCart, useClearCart } from "../cart/hooks";
import { setGuestCartToken } from "../../lib/cart/guestCartToken";
import { useCheckoutSummary, useSubmitCheckout } from "./hooks";

function CopyButton({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      onClick={() => {
        void navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }}
      aria-label={`Copy ${label}`}
      style={{
        padding: "3px 10px",
        fontSize: "0.75rem",
        borderRadius: "4px",
        border: "1px solid var(--border)",
        background: copied ? "#e8f5e9" : "#ffffff",
        color: copied ? "#2e7d32" : "var(--ink)",
        fontWeight: 600,
        cursor: "pointer",
      }}
    >
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

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

  // Payment modal state
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState<"MPESA" | "BANK_TRANSFER">("MPESA");
  const [mpesaPhone, setMpesaPhone] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const items = (cart?.items ?? []).map((i) => ({ product_id: i.product_id, variant_id: i.variant_id, quantity: i.quantity }));
  const summary = useCheckoutSummary(items, countryCode, discountCode);

  if (!cart || cart.items.length === 0) {
    return <div className="page">Your cart is empty.</div>;
  }

  function handleOpenPayment(e: React.FormEvent) {
    e.preventDefault();
    if (!fullName.trim() || !line1.trim() || !city.trim() || !countryCode.trim() || !phone.trim() || (!isAuthenticated && !email.trim())) {
      setFormError("Please fill in all required shipping fields before proceeding to payment.");
      return;
    }
    setFormError(null);
    if (!mpesaPhone.trim()) {
      setMpesaPhone(phone);
    }
    setShowPaymentModal(true);
  }

  async function handleExecutePayment(selectedMethod: "MPESA" | "BANK_TRANSFER") {
    setSubmitError(null);
    if (selectedMethod === "MPESA" && !mpesaPhone.trim()) {
      setSubmitError("Please provide a valid M-Pesa phone number.");
      return;
    }

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
        payment_method: selectedMethod,
        mpesa_phone: selectedMethod === "MPESA" ? mpesaPhone : undefined,
      });

      await clearCart.mutateAsync().catch(() => undefined);
      setGuestCartToken(null);
      setShowPaymentModal(false);
      navigate(`/checkout/confirmation/${result.order_number}`, {
        state: { paymentInstructions: result.payment_instructions, guestAccessToken: result.guest_access_token },
      });
    } catch {
      setSubmitError("Payment processing failed. Please verify your details and try again.");
    }
  }

  const kesFormatted = summary.data?.total_amount_kes
    ? Number(summary.data.total_amount_kes).toLocaleString("en-KE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : null;

  return (
    <div className="page checkout">
      <h1>Checkout</h1>
      <form onSubmit={handleOpenPayment} className="checkout-form">
        <fieldset>
          <legend>Shipping Details</legend>
          <label>
            Full Name <span style={{ color: "var(--danger)" }}>*</span>
            <input required value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </label>
          {!isAuthenticated && (
            <label>
              Email Address <span style={{ color: "var(--danger)" }}>*</span>
              <input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            </label>
          )}
          <label>
            Address Line 1 <span style={{ color: "var(--danger)" }}>*</span>
            <input required value={line1} onChange={(e) => setLine1(e.target.value)} />
          </label>
          <label>
            Address Line 2 (Optional)
            <input value={line2} onChange={(e) => setLine2(e.target.value)} />
          </label>
          <label>
            City / Town <span style={{ color: "var(--danger)" }}>*</span>
            <input required value={city} onChange={(e) => setCity(e.target.value)} />
          </label>
          <label>
            Country Code <span style={{ color: "var(--danger)" }}>*</span>
            <input required maxLength={2} value={countryCode} onChange={(e) => setCountryCode(e.target.value.toUpperCase())} />
          </label>
          <label>
            Postal Code (Optional)
            <input value={postalCode} onChange={(e) => setPostalCode(e.target.value)} />
          </label>
          <label>
            Phone Number <span style={{ color: "var(--danger)" }}>*</span>
            <input required placeholder="e.g. 0712345678" value={phone} onChange={(e) => setPhone(e.target.value)} />
          </label>
        </fieldset>

        <label>
          Discount Code
          <input placeholder="Enter promo code" value={discountCode} onChange={(e) => setDiscountCode(e.target.value)} />
        </label>

        {summary.data && (
          <div className="checkout-summary">
            <h3>Order Breakdown</h3>
            <p>Subtotal: ${summary.data.subtotal_usd}</p>
            <p>Shipping: ${summary.data.shipping_fee_usd}</p>
            <p>Handling: ${summary.data.handling_fee_usd}</p>
            <p>Customs estimate: ${summary.data.customs_estimate_usd}</p>
            {Number(summary.data.discount_usd) > 0 && <p>Discount: -${summary.data.discount_usd}</p>}
            <div className="total" style={{ marginTop: "0.75rem", borderTop: "1px solid var(--border)", paddingTop: "0.75rem" }}>
              <div>Total USD: <strong>${summary.data.total_amount_usd}</strong></div>
              {kesFormatted && (
                <div style={{ color: "var(--accent)", fontSize: "1.2rem", marginTop: "0.25rem" }}>
                  Total KES: <strong>KES {kesFormatted}</strong>
                </div>
              )}
              {summary.data.effective_exchange_rate && (
                <small style={{ display: "block", color: "var(--muted)", marginTop: "0.25rem" }}>
                  Exchange Rate: 1 USD = KES {summary.data.effective_exchange_rate}
                </small>
              )}
            </div>
          </div>
        )}

        {summary.isError && <p className="error">Could not price this order for that address yet.</p>}
        {formError && <p className="error">{formError}</p>}

        <button type="submit" className="btn btn--primary" style={{ width: "100%", padding: "0.9rem", fontSize: "1rem", fontWeight: 700 }}>
          Proceed to Payment
        </button>
      </form>

      {/* ── Dedicated Checkout Payment Modal ───────────────────────────────── */}
      {showPaymentModal && (
        <div className="modal-overlay" onClick={() => setShowPaymentModal(false)}>
          <div
            className="modal-card"
            onClick={(e) => e.stopPropagation()}
            style={{ maxWidth: "540px", padding: "1.5rem" }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--border)", paddingBottom: "0.75rem" }}>
              <h2 style={{ fontSize: "1.25rem", margin: 0 }}>Select Payment Method</h2>
              <button
                type="button"
                onClick={() => setShowPaymentModal(false)}
                style={{ background: "none", border: "none", fontSize: "1.25rem", cursor: "pointer", color: "var(--muted)" }}
                style={{ background: "none", border: "none", fontSize: "1.25rem", cursor: "pointer", color: "var(--muted)", padding: "4px" }}
                aria-label="Close payment modal"
              >
                ✕
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
            </div>

            {/* Total Amount Banner */}
            <div style={{ background: "#f8f5f2", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border)", textAlign: "center" }}>
              <div style={{ fontSize: "0.75rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                Total Payable Amount
              </div>
              <div style={{ fontSize: "1.6rem", fontWeight: 700, color: "var(--ink)", margin: "0.25rem 0" }}>
                ${summary.data?.total_amount_usd}
              </div>
              {kesFormatted && (
                <div style={{ fontSize: "1.15rem", fontWeight: 700, color: "var(--accent)" }}>
                  KES {kesFormatted}
                </div>
              )}
              {summary.data?.effective_exchange_rate && (
                <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginTop: "0.25rem" }}>
                  Effective rate: 1 USD = KES {summary.data.effective_exchange_rate}
                </div>
              )}
            </div>

            {/* Method Tabs */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
              <button
                type="button"
                onClick={() => { setPaymentMethod("MPESA"); setSubmitError(null); }}
                style={{
                  padding: "0.75rem 0.5rem",
                  borderRadius: "6px",
                  border: paymentMethod === "MPESA" ? "2px solid #00a651" : "1px solid var(--border)",
                  background: paymentMethod === "MPESA" ? "#f0fdf4" : "var(--surface)",
                  color: paymentMethod === "MPESA" ? "#15803d" : "var(--ink)",
                  fontWeight: 700,
                  cursor: "pointer",
                  textAlign: "center",
                }}
              >
                M-Pesa STK Push
              </button>
              <button
                type="button"
                onClick={() => { setPaymentMethod("BANK_TRANSFER"); setSubmitError(null); }}
                style={{
                  padding: "0.75rem 0.5rem",
                  borderRadius: "6px",
                  border: paymentMethod === "BANK_TRANSFER" ? "2px solid #a32a29" : "1px solid var(--border)",
                  background: paymentMethod === "BANK_TRANSFER" ? "#fff5f5" : "var(--surface)",
                  color: paymentMethod === "BANK_TRANSFER" ? "#a32a29" : "var(--ink)",
                  fontWeight: 700,
                  cursor: "pointer",
                  textAlign: "center",
                }}
              >
                Equity Bank Paybill
              </button>
            </div>

            {/* Tab 1: M-Pesa STK Push */}
            {paymentMethod === "MPESA" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--muted)" }}>
                  An automated payment prompt will appear on your phone screen. Simply enter your M-Pesa PIN to complete checkout.
                </p>
                <label style={{ display: "flex", flexDirection: "column", gap: "0.25rem", fontSize: "0.85rem", fontWeight: 600 }}>
                  Safaricom Phone Number
                  <input
                    required
                    type="tel"
                    placeholder="e.g. 0712345678 or 254712345678"
                    value={mpesaPhone}
                    onChange={(e) => setMpesaPhone(e.target.value)}
                    style={{ padding: "0.6rem", borderRadius: "6px", border: "1px solid var(--border)", fontSize: "0.95rem" }}
                  />
                </label>
                <button
                  type="button"
                  disabled={submit.isPending}
                  onClick={() => handleExecutePayment("MPESA")}
                  style={{
                    background: "#00a651",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "6px",
                    padding: "0.85rem",
                    fontWeight: 700,
                    fontSize: "1rem",
                    cursor: submit.isPending ? "not-allowed" : "pointer",
                    marginTop: "0.5rem",
                  }}
                >
                  {submit.isPending ? "Sending STK Prompt..." : `Send Prompt for KES ${kesFormatted ?? ""}`}
                </button>
              </div>
            )}

            {/* Tab 2: Equity Bank Paybill */}
            {paymentMethod === "BANK_TRANSFER" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                <div style={{ background: "#fafafa", border: "1px solid var(--border)", borderRadius: "6px", padding: "0.85rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.4rem 0", borderBottom: "1px solid #eee" }}>
                    <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>Paybill Business Number:</span>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <strong>247247</strong>
                      <CopyButton text="247247" label="Paybill" />
                    </div>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.4rem 0", borderBottom: "1px solid #eee" }}>
                    <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>Account Number:</span>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <strong>0310173604563</strong>
                      <CopyButton text="0310173604563" label="Account" />
                    </div>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.4rem 0", borderBottom: "1px solid #eee" }}>
                    <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>Account Name:</span>
                    <strong>Cherubim Express Ltd</strong>
                  </div>
                  {kesFormatted && (
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.4rem 0" }}>
                      <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>Exact Amount:</span>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <strong style={{ color: "var(--accent)" }}>KES {kesFormatted}</strong>
                        <CopyButton text={String(summary.data?.total_amount_kes ?? "")} label="Amount" />
                      </div>
                    </div>
                  )}
                </div>

                <div style={{ fontSize: "0.8rem", color: "var(--muted)", lineHeight: 1.4 }}>
                  <strong>How to pay:</strong> Open M-Pesa &gt; Lipa na M-Pesa &gt; Pay Bill &gt; Enter Business No. <strong>247247</strong> &gt; Account <strong>0310173604563</strong> &gt; Enter Amount &gt; Enter PIN.
                </div>

                <button
                  type="button"
                  disabled={submit.isPending}
                  onClick={() => handleExecutePayment("BANK_TRANSFER")}
                  style={{
                    background: "#a32a29",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "6px",
                    padding: "0.85rem",
                    fontWeight: 700,
                    fontSize: "1rem",
                    cursor: submit.isPending ? "not-allowed" : "pointer",
                    marginTop: "0.5rem",
                  }}
                >
                  {submit.isPending ? "Placing Order..." : "I Have Completed Payment / Place Order"}
                </button>
              </div>
            )}

            {submitError && <p className="error" style={{ margin: 0 }}>{submitError}</p>}
          </div>
        </div>
      )}
    </div>
  );
}

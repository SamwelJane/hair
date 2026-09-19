import { Link, useLocation, useParams } from "react-router";
import { useOrder } from "../orders/hooks";
import { EquityBankPaymentCard } from "./EquityBankPaymentCard";

interface ConfirmationState {
  paymentInstructions?: Record<string, unknown>;
  guestAccessToken?: string | null;
}

export function ConfirmationPage() {
  const { orderNumber } = useParams<{ orderNumber: string }>();
  const location = useLocation();
  const state = (location.state ?? {}) as ConfirmationState;
  const { data: order } = useOrder(orderNumber, state.guestAccessToken ?? undefined);

  const isBankTransfer = state.paymentInstructions?.bankDetails != null;
  const amountKes = state.paymentInstructions?.amountKes as number | string | undefined;

  return (
    <div className="page confirmation-page">
      <div className="confirmation-page__hero">
        <span className="confirmation-page__tick" aria-hidden="true" style={{ display: "inline-flex", justifyContent: "center", alignItems: "center", width: "48px", height: "48px", borderRadius: "50%", background: "#e8f5e9", color: "#2e7d32", margin: "0 auto 1rem" }}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
        </span>
        <h1>Order Placed Successfully!</h1>
        <p className="confirmation-page__sub">
          Order number: <strong>{orderNumber}</strong>
        </p>
      </div>

      {/* ── Bank transfer / Equity Bank Paybill instructions ──────────────── */}
      {isBankTransfer && orderNumber && amountKes != null && (
        <section className="confirmation-page__payment">
          <EquityBankPaymentCard
            orderNumber={orderNumber}
            amountKes={amountKes}
            amountUsd={order?.total_amount_usd}
          />
        </section>
      )}

      {/* M-Pesa STK push message */}
      {typeof state.paymentInstructions?.message === "string" && !isBankTransfer && (
        <div className="callout callout--info">
          <p>{state.paymentInstructions.message}</p>
        </div>
      )}

      {/* Payment error */}
      {typeof state.paymentInstructions?.error === "string" && (
        <div className="callout callout--error">
          <p>{state.paymentInstructions.error}</p>
        </div>
      )}

      {/* ── Order summary ─────────────────────────────────────────────────── */}
      {order && (
        <div className="confirmation-page__summary card">
          <h2>Order Summary</h2>
          <div className="summary-row"><span>Status</span><strong>{order.status.replace(/_/g, " ")}</strong></div>
          <div className="summary-row"><span>Subtotal</span><span>${order.subtotal_usd}</span></div>
          {order.packaging_fee_usd && (
            <div className="summary-row"><span>Packaging</span><span>${order.packaging_fee_usd}</span></div>
          )}
          <div className="summary-row"><span>Shipping</span><span>${order.shipping_fee_usd}</span></div>
          <div className="summary-row summary-row--total">
            <span>Total</span>
            <span>
              <strong>${order.total_amount_usd}</strong>
              {order.total_amount_kes && (
                <span className="summary-kes"> / KES {Number(order.total_amount_kes).toLocaleString("en-KE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              )}
            </span>
          </div>
        </div>
      )}

      {/* ── Guest notice ──────────────────────────────────────────────────── */}
      {state.guestAccessToken && (
        <div className="callout callout--info">
          <p>
            A confirmation email has been sent. Create an account with your email to track
            this order from your dashboard, or bookmark this page.
          </p>
        </div>
      )}

      {/* ── What happens next ─────────────────────────────────────────────── */}
      <div className="confirmation-page__next-steps card">
        <h2>What happens next?</h2>
        <ol>
          <li>We confirm your payment (1–2 hours)</li>
          <li>Your order is sent to our Vietnam factory for production (7–14 days)</li>
          <li>Quality checked and shipped to Kenya by air freight</li>
          <li>You receive a WhatsApp update at each milestone</li>
          <li>Collect from our Nairobi office</li>
        </ol>
        <p>Reply to any of our WhatsApp messages with <strong>{orderNumber}</strong> to check your status anytime.</p>
      </div>

      <div className="confirmation-page__actions">
        <Link to="/account/orders" className="btn btn--primary">View My Orders</Link>
        <Link to="/products" className="btn btn--outline">Continue Shopping</Link>
      </div>
    </div>
  );
}

import { Link, useLocation, useParams } from "react-router";
import { useOrder } from "../orders/hooks";

interface ConfirmationState {
  paymentInstructions?: Record<string, unknown>;
  guestAccessToken?: string | null;
}

export function ConfirmationPage() {
  const { orderNumber } = useParams<{ orderNumber: string }>();
  const location = useLocation();
  const state = (location.state ?? {}) as ConfirmationState;
  const { data: order } = useOrder(orderNumber, state.guestAccessToken ?? undefined);

  return (
    <div className="page">
      <h1>Thank you for your order!</h1>
      <p>Order number: <strong>{orderNumber}</strong></p>

      {state.paymentInstructions?.bankDetails != null && (
        <div className="callout">
          <h2>Bank transfer details</h2>
          <pre>{JSON.stringify(state.paymentInstructions.bankDetails, null, 2)}</pre>
          <p>Amount: {String(state.paymentInstructions.amountKes)} KES</p>
        </div>
      )}
      {typeof state.paymentInstructions?.message === "string" && (
        <div className="callout"><p>{state.paymentInstructions.message}</p></div>
      )}
      {typeof state.paymentInstructions?.error === "string" && (
        <div className="callout error"><p>{state.paymentInstructions.error}</p></div>
      )}

      {order && (
        <div className="order-summary">
          <p>Status: {order.status}</p>
          <p>Total: ${order.total_amount_usd}</p>
        </div>
      )}

      {state.guestAccessToken && (
        <p className="muted">
          Create an account with this email to view this order again later, or keep this confirmation page open.
        </p>
      )}

      <Link to="/products">Continue shopping</Link>
    </div>
  );
}

/**
 * EquityBankPaymentCard — Equity Bank Paybill payment instructions.
 *
 * Displayed at checkout when the customer selects "Bank Transfer / Paybill".
 * Shows exact steps for paying via M-Pesa / Equity Bank Paybill 247247.
 *
 * Usage:
 *   <EquityBankPaymentCard orderNumber="ORD-20250918-00123" amountKes={18500} />
 */

import { useState } from "react";

interface EquityBankPaymentCardProps {
  orderNumber: string;
  amountKes: number | string;
  amountUsd?: number | string;
}

export function EquityBankPaymentCard({ orderNumber, amountKes, amountUsd }: EquityBankPaymentCardProps) {
  return (
    <div className="equity-card">
      {/* Equity Bank branding banner */}
      <div className="equity-card__banner">
        <div className="equity-card__bank-logo" aria-hidden="true">
          <span className="equity-card__bank-text">Equity</span>
          <span className="equity-card__bank-sub">Bank</span>
        </div>
        <span className="equity-card__tag">Secure Payment</span>
      </div>

      {/* Payment details */}
      <div className="equity-card__body">
        <h3 className="equity-card__title">Pay via M-Pesa Paybill</h3>

        <ol className="equity-card__steps">
          <li>Open <strong>M-Pesa</strong> on your phone</li>
          <li>Select <strong>Lipa na M-Pesa → Pay Bill</strong></li>
          <li>
            Enter Business Number:{" "}
            <CopyField label="Paybill" value="247247" />
          </li>
          <li>
            Enter Account Number:{" "}
            <CopyField label="Account" value="0310173604563" />
          </li>
          <li>
            Enter Amount:{" "}
            <strong className="equity-card__amount">
              KES {Math.round(Number(amountKes)).toLocaleString("en-KE")}
              {amountUsd && <span className="equity-card__usd"> (~${Number(amountUsd).toFixed(2)})</span>}
            </strong>
          </li>
          <li>
            Enter Reference / Reason:{" "}
            <CopyField label="Reference" value={orderNumber} />
          </li>
          <li>Enter your M-Pesa PIN and confirm</li>
        </ol>

        <div className="equity-card__note">
          <p>
            <strong>Note:</strong> Your order will be confirmed once our team verifies the payment.
            This usually takes <strong>1–2 business hours</strong> during working hours.
            Keep your M-Pesa confirmation SMS as proof of payment.
          </p>
        </div>

        <div className="equity-card__summary">
          <div className="equity-card__row">
            <span>Paybill</span><strong>247247</strong>
          </div>
          <div className="equity-card__row">
            <span>Account</span><strong>0310173604563</strong>
          </div>
          <div className="equity-card__row">
            <span>Reference</span><strong>{orderNumber}</strong>
          </div>
          <div className="equity-card__row equity-card__row--total">
            <span>Amount</span>
            <strong>KES {Math.round(Number(amountKes)).toLocaleString("en-KE")}</strong>
          </div>
        </div>
      </div>
    </div>
  );
}


// ── Inline copy helper ────────────────────────────────────────────────────────

function CopyField({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false);

  function copy() {
    void navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }
  return (
    <span className="copy-field" style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
      <strong className="copy-field__value">{value}</strong>
      <button
        type="button"
        className="copy-field__btn"
        onClick={copy}
        aria-label={`Copy ${label}`}
        title={`Copy ${label}`}
        style={{
          padding: "2px 8px",
          fontSize: "0.75rem",
          borderRadius: "4px",
          border: "1px solid #ccc",
          background: copied ? "#e8f5e9" : "#f5f5f5",
          cursor: "pointer",
        }}
      >
        {copied ? "Copied" : "Copy"}
      </button>
    </span>
  );
}


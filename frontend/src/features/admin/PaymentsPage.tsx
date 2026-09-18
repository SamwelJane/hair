import { useAdminPayments, useConfirmBankTransfer, useRejectBankTransfer } from "./hooks";

export function AdminPaymentsPage() {
  const { data, isLoading } = useAdminPayments();
  const confirm = useConfirmBankTransfer();
  const reject = useRejectBankTransfer();

  if (isLoading) return <div className="page">Loading...</div>;

  return (
    <div className="page">
      <h1>Payments</h1>

      <h2>Pending Bank Transfer Payments</h2>
      <table className="page-table">
        <thead><tr><th>Order</th><th>Customer</th><th>Amount (KES)</th><th /></tr></thead>
        <tbody>
          {data?.pending_bank_transfers.map((p) => (
            <tr key={p.id}>
              <td>{p.order_number}</td><td>{p.customer_email}</td><td>{p.amount_kes}</td>
              <td className="link-row">
                <button type="button" onClick={() => confirm.mutate(p.id)}>Confirm Received</button>
                <button type="button" className="danger" onClick={() => reject.mutate(p.id)}>Reject</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {data?.pending_bank_transfers.length === 0 && <p>No pending bank transfer payments.</p>}

      <h2>M-Pesa Payments (automatic)</h2>
      <p className="muted">M-Pesa payments are confirmed automatically via Safaricom's callback - shown for reconciliation only.</p>
      <table className="page-table">
        <thead><tr><th>Order</th><th>Customer</th><th>Amount (KES)</th><th>Status</th><th>Receipt</th></tr></thead>
        <tbody>
          {data?.mpesa_payments.map((p) => (
            <tr key={p.id}><td>{p.order_number}</td><td>{p.customer_email}</td><td>{p.amount_kes}</td><td>{p.status}</td><td>{p.provider_ref ?? "-"}</td></tr>
          ))}
        </tbody>
      </table>

      <h2>Recent Bank Transfer History</h2>
      <table className="page-table">
        <thead><tr><th>Order</th><th>Customer</th><th>Amount (KES)</th><th>Status</th><th>By</th></tr></thead>
        <tbody>
          {data?.resolved_bank_transfers.map((p) => (
            <tr key={p.id}><td>{p.order_number}</td><td>{p.customer_email}</td><td>{p.amount_kes}</td><td>{p.status}</td><td>{p.confirmed_by_name ?? "-"}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

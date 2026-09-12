# Data Privacy Notice

This document describes what personal data Hiar Business collects, why, how long
it is kept, and how a customer can exercise their data rights. It is written to
be published as the `/privacy` page content and kept in sync with it.

## What we collect

| Data | Why we collect it | Where it lives |
|---|---|---|
| Name, email, password (hashed) | Account creation, login | `users` table (`passwordHash` is bcrypt-hashed, never stored or logged in plaintext) |
| Shipping address, phone number | Delivering orders, customs declarations | `orders.shippingAddress` (JSON), snapshotted per order |
| Order and payment history | Fulfilling orders, support, accounting | `orders`, `order_items`, `payments` |
| M-Pesa phone number | Initiating M-Pesa STK push payments | Passed to Safaricom's Daraja API at checkout time; not persisted beyond the payment record's provider reference |
| Bank transfer proof of payment (optional upload) | Manually reconciling bank transfers | `payments.proofOfPaymentUrl` |
| Product reviews | Displayed publicly on product pages after admin approval | `reviews` |
| Admin action history | Security, dispute resolution, accountability | `audit_logs`, `order_status_history` |

We do not collect payment card numbers - M-Pesa and bank transfer are handled by
Safaricom and the customer's own bank respectively.

## Retention

- Account and order data is kept for as long as the account is active, plus a
  reasonable period afterward for tax/accounting records (recommend: 7 years,
  matching typical financial record-keeping requirements - confirm against
  local law in your operating jurisdiction).
- `audit_logs` are kept indefinitely as a security/accountability record but
  contain no more personal data than the action itself required (see
  `src/lib/security/audit.ts`).

## Data subject rights

A customer can request, by contacting support:
- **Access** - a copy of their account, order, and payment data.
- **Correction** - of inaccurate profile or address data.
- **Deletion** - of their account, subject to retaining order records required
  for tax/accounting compliance (those are retained in de-identified form where
  feasible).

## Third parties data is shared with

- **Safaricom (Daraja API)** - phone number and amount, to process M-Pesa payments.
- **Cloudinary** - product images only (no personal data).
- **Resend** (email) and **Twilio** (WhatsApp) - supplier contact details, to
  notify suppliers of new orders. Customer data is not sent to suppliers.
- Suppliers themselves never receive customer names, addresses, or contact
  information - only what is needed to produce the order (product, variant,
  quantity), per the managed-marketplace model.

## Security measures

- Passwords are hashed with bcrypt, never stored or logged in plaintext.
- Role-based access control restricts admin/staff-only data to those roles.
- Login and payment-initiation endpoints are rate-limited (see
  `src/lib/security/rate-limit.ts`).
- Admin mutations are recorded in an audit log (see `src/lib/security/audit.ts`).

This notice is a starting point, not legal advice - have it reviewed against
the specific data protection law that applies to your customers (e.g. Kenya's
Data Protection Act, or GDPR if serving EU residents) before relying on it.

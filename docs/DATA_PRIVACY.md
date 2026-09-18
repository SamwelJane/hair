# Data Privacy Notice

This document describes what personal data Hiar Business collects, why, how long
it is kept, and how a customer can exercise their data rights. It is written to
be published as the `/privacy` page content and kept in sync with it.

## What we collect

| Data | Why we collect it | Where it lives |
|---|---|---|
| Name, email, password (hashed) | Account creation, login | `users` table (`password_hash` is bcrypt-hashed, never stored or logged in plaintext) |
| Shipping address, phone number | Delivering orders, customs declarations | `orders.shipping_address` (JSON), snapshotted per order |
| Order and payment history | Fulfilling orders, support, accounting | `orders`, `order_items`, `payments` |
| M-Pesa phone number | Initiating M-Pesa STK push payments | Passed to Safaricom's Daraja API at checkout time; not persisted beyond the payment record's provider reference |
| Bank transfer proof of payment (optional upload) | Manually reconciling bank transfers | `payments.proof_of_payment_url` |
| Product reviews | Displayed publicly on product pages after admin approval | `reviews` |
| Admin/warehouse/ops action history | Security, dispute resolution, accountability | `audit_logs`, `order_status_history` |
| **Non-account ("external shipment") customer name, phone, and optional email** | A customer who bought from a Vietnamese supplier outside the platform (e.g. WhatsApp/Facebook) still needs their parcel tracked through Cherubim warehouse, consolidation, and Kenya customs | `external_shipments.customer_name` / `.customer_phone` / `.customer_email`, captured by warehouse staff at intake - no `users` row is created for this person, since they never register an account |
| **Package photos, weight/dimensions, QC notes** | Verifying condition on arrival, resolving damage/loss disputes | `packages.photo_urls` (Cloudinary), `packages.weight_grams`/`length_cm`/`width_cm`/`height_cm`, `packages.notes` |
| **Customs declaration data** (HS code, declared value, duty/VAT) | Legally required for clearing goods through Kenyan customs | `customs_declarations` |
| **Operational exceptions** (damage, loss, customs queries, mismatches) | Tracking and resolving fulfilment problems | `ops_exceptions` (polymorphic `entity_type`/`entity_id`, same pattern as `audit_logs`) |

We do not collect payment card numbers - M-Pesa and bank transfer are handled by
Safaricom and the customer's own bank respectively.

### Warehouse shipping labels are deliberately de-identified

A physical label printed at the Vietnam warehouse (`services/packages.py::build_label`)
never carries a customer's full name - only a masked form (`mask_customer_name`,
e.g. "Jane Doe" → "Jane D."), the tracking number, and destination city/country.
This applies identically to platform-order packages and external-shipment
packages. The full name only ever appears inside the authenticated admin/
warehouse portal, never on paper that travels with the parcel.

### The public tracking page and customer-facing timeline

`GET /track/{tracking_number}` (`routers/tracking.py`) and the `TrackingEvent`
timeline it renders are intentionally free of PII beyond what the tracking
number's holder already knows: package/consolidation status, location
strings ("Vietnam", "Kenya", free-text transit updates), and event labels. No
endpoint resolves a tracking number back to a name, phone number, or address
without authentication as the order's owner (platform orders) or admin/
warehouse/ops role (external shipments, which have no "owner" login at all).

## Retention

- Account and order data is kept for as long as the account is active, plus a
  reasonable period afterward for tax/accounting records (recommend: 7 years,
  matching typical financial record-keeping requirements - confirm against
  local law in your operating jurisdiction).
- External-shipment records follow the same retention period as orders, even
  though they have no associated account - they are tied to a physical
  shipment and its customs/accounting record, not to a login.
- `audit_logs` and `ops_exceptions` are kept indefinitely as a security/
  accountability record but contain no more personal data than the action
  itself required (see `app/services/audit.py::log_audit`).

## Data subject rights

A customer can request, by contacting support:
- **Access** - a copy of their account, order, payment, and (for external
  shipments) shipment-intake data.
- **Correction** - of inaccurate profile, address, or external-shipment
  contact data.
- **Deletion** - of their account, subject to retaining order/shipment
  records required for tax/accounting and customs compliance (those are
  retained in de-identified form where feasible). Because an external
  shipment has no login to delete, a deletion request for one is handled by
  redacting `customer_name`/`customer_phone`/`customer_email` on the record
  while keeping the shipment/customs data needed for compliance.

## Third parties data is shared with

- **Safaricom (Daraja API)** - phone number and amount, to process M-Pesa payments.
- **Cloudinary** - product images, and package condition/QC photos captured at
  the warehouse (no other personal data embedded in those photos beyond what
  is visible in the image itself).
- **Resend** (email) and **Twilio** (WhatsApp) - contact details needed to
  send the notification in question: supplier phone/email for new-order
  alerts, and customer/external-shipment phone number for order-status,
  package-received, and customs-cleared updates (`app/services/notifications/`).
- Suppliers themselves never receive customer names, addresses, or contact
  information - only what is needed to produce the order (product, variant,
  quantity), per the managed-marketplace model.
- Freight carriers and Kenyan customs authorities receive only what is legally
  required to move and clear a shipment (declared value, HS code, consignee
  name/destination) - never account credentials or payment details.

## Security measures

- Passwords are hashed with bcrypt, never stored or logged in plaintext.
- Role-based access control restricts admin/staff/warehouse/Kenya-ops-only
  data to those roles, at the operation level (`app/core/permissions.py`) as
  well as the endpoint-role level (`app/core/deps.py`) - see
  `docs/VNKE_ROADMAP.md` Phase 4/11 for why both layers exist.
- Login and payment-initiation endpoints are rate-limited (see
  `app/core/rate_limit.py`).
- Admin/warehouse/ops mutations are recorded in an audit log (see
  `app/services/audit.py::log_audit`), and operational problems are tracked
  in a dedicated exceptions table rather than left as untracked notes.

This notice is a starting point, not legal advice - have it reviewed against
the specific data protection law that applies to your customers (e.g. Kenya's
Data Protection Act, or GDPR if serving EU residents) before relying on it.

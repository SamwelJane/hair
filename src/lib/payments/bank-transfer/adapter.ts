import type { PaymentProvider, InitiatePaymentInput, InitiatePaymentResult } from "../provider";

/**
 * Bank transfer is manual: we just record that the customer intends to pay this
 * way and show them account details + a reference. An admin later confirms
 * receipt via /admin/payments, which is what actually marks the order Paid.
 */
export const bankTransferProvider: PaymentProvider = {
  async initiate(input: InitiatePaymentInput): Promise<InitiatePaymentResult> {
    return {
      providerRef: `BANK-${input.orderId}`,
      status: "INITIATED",
    };
  },
};

export const BANK_TRANSFER_DETAILS = {
  bankName: process.env.BANK_TRANSFER_BANK_NAME ?? "Set BANK_TRANSFER_BANK_NAME in env",
  accountName: process.env.BANK_TRANSFER_ACCOUNT_NAME ?? "Hiar Business Ltd",
  accountNumber: process.env.BANK_TRANSFER_ACCOUNT_NUMBER ?? "Set BANK_TRANSFER_ACCOUNT_NUMBER in env",
  swiftCode: process.env.BANK_TRANSFER_SWIFT_CODE ?? "",
};

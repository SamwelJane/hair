import type { PaymentProvider, InitiatePaymentInput, InitiatePaymentResult } from "../provider";
import { stkPush } from "./daraja-client";

export const mpesaProvider: PaymentProvider = {
  async initiate(input: InitiatePaymentInput): Promise<InitiatePaymentResult> {
    if (!input.phone) {
      throw new Error("Phone number is required for M-Pesa payment.");
    }

    const response = await stkPush({
      phone: input.phone,
      amountKes: input.amountKes,
      accountReference: input.orderId,
      transactionDesc: `Hiar Business order ${input.orderId}`,
    });

    return {
      providerRef: response.CheckoutRequestID,
      status: "PENDING",
    };
  },
};

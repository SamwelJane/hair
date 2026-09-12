export interface InitiatePaymentInput {
  orderId: string;
  amountKes: number;
  phone?: string;
}

export interface InitiatePaymentResult {
  providerRef: string;
  status: "INITIATED" | "PENDING";
}

/**
 * Common seam over payment providers. M-Pesa is automated (STK push + callback);
 * bank transfer is manual (admin confirms receipt) but still implements this
 * interface so order/payment code doesn't need to branch on provider type.
 */
export interface PaymentProvider {
  initiate(input: InitiatePaymentInput): Promise<InitiatePaymentResult>;
}

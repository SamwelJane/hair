const DARAJA_BASE_URL =
  process.env.MPESA_ENV === "production"
    ? "https://api.safaricom.co.ke"
    : "https://sandbox.safaricom.co.ke";

async function getAccessToken(): Promise<string> {
  const consumerKey = process.env.MPESA_CONSUMER_KEY!;
  const consumerSecret = process.env.MPESA_CONSUMER_SECRET!;
  const auth = Buffer.from(`${consumerKey}:${consumerSecret}`).toString("base64");

  const res = await fetch(`${DARAJA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials`, {
    headers: { Authorization: `Basic ${auth}` },
  });

  if (!res.ok) {
    throw new Error(`Failed to get Daraja access token: ${res.status}`);
  }

  const data = (await res.json()) as { access_token: string };
  return data.access_token;
}

function buildTimestamp(): string {
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}${pad(
    now.getHours()
  )}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
}

export interface StkPushInput {
  phone: string; // format 2547XXXXXXXX
  amountKes: number;
  accountReference: string;
  transactionDesc: string;
}

export interface StkPushResponse {
  MerchantRequestID: string;
  CheckoutRequestID: string;
  ResponseCode: string;
  ResponseDescription: string;
  CustomerMessage: string;
}

export async function stkPush(input: StkPushInput): Promise<StkPushResponse> {
  const shortcode = process.env.MPESA_SHORTCODE!;
  const passkey = process.env.MPESA_PASSKEY!;
  const timestamp = buildTimestamp();
  const password = Buffer.from(`${shortcode}${passkey}${timestamp}`).toString("base64");

  const accessToken = await getAccessToken();

  const res = await fetch(`${DARAJA_BASE_URL}/mpesa/stkpush/v1/processrequest`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      BusinessShortCode: shortcode,
      Password: password,
      Timestamp: timestamp,
      TransactionType: "CustomerPayBillOnline",
      Amount: Math.ceil(input.amountKes),
      PartyA: input.phone,
      PartyB: shortcode,
      PhoneNumber: input.phone,
      CallBackURL: process.env.MPESA_CALLBACK_URL,
      AccountReference: input.accountReference,
      TransactionDesc: input.transactionDesc,
    }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Daraja STK push failed: ${res.status} ${body}`);
  }

  return res.json();
}

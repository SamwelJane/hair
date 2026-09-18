import { useState } from "react";
import { Pressable, ScrollView, StyleSheet, Switch, Text, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import { useAuth } from "../lib/auth/AuthContext";
import { useCart, useClearCart } from "../features/cart/hooks";
import { setGuestCartToken } from "../lib/cart/guestCartToken";
import { useCheckoutSummary, useSubmitCheckout } from "../features/checkout/hooks";
import { colors } from "../lib/theme";

export default function CheckoutScreen() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuth();
  const { data: cart } = useCart();
  const submit = useSubmitCheckout();
  const clearCart = useClearCart();

  const [fullName, setFullName] = useState(user?.name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [line1, setLine1] = useState("");
  const [city, setCity] = useState("");
  const [countryCode, setCountryCode] = useState("KE");
  const [phone, setPhone] = useState("");
  const [paymentMethod, setPaymentMethod] = useState<"MPESA" | "BANK_TRANSFER">("BANK_TRANSFER");
  const [mpesaPhone, setMpesaPhone] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const items = (cart?.items ?? []).map((i) => ({ product_id: i.product_id, variant_id: i.variant_id, quantity: i.quantity }));
  const summary = useCheckoutSummary(items, countryCode, undefined);

  if (!cart || cart.items.length === 0) {
    return (
      <View style={styles.container}>
        <Text style={styles.muted}>Your cart is empty.</Text>
      </View>
    );
  }

  async function handleSubmit() {
    setSubmitting(true);
    setError(null);
    try {
      const result = await submit.mutateAsync({
        items,
        shipping_address: {
          full_name: fullName,
          email: isAuthenticated ? undefined : email,
          line1,
          city,
          country_code: countryCode,
          phone,
        },
        payment_method: paymentMethod,
        mpesa_phone: paymentMethod === "MPESA" ? mpesaPhone : undefined,
      });
      await clearCart.mutateAsync().catch(() => undefined);
      await setGuestCartToken(null);
      router.replace({
        pathname: "/checkout-confirmation/[orderNumber]",
        params: {
          orderNumber: result.order_number,
          guestAccessToken: result.guest_access_token ?? "",
          paymentInstructions: JSON.stringify(result.payment_instructions ?? {}),
        },
      });
    } catch {
      setError("Checkout failed. Please check your details and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.sectionTitle}>Shipping details</Text>
      <Text style={styles.label}>Full name</Text>
      <TextInput style={styles.input} value={fullName} onChangeText={setFullName} />
      {!isAuthenticated && (
        <>
          <Text style={styles.label}>Email</Text>
          <TextInput style={styles.input} autoCapitalize="none" keyboardType="email-address" value={email} onChangeText={setEmail} />
        </>
      )}
      <Text style={styles.label}>Address line 1</Text>
      <TextInput style={styles.input} value={line1} onChangeText={setLine1} />
      <Text style={styles.label}>City</Text>
      <TextInput style={styles.input} value={city} onChangeText={setCity} />
      <Text style={styles.label}>Country code</Text>
      <TextInput style={styles.input} maxLength={2} autoCapitalize="characters" value={countryCode} onChangeText={(t) => setCountryCode(t.toUpperCase())} />
      <Text style={styles.label}>Phone</Text>
      <TextInput style={styles.input} value={phone} onChangeText={setPhone} />

      <Text style={styles.sectionTitle}>Payment</Text>
      <View style={styles.row}>
        <Text>Bank transfer</Text>
        <Switch value={paymentMethod === "BANK_TRANSFER"} onValueChange={() => setPaymentMethod("BANK_TRANSFER")} />
      </View>
      <View style={styles.row}>
        <Text>M-Pesa</Text>
        <Switch value={paymentMethod === "MPESA"} onValueChange={() => setPaymentMethod("MPESA")} />
      </View>
      {paymentMethod === "MPESA" && (
        <>
          <Text style={styles.label}>M-Pesa phone</Text>
          <TextInput style={styles.input} value={mpesaPhone} onChangeText={setMpesaPhone} />
        </>
      )}

      {summary.data && (
        <View style={styles.summary}>
          <Text>Subtotal: ${summary.data.subtotal_usd}</Text>
          <Text>Shipping: ${summary.data.shipping_fee_usd}</Text>
          <Text>Handling: ${summary.data.handling_fee_usd}</Text>
          <Text style={styles.total}>Total: ${summary.data.total_amount_usd}</Text>
        </View>
      )}
      {error && <Text style={styles.error}>{error}</Text>}

      <Pressable style={styles.button} onPress={() => void handleSubmit()} disabled={submitting}>
        <Text style={styles.buttonText}>{submitting ? "Placing order..." : "Place Order"}</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: colors.bg },
  sectionTitle: { fontSize: 16, fontWeight: "700", marginTop: 16, marginBottom: 6, color: colors.ink },
  label: { fontSize: 13, color: colors.muted, marginTop: 8 },
  input: { borderWidth: 1, borderColor: colors.border, borderRadius: 8, padding: 10, backgroundColor: colors.surface, marginTop: 4 },
  row: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingVertical: 6 },
  summary: { marginTop: 16, backgroundColor: colors.surface, borderRadius: 8, padding: 12, borderWidth: 1, borderColor: colors.border, gap: 4 },
  total: { fontWeight: "700", marginTop: 4 },
  error: { color: colors.danger, marginTop: 10 },
  button: { backgroundColor: colors.accent, borderRadius: 999, padding: 14, alignItems: "center", marginVertical: 20 },
  buttonText: { color: "#fff", fontWeight: "600" },
  muted: { color: colors.muted, padding: 16 },
});

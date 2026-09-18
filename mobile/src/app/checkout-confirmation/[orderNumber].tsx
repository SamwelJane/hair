import { Link, useLocalSearchParams } from "expo-router";
import { ScrollView, StyleSheet, Text } from "react-native";
import { useOrder } from "../../features/orders/hooks";
import { colors } from "../../lib/theme";

export default function CheckoutConfirmationScreen() {
  const { orderNumber, guestAccessToken, paymentInstructions } = useLocalSearchParams<{
    orderNumber: string;
    guestAccessToken?: string;
    paymentInstructions?: string;
  }>();
  const { data: order } = useOrder(orderNumber, guestAccessToken || undefined);
  const instructions = paymentInstructions ? (JSON.parse(paymentInstructions) as Record<string, unknown>) : {};

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Thank you for your order!</Text>
      <Text>Order number: <Text style={{ fontWeight: "700" }}>{orderNumber}</Text></Text>

      {typeof instructions.message === "string" && <Text style={styles.callout}>{instructions.message}</Text>}
      {typeof instructions.error === "string" && <Text style={[styles.callout, styles.error]}>{instructions.error}</Text>}
      {instructions.bankDetails != null && (
        <Text style={styles.callout}>
          Bank transfer details:{"\n"}{JSON.stringify(instructions.bankDetails, null, 2)}{"\n\n"}Amount: {String(instructions.amountKes)} KES
        </Text>
      )}

      {order && (
        <Text style={styles.callout}>Status: {order.status} · Total: ${order.total_amount_usd}</Text>
      )}

      <Link href="/" style={styles.link}>Continue shopping</Link>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: colors.bg },
  title: { fontSize: 20, fontWeight: "700", marginBottom: 10, color: colors.ink },
  callout: { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, borderRadius: 8, padding: 12, marginTop: 12 },
  error: { color: colors.danger },
  link: { marginTop: 20, color: colors.accent },
});

import { useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { Stack, useLocalSearchParams, useRouter } from "expo-router";
import { useCancelOrder, useOrder, useRequestReturn, useSubmitReview } from "../../features/orders/hooks";
import { colors } from "../../lib/theme";

const CANCELLABLE_STATUSES = new Set([
  "PENDING_PAYMENT", "PAID", "SENT_TO_SUPPLIER", "SUPPLIER_PROCESSING", "READY_FOR_PICKUP", "RECEIVED_AT_OFFICE",
]);

export default function OrderDetailScreen() {
  const { orderNumber } = useLocalSearchParams<{ orderNumber: string }>();
  const router = useRouter();
  const { data: order, isLoading } = useOrder(orderNumber);
  const cancelOrder = useCancelOrder();
  const submitReview = useSubmitReview();
  const requestReturn = useRequestReturn();

  const [returnReason, setReturnReason] = useState("");
  const [returnSubmitted, setReturnSubmitted] = useState(false);
  const [reviewBody, setReviewBody] = useState<Record<string, string>>({});
  const [submittedProducts, setSubmittedProducts] = useState<Set<string>>(new Set());

  if (isLoading) return <ActivityIndicator style={{ marginTop: 40 }} />;
  if (!order) return <Text style={styles.muted}>Order not found.</Text>;

  const canCancel = CANCELLABLE_STATUSES.has(order.status);
  const isDelivered = order.status === "DELIVERED";
  const uniqueProducts = [...new Map(order.items.map((i) => [i.product_id, i])).values()];

  return (
    <ScrollView style={styles.container}>
      <Stack.Screen options={{ title: `Order ${orderNumber}`, headerShown: true }} />
      <Text style={styles.badge}>{order.status.replaceAll("_", " ")}</Text>
      <Pressable onPress={() => router.push(`/track/${order.tracking_number}`)}>
        <Text style={styles.trackingLine}>Tracking number: <Text style={{ color: colors.accent }}>{order.tracking_number}</Text></Text>
      </Pressable>

      {order.packages.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Packages</Text>
          {order.packages.map((pkg) => (
            <View key={pkg.package_code} style={styles.itemRow}>
              <Text>{pkg.package_code}</Text>
              <Text>{pkg.status.replaceAll("_", " ")}</Text>
            </View>
          ))}
        </View>
      )}

      {order.items.map((item, idx) => (
        <View key={idx} style={styles.itemRow}>
          <Text>{item.quantity}× {item.product_name}{item.variant_label ? ` (${item.variant_label})` : ""}</Text>
          <Text>${item.line_total_usd}</Text>
        </View>
      ))}
      <Text style={styles.total}>Total: ${order.total_amount_usd}</Text>

      {canCancel && (
        <Pressable style={styles.dangerButton} onPress={() => cancelOrder.mutate(order.order_number)} disabled={cancelOrder.isPending}>
          <Text style={styles.dangerButtonText}>Cancel Order</Text>
        </Pressable>
      )}

      {isDelivered && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Request a Return</Text>
          {returnSubmitted || requestReturn.isSuccess ? (
            <Text>Your return request has been submitted.</Text>
          ) : (
            <>
              <TextInput
                style={styles.textArea}
                multiline
                placeholder="Tell us why you'd like to return this order"
                value={returnReason}
                onChangeText={setReturnReason}
              />
              <Pressable
                style={styles.button}
                onPress={async () => { await requestReturn.mutateAsync({ order_id: order.id, reason: returnReason }); setReturnSubmitted(true); }}
                disabled={requestReturn.isPending || !returnReason}
              >
                <Text style={styles.buttonText}>Request Return</Text>
              </Pressable>
            </>
          )}
        </View>
      )}

      {isDelivered && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Reviews</Text>
          {uniqueProducts.map((item) => {
            const done = submittedProducts.has(item.product_id);
            return (
              <View key={item.product_id} style={{ marginBottom: 12 }}>
                <Text style={{ fontWeight: "600" }}>{item.product_name}</Text>
                {done ? (
                  <Text style={styles.muted}>Thanks for your review!</Text>
                ) : (
                  <>
                    <TextInput
                      style={styles.textArea}
                      multiline
                      placeholder="Share your thoughts (rating out of 5 assumed as 5)"
                      value={reviewBody[item.product_id] ?? ""}
                      onChangeText={(t) => setReviewBody((prev) => ({ ...prev, [item.product_id]: t }))}
                    />
                    <Pressable
                      style={styles.button}
                      disabled={!reviewBody[item.product_id]}
                      onPress={async () => {
                        await submitReview.mutateAsync({ order_id: order.id, product_id: item.product_id, rating: 5, body: reviewBody[item.product_id] });
                        setSubmittedProducts((prev) => new Set(prev).add(item.product_id));
                      }}
                    >
                      <Text style={styles.buttonText}>Submit Review</Text>
                    </Pressable>
                  </>
                )}
              </View>
            );
          })}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: colors.bg },
  badge: { color: colors.accent, fontWeight: "600", marginBottom: 12 },
  itemRow: { flexDirection: "row", justifyContent: "space-between", paddingVertical: 6, borderBottomWidth: 1, borderBottomColor: colors.border },
  total: { fontWeight: "700", fontSize: 16, marginTop: 10 },
  dangerButton: { borderWidth: 1, borderColor: colors.danger, borderRadius: 999, padding: 12, alignItems: "center", marginTop: 16 },
  dangerButtonText: { color: colors.danger, fontWeight: "600" },
  section: { marginTop: 20, borderTopWidth: 1, borderTopColor: colors.border, paddingTop: 16 },
  sectionTitle: { fontSize: 16, fontWeight: "700", marginBottom: 8 },
  textArea: { borderWidth: 1, borderColor: colors.border, borderRadius: 8, padding: 10, backgroundColor: colors.surface, minHeight: 60, marginBottom: 8 },
  button: { backgroundColor: colors.accent, borderRadius: 999, padding: 10, alignItems: "center", alignSelf: "flex-start", paddingHorizontal: 16 },
  buttonText: { color: "#fff", fontWeight: "600" },
  muted: { color: colors.muted, padding: 16 },
  trackingLine: { color: colors.muted, marginBottom: 12 },
});

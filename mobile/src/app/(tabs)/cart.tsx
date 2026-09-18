import { useState } from "react";
import { ActivityIndicator, FlatList, Image, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import { useCart, useRemoveCartItem, useUpdateCartItem } from "../../features/cart/hooks";
import { colors } from "../../lib/theme";

function TrackOrderBox() {
  const router = useRouter();
  const [trackingNumber, setTrackingNumber] = useState("");
  return (
    <View style={styles.trackBox}>
      <Text style={styles.muted}>Have a tracking number?</Text>
      <View style={styles.trackRow}>
        <TextInput
          style={[styles.qtyInput, { flex: 1, width: undefined }]}
          placeholder="e.g. HB-ABC123"
          value={trackingNumber}
          onChangeText={setTrackingNumber}
        />
        <Pressable
          style={styles.trackButton}
          disabled={!trackingNumber}
          onPress={() => router.push(`/track/${trackingNumber.trim()}`)}
        >
          <Text style={styles.checkoutButtonText}>Track</Text>
        </Pressable>
      </View>
    </View>
  );
}

export default function CartScreen() {
  const router = useRouter();
  const { data: cart, isLoading } = useCart();
  const updateItem = useUpdateCartItem();
  const removeItem = useRemoveCartItem();

  if (isLoading) return <ActivityIndicator style={{ marginTop: 40 }} />;

  const items = cart?.items ?? [];
  const total = items.reduce((sum, item) => sum + Number(item.unit_price_usd) * item.quantity, 0);

  if (items.length === 0) {
    return (
      <View style={styles.container}>
        <Text style={styles.muted}>Your cart is empty.</Text>
        <TrackOrderBox />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={items}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ gap: 10 }}
        renderItem={({ item }) => (
          <View style={styles.card}>
            {item.image_url && <Image source={{ uri: item.image_url }} style={styles.image} />}
            <View style={{ flex: 1 }}>
              <Text style={styles.name}>{item.name}</Text>
              {item.variant_label && <Text style={styles.muted}>{item.variant_label}</Text>}
              <Text style={styles.price}>${item.unit_price_usd} each</Text>
            </View>
            <TextInput
              style={styles.qtyInput}
              keyboardType="number-pad"
              defaultValue={String(item.quantity)}
              onEndEditing={(e) => updateItem.mutate({ itemId: item.id, quantity: Number(e.nativeEvent.text) || 1 })}
            />
            <Pressable onPress={() => removeItem.mutate(item.id)}>
              <Text style={styles.remove}>Remove</Text>
            </Pressable>
          </View>
        )}
      />
      <Text style={styles.total}>Total: ${total.toFixed(2)}</Text>
      <Pressable style={styles.checkoutButton} onPress={() => router.push("/checkout")}>
        <Text style={styles.checkoutButtonText}>Proceed to Checkout</Text>
      </Pressable>
      <TrackOrderBox />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: colors.bg },
  card: { flexDirection: "row", gap: 10, alignItems: "center", backgroundColor: colors.surface, borderRadius: 10, padding: 10, borderWidth: 1, borderColor: colors.border },
  image: { width: 48, height: 48, borderRadius: 8 },
  name: { fontWeight: "600", color: colors.ink },
  price: { color: colors.muted, fontSize: 12 },
  muted: { color: colors.muted },
  qtyInput: { borderWidth: 1, borderColor: colors.border, borderRadius: 6, width: 48, padding: 6, textAlign: "center" },
  remove: { color: colors.danger, fontSize: 12 },
  total: { fontSize: 18, fontWeight: "700", marginTop: 16, color: colors.ink },
  checkoutButton: { backgroundColor: colors.accent, borderRadius: 999, padding: 14, alignItems: "center", marginTop: 12 },
  checkoutButtonText: { color: "#fff", fontWeight: "600" },
  trackBox: { marginTop: 24, borderTopWidth: 1, borderTopColor: colors.border, paddingTop: 16 },
  trackRow: { flexDirection: "row", gap: 8, marginTop: 8, alignItems: "center" },
  trackButton: { backgroundColor: colors.accent, borderRadius: 8, paddingHorizontal: 14, paddingVertical: 10 },
});

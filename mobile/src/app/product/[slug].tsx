import { useState } from "react";
import { ActivityIndicator, Image, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { Stack, useLocalSearchParams } from "expo-router";
import { useAddCartItem } from "../../features/cart/hooks";
import { useProductDetail } from "../../features/catalog/hooks";
import { colors } from "../../lib/theme";

export default function ProductDetailScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const { data: product, isLoading } = useProductDetail(slug);
  const addItem = useAddCartItem();
  const [variantId, setVariantId] = useState<string>("");
  const [quantity, setQuantity] = useState("1");

  if (isLoading) return <ActivityIndicator style={{ marginTop: 40 }} />;
  if (!product) return <Text style={styles.muted}>Product not found.</Text>;

  const mainImage = product.images?.[0];
  const variants = product.variants ?? [];
  const reviews = product.reviews ?? [];

  return (
    <ScrollView style={styles.container}>
      <Stack.Screen options={{ title: product.name, headerShown: true }} />
      {mainImage ? <Image source={{ uri: mainImage.url }} style={styles.image} /> : <View style={[styles.image, styles.placeholder]} />}
      <Text style={styles.title}>{product.name}</Text>
      <Text style={styles.price}>from ${product.base_price_usd}</Text>
      <Text style={styles.body}>{product.description}</Text>
      <Text style={styles.muted}>Origin: {product.country_of_origin} · Supplier: {product.supplier.name}</Text>

      {variants.length > 0 && (
        <View style={{ marginTop: 12 }}>
          <Text style={styles.label}>Variant</Text>
          {variants.map((v) => (
            <Pressable
              key={v.id}
              style={[styles.variantOption, variantId === v.id && styles.variantOptionSelected]}
              onPress={() => setVariantId(v.id)}
              disabled={v.stock_qty === 0}
            >
              <Text>{[v.length, v.color, v.texture].filter(Boolean).join(" / ") || v.sku}{v.stock_qty === 0 ? " (out of stock)" : ""}</Text>
            </Pressable>
          ))}
        </View>
      )}

      <Text style={styles.label}>Quantity</Text>
      <TextInput style={styles.input} keyboardType="number-pad" value={quantity} onChangeText={setQuantity} />

      <Pressable
        style={styles.addButton}
        onPress={() => addItem.mutate({ product_id: product.id, variant_id: variantId || null, quantity: Number(quantity) || 1 })}
      >
        <Text style={styles.addButtonText}>Add to cart</Text>
      </Pressable>
      {addItem.isSuccess && <Text style={styles.success}>Added to cart.</Text>}

      <Text style={styles.sectionTitle}>Reviews</Text>
      {reviews.length === 0 && <Text style={styles.muted}>No reviews yet.</Text>}
      {reviews.map((r) => (
        <View key={r.id} style={{ marginBottom: 8 }}>
          <Text style={{ fontWeight: "600" }}>{r.user_name} — {"★".repeat(r.rating)}</Text>
          <Text>{r.body}</Text>
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: colors.bg },
  image: { width: "100%", aspectRatio: 1, borderRadius: 10, backgroundColor: colors.border },
  placeholder: {},
  title: { fontSize: 20, fontWeight: "700", marginTop: 12, color: colors.ink },
  price: { color: colors.accent, fontWeight: "600", marginTop: 4 },
  body: { marginTop: 10, color: colors.ink },
  muted: { color: colors.muted, marginTop: 6 },
  label: { fontSize: 13, color: colors.muted, marginTop: 12 },
  input: { borderWidth: 1, borderColor: colors.border, borderRadius: 8, padding: 10, backgroundColor: colors.surface, marginTop: 4 },
  variantOption: { borderWidth: 1, borderColor: colors.border, borderRadius: 8, padding: 10, marginTop: 6 },
  variantOptionSelected: { borderColor: colors.accent, backgroundColor: "#f3e6db" },
  addButton: { backgroundColor: colors.accent, borderRadius: 999, padding: 14, alignItems: "center", marginTop: 16 },
  addButtonText: { color: "#fff", fontWeight: "600" },
  success: { color: "#2f7a3a", marginTop: 8 },
  sectionTitle: { fontSize: 16, fontWeight: "700", marginTop: 20, marginBottom: 8 },
});

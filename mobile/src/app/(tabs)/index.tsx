import { useState } from "react";
import { ActivityIndicator, FlatList, Image, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import { useAddCartItem } from "../../features/cart/hooks";
import { useProducts } from "../../features/catalog/hooks";
import { colors } from "../../lib/theme";

export default function ShopScreen() {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const { data, isLoading } = useProducts({ q: search || undefined });
  const addItem = useAddCartItem();

  return (
    <View style={styles.container}>
      <TextInput
        style={styles.search}
        placeholder="Search products..."
        value={search}
        onChangeText={setSearch}
      />
      {isLoading ? (
        <ActivityIndicator style={{ marginTop: 24 }} />
      ) : (
        <FlatList
          data={data?.items ?? []}
          keyExtractor={(item) => item.id}
          contentContainerStyle={{ gap: 12, paddingBottom: 24 }}
          ListEmptyComponent={<Text style={styles.muted}>No products match your search.</Text>}
          renderItem={({ item }) => (
            <Pressable style={styles.card} onPress={() => router.push(`/product/${item.slug}`)}>
              {item.image_url ? (
                <Image source={{ uri: item.image_url }} style={styles.image} />
              ) : (
                <View style={[styles.image, styles.placeholder]} />
              )}
              <View style={{ flex: 1 }}>
                <Text style={styles.name}>{item.name}</Text>
                <Text style={styles.price}>from ${item.base_price_usd}</Text>
                {item.average_rating != null && (
                  <Text style={styles.muted}>{"★".repeat(Math.round(item.average_rating))} ({item.review_count})</Text>
                )}
              </View>
              <Pressable style={styles.addButton} onPress={() => addItem.mutate({ product_id: item.id, quantity: 1 })}>
                <Text style={styles.addButtonText}>Add</Text>
              </Pressable>
            </Pressable>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: colors.bg },
  search: { borderWidth: 1, borderColor: colors.border, borderRadius: 8, padding: 10, backgroundColor: colors.surface, marginBottom: 12 },
  card: { flexDirection: "row", gap: 10, backgroundColor: colors.surface, borderRadius: 10, padding: 10, alignItems: "center", borderWidth: 1, borderColor: colors.border },
  image: { width: 56, height: 56, borderRadius: 8 },
  placeholder: { backgroundColor: colors.border },
  name: { fontWeight: "600", color: colors.ink },
  price: { color: colors.accent, fontWeight: "600" },
  muted: { color: colors.muted, fontSize: 12 },
  addButton: { backgroundColor: colors.accent, borderRadius: 999, paddingHorizontal: 14, paddingVertical: 8 },
  addButtonText: { color: "#fff", fontWeight: "600", fontSize: 12 },
});

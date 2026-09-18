import { useState } from "react";
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import { Redirect, useRouter } from "expo-router";
import { useAuth } from "../../lib/auth/AuthContext";
import { useMyOrders } from "../../features/orders/hooks";
import { colors } from "../../lib/theme";

export default function OrdersScreen() {
  const { isAuthenticated, initializing } = useAuth();
  const router = useRouter();
  const [page, setPage] = useState(1);
  const { data, isLoading } = useMyOrders(page);

  if (initializing) return null;
  if (!isAuthenticated) return <Redirect href="/login" />;

  if (isLoading) return <ActivityIndicator style={{ marginTop: 40 }} />;

  return (
    <View style={styles.container}>
      <FlatList
        data={data?.orders ?? []}
        keyExtractor={(o) => o.order_number}
        contentContainerStyle={{ gap: 8 }}
        ListEmptyComponent={<Text style={styles.muted}>You haven't placed any orders yet.</Text>}
        renderItem={({ item }) => (
          <Pressable style={styles.card} onPress={() => router.push(`/order/${item.order_number}`)}>
            <Text style={styles.orderNumber}>{item.order_number}</Text>
            <Text style={styles.badge}>{item.status.replaceAll("_", " ")}</Text>
            <Text>${item.total_amount_usd}</Text>
          </Pressable>
        )}
      />
      {data && data.total > data.page_size && (
        <View style={styles.pagination}>
          <Pressable disabled={page === 1} onPress={() => setPage((p) => p - 1)}><Text>Previous</Text></Pressable>
          <Text>Page {page}</Text>
          <Pressable disabled={page * data.page_size >= data.total} onPress={() => setPage((p) => p + 1)}><Text>Next</Text></Pressable>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: colors.bg },
  card: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", backgroundColor: colors.surface, borderRadius: 10, padding: 12, borderWidth: 1, borderColor: colors.border },
  orderNumber: { fontWeight: "600" },
  badge: { color: colors.accent, fontSize: 12 },
  muted: { color: colors.muted, marginTop: 20 },
  pagination: { flexDirection: "row", justifyContent: "space-between", marginTop: 12 },
});

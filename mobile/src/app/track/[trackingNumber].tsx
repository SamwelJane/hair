import { useQuery } from "@tanstack/react-query";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams } from "expo-router";
import { apiClient } from "../../lib/apiClient";
import { colors } from "../../lib/theme";

export default function TrackScreen() {
  const { trackingNumber } = useLocalSearchParams<{ trackingNumber: string }>();
  const { data: tracking, isLoading, isError } = useQuery({
    queryKey: ["tracking", trackingNumber],
    enabled: !!trackingNumber,
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/track/{tracking_number}", {
        params: { path: { tracking_number: trackingNumber! } },
      });
      if (error) throw error;
      return data;
    },
  });

  if (isLoading) return <ActivityIndicator style={{ marginTop: 40 }} />;
  if (isError || !tracking) return <Text style={styles.muted}>We couldn't find a shipment with that tracking number.</Text>;

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Tracking {tracking.tracking_number}</Text>
      <Text>Status: {tracking.status.replaceAll("_", " ")}</Text>
      {tracking.delivery_estimate && (
        <Text style={styles.muted}>
          Estimated delivery: {tracking.delivery_estimate.min_days}-{tracking.delivery_estimate.max_days} days from dispatch
        </Text>
      )}

      {tracking.packages.length > 1 && tracking.packages.map((p) => (
        <View key={p.package_code} style={styles.milestone}>
          <Text style={styles.milestoneLabel}>{p.package_code}</Text>
          <Text style={styles.muted}>{p.status.replaceAll("_", " ")}</Text>
        </View>
      ))}

      {tracking.events.map((e) => (
        <View key={e.id} style={styles.milestone}>
          <Text style={styles.milestoneLabel}>{e.label}</Text>
          <Text style={styles.muted}>{new Date(e.occurred_at).toLocaleString()} {e.location ?? ""}</Text>
        </View>
      ))}
      {tracking.events.length === 0 && <Text style={styles.muted}>No updates yet.</Text>}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: colors.bg },
  title: { fontSize: 18, fontWeight: "700", marginBottom: 8, color: colors.ink },
  muted: { color: colors.muted, marginTop: 4 },
  milestone: { marginTop: 12, paddingLeft: 10, borderLeftWidth: 2, borderLeftColor: colors.border },
  milestoneLabel: { fontWeight: "600" },
});

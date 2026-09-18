import { useState } from "react";
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Switch, Text, TextInput, View } from "react-native";
import { Redirect, useRouter } from "expo-router";
import { useAuth } from "../../lib/auth/AuthContext";
import { useAddresses, useCreateAddress, useDeactivateAccount, useDeleteAddress, useSetDefaultAddress } from "../../features/account/hooks";
import { colors } from "../../lib/theme";

export default function AccountScreen() {
  const { user, isAuthenticated, initializing, logout } = useAuth();
  const router = useRouter();
  const { data: addresses, isLoading } = useAddresses();
  const createAddress = useCreateAddress();
  const deleteAddress = useDeleteAddress();
  const setDefault = useSetDefaultAddress();
  const deactivate = useDeactivateAccount();

  const [fullName, setFullName] = useState("");
  const [line1, setLine1] = useState("");
  const [city, setCity] = useState("");
  const [countryCode, setCountryCode] = useState("");
  const [phone, setPhone] = useState("");
  const [isDefault, setIsDefault] = useState(false);

  if (initializing) return null;
  if (!isAuthenticated) return <Redirect href="/login" />;

  async function handleAdd() {
    await createAddress.mutateAsync({ full_name: fullName, line1, city, country_code: countryCode.toUpperCase(), phone, is_default: isDefault });
    setFullName(""); setLine1(""); setCity(""); setCountryCode(""); setPhone(""); setIsDefault(false);
  }

  function confirmDeactivate() {
    Alert.alert("Deactivate account", "Are you sure? This cannot be undone from the app.", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Deactivate", style: "destructive", onPress: async () => {
          await deactivate.mutateAsync();
          await logout();
          router.replace("/");
        },
      },
    ]);
  }

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>My Account</Text>
      <Text style={styles.muted}>Signed in as {user?.email}</Text>
      <Pressable style={styles.signOutButton} onPress={() => void logout()}>
        <Text style={styles.signOutText}>Log out</Text>
      </Pressable>

      <Text style={styles.sectionTitle}>Saved Addresses</Text>
      {isLoading ? <ActivityIndicator /> : (
        addresses?.map((a) => (
          <View key={a.id} style={styles.addressCard}>
            <Text style={{ fontWeight: "600" }}>{a.label || a.full_name} {a.is_default ? "(Default)" : ""}</Text>
            <Text style={styles.muted}>{a.full_name} · {a.line1}, {a.city}, {a.country_code} · {a.phone}</Text>
            <View style={styles.row}>
              {!a.is_default && (
                <Pressable onPress={() => setDefault.mutate(a.id)}><Text style={styles.link}>Set as default</Text></Pressable>
              )}
              <Pressable onPress={() => deleteAddress.mutate(a.id)}><Text style={[styles.link, { color: colors.danger }]}>Delete</Text></Pressable>
            </View>
          </View>
        ))
      )}
      {addresses?.length === 0 && <Text style={styles.muted}>No saved addresses yet.</Text>}

      <Text style={styles.sectionTitle}>Add Address</Text>
      <TextInput style={styles.input} placeholder="Full name" value={fullName} onChangeText={setFullName} />
      <TextInput style={styles.input} placeholder="Address line 1" value={line1} onChangeText={setLine1} />
      <TextInput style={styles.input} placeholder="City" value={city} onChangeText={setCity} />
      <TextInput style={styles.input} placeholder="Country code" maxLength={2} autoCapitalize="characters" value={countryCode} onChangeText={setCountryCode} />
      <TextInput style={styles.input} placeholder="Phone" value={phone} onChangeText={setPhone} />
      <View style={styles.row}>
        <Text>Set as default</Text>
        <Switch value={isDefault} onValueChange={setIsDefault} />
      </View>
      <Pressable style={styles.button} onPress={() => void handleAdd()} disabled={createAddress.isPending}>
        <Text style={styles.buttonText}>Save Address</Text>
      </Pressable>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Your Data</Text>
        <Pressable style={styles.dangerButton} onPress={confirmDeactivate}>
          <Text style={styles.dangerButtonText}>Deactivate My Account</Text>
        </Pressable>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: colors.bg },
  title: { fontSize: 20, fontWeight: "700", color: colors.ink },
  muted: { color: colors.muted, marginTop: 4 },
  signOutButton: { alignSelf: "flex-start", marginTop: 10 },
  signOutText: { color: colors.danger },
  sectionTitle: { fontSize: 16, fontWeight: "700", marginTop: 20, marginBottom: 8, color: colors.ink },
  addressCard: { backgroundColor: colors.surface, borderRadius: 8, padding: 10, borderWidth: 1, borderColor: colors.border, marginBottom: 8 },
  row: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginTop: 8 },
  link: { color: colors.accent },
  input: { borderWidth: 1, borderColor: colors.border, borderRadius: 8, padding: 10, backgroundColor: colors.surface, marginBottom: 8 },
  button: { backgroundColor: colors.accent, borderRadius: 999, padding: 12, alignItems: "center", marginTop: 8 },
  buttonText: { color: "#fff", fontWeight: "600" },
  section: { marginTop: 24, marginBottom: 40, borderTopWidth: 1, borderTopColor: colors.border, paddingTop: 16 },
  dangerButton: { borderWidth: 1, borderColor: colors.danger, borderRadius: 999, padding: 12, alignItems: "center" },
  dangerButtonText: { color: colors.danger, fontWeight: "600" },
});

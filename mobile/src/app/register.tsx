import { useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { Link, useRouter } from "expo-router";
import { AuthRequestError, useAuth } from "../lib/auth/AuthContext";
import { useMergeGuestCartOnLogin } from "../features/cart/hooks";
import { getGuestCartToken } from "../lib/cart/guestCartToken";
import { colors } from "../lib/theme";

export default function RegisterScreen() {
  const { register } = useAuth();
  const mergeCart = useMergeGuestCartOnLogin();
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit() {
    setError(null);
    setSubmitting(true);
    try {
      await register(name, email, password);
      if (await getGuestCartToken()) await mergeCart.mutateAsync().catch(() => undefined);
      router.replace("/account");
    } catch (err) {
      setError(err instanceof AuthRequestError ? err.message : "Registration failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Name</Text>
      <TextInput style={styles.input} value={name} onChangeText={setName} />
      <Text style={styles.label}>Email</Text>
      <TextInput style={styles.input} autoCapitalize="none" keyboardType="email-address" value={email} onChangeText={setEmail} />
      <Text style={styles.label}>Password</Text>
      <TextInput style={styles.input} secureTextEntry value={password} onChangeText={setPassword} />
      {error && <Text style={styles.error}>{error}</Text>}
      <Pressable style={styles.button} onPress={() => void handleSubmit()} disabled={submitting}>
        <Text style={styles.buttonText}>{submitting ? "Creating account..." : "Create account"}</Text>
      </Pressable>
      <Link href="/login" style={styles.link}>Already have an account? Log in</Link>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: colors.bg, gap: 6 },
  label: { fontSize: 13, color: colors.muted, marginTop: 10 },
  input: { borderWidth: 1, borderColor: colors.border, borderRadius: 8, padding: 10, backgroundColor: colors.surface },
  error: { color: colors.danger, marginTop: 8 },
  button: { backgroundColor: colors.accent, borderRadius: 999, padding: 14, alignItems: "center", marginTop: 16 },
  buttonText: { color: "#fff", fontWeight: "600" },
  link: { marginTop: 16, color: colors.accent, textAlign: "center" },
});

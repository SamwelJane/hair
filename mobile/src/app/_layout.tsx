import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "../lib/auth/AuthContext";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1 } },
});

export default function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <StatusBar style="auto" />
        <Stack screenOptions={{ headerShown: false }}>
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="login" options={{ headerShown: true, title: "Log in" }} />
          <Stack.Screen name="register" options={{ headerShown: true, title: "Create account" }} />
          <Stack.Screen name="checkout" options={{ headerShown: true, title: "Checkout" }} />
          <Stack.Screen
            name="checkout-confirmation/[orderNumber]"
            options={{ headerShown: true, title: "Order confirmed" }}
          />
          <Stack.Screen name="track/[trackingNumber]" options={{ headerShown: true, title: "Track order" }} />
        </Stack>
      </AuthProvider>
    </QueryClientProvider>
  );
}

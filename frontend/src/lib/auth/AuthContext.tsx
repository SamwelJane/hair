import { createContext, useContext, useEffect, useSyncExternalStore, type ReactNode } from "react";
import { apiClient } from "../apiClient";
import { tokenStore } from "./tokenStore";

interface AuthContextValue {
  user: ReturnType<typeof tokenStore.getState>["user"];
  accessToken: string | null;
  initializing: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const state = useSyncExternalStore(tokenStore.subscribe, tokenStore.getState);

  useEffect(() => {
    void tokenStore.initialize();
  }, []);

  const value: AuthContextValue = {
    user: state.user,
    accessToken: state.accessToken,
    initializing: state.initializing,
    isAuthenticated: state.accessToken !== null,
    async login(email, password) {
      const { data, error } = await apiClient.POST("/auth/login", { body: { email, password } });
      if (error) throw new AuthRequestError(error);
      tokenStore.applyTokenPair(data);
    },
    async register(name, email, password) {
      const { data, error } = await apiClient.POST("/auth/register", { body: { name, email, password } });
      if (error) throw new AuthRequestError(error);
      tokenStore.applyTokenPair(data);
    },
    async logout() {
      const refreshToken = tokenStore.getRefreshToken();
      if (refreshToken) {
        // Best-effort - a failed/offline revoke shouldn't block the client
        // from forgetting the session locally.
        await apiClient.POST("/auth/logout", { body: { refresh_token: refreshToken } }).catch(() => undefined);
      }
      tokenStore.clearSession();
    },
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export class AuthRequestError extends Error {
  detail: unknown;

  constructor(detail: unknown) {
    super(typeof detail === "object" && detail && "detail" in detail ? String((detail as { detail: unknown }).detail) : "Request failed");
    this.detail = detail;
  }
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

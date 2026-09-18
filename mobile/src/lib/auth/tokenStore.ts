// Mirrors frontend/src/lib/auth/tokenStore.ts, adapted for React Native:
// the access token still lives only in memory, but the refresh token is
// persisted via expo-secure-store (see ./tokenStorage.ts) instead of
// localStorage, and every persistence call is async as a result.
import type { components } from "@hiar-business/api-client";
import { clearRefreshToken, getRefreshToken as getStoredRefreshToken, saveRefreshToken } from "./tokenStorage";

type UserOut = components["schemas"]["UserOut"];
type TokenPair = components["schemas"]["TokenPair"];

export interface AuthState {
  accessToken: string | null;
  user: UserOut | null;
  initializing: boolean;
}

const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

let state: AuthState = { accessToken: null, user: null, initializing: true };
const listeners = new Set<() => void>();

function setState(partial: Partial<AuthState>): void {
  state = { ...state, ...partial };
  for (const listener of listeners) listener();
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function getState(): AuthState {
  return state;
}

async function applyTokenPair(pair: TokenPair): Promise<void> {
  await saveRefreshToken(pair.refresh_token);
  setState({ accessToken: pair.access_token, user: pair.user, initializing: false });
}

async function clearSession(): Promise<void> {
  await clearRefreshToken();
  setState({ accessToken: null, user: null, initializing: false });
}

let refreshPromise: Promise<string | null> | null = null;

// Deduplicated: concurrent 401s from several in-flight requests trigger only
// one /auth/refresh call, not one per request.
async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = await getStoredRefreshToken();
  if (!refreshToken) return null;

  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (!res.ok) {
          await clearSession();
          return null;
        }
        const pair = (await res.json()) as TokenPair;
        await applyTokenPair(pair);
        return pair.access_token;
      } catch {
        return null;
      } finally {
        refreshPromise = null;
      }
    })();
  }
  return refreshPromise;
}

async function initialize(): Promise<void> {
  const refreshToken = await getStoredRefreshToken();
  if (!refreshToken) {
    setState({ initializing: false });
    return;
  }
  await refreshAccessToken();
}

export const tokenStore = {
  subscribe,
  getState,
  applyTokenPair,
  clearSession,
  refreshAccessToken,
  initialize,
  getRefreshToken: getStoredRefreshToken,
  apiBaseUrl: API_BASE_URL,
};

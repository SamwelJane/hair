// Minimal external store (React 18+ useSyncExternalStore-compatible) holding
// the current session. The access token lives only in memory (this module),
// never persisted - only the refresh token goes to localStorage, so a page
// reload can silently re-establish a session without re-prompting for a
// password. See AGENTS.md/plan notes: this is a pragmatic SPA choice (no
// BFF/httpOnly-cookie layer in this pass), not the most XSS-hardened option.
import type { components } from "@hiar-business/api-client";

type UserOut = components["schemas"]["UserOut"];
type TokenPair = components["schemas"]["TokenPair"];

export interface AuthState {
  accessToken: string | null;
  user: UserOut | null;
  initializing: boolean;
}

const REFRESH_TOKEN_KEY = "hiar_refresh_token";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function getStoredRefreshToken(): string | null {
  try {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  } catch {
    return null;
  }
}

function setStoredRefreshToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(REFRESH_TOKEN_KEY, token);
    else localStorage.removeItem(REFRESH_TOKEN_KEY);
  } catch {
    // Private browsing / storage disabled - session just won't survive a reload.
  }
}

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

function applyTokenPair(pair: TokenPair): void {
  setStoredRefreshToken(pair.refresh_token);
  setState({ accessToken: pair.access_token, user: pair.user, initializing: false });
}

function clearSession(): void {
  setStoredRefreshToken(null);
  setState({ accessToken: null, user: null, initializing: false });
}

let refreshPromise: Promise<string | null> | null = null;

// Deduplicated: concurrent 401s from several in-flight requests trigger only
// one /auth/refresh call, not one per request.
async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getStoredRefreshToken();
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
          clearSession();
          return null;
        }
        const pair = (await res.json()) as TokenPair;
        applyTokenPair(pair);
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
  if (!getStoredRefreshToken()) {
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

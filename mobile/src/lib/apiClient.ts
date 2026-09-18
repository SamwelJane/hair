import { createApiClient } from "@hiar-business/api-client";
import { tokenStore } from "./auth/tokenStore";

export const apiClient = createApiClient(tokenStore.apiBaseUrl, () => tokenStore.getState().accessToken);

// Same refresh-and-retry-once pattern as frontend/src/lib/apiClient.ts - see
// that file's comment for why this lives outside openapi-fetch's own
// middleware instead of trying to retry from onResponse directly.
apiClient.use({
  async onResponse({ request, response }) {
    if (response.status !== 401 || !tokenStore.getState().accessToken) {
      return response;
    }
    const newToken = await tokenStore.refreshAccessToken();
    if (!newToken) return response;

    const retryRequest = request.clone();
    retryRequest.headers.set("Authorization", `Bearer ${newToken}`);
    return fetch(retryRequest);
  },
});

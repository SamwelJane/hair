import { createApiClient } from "@hiar-business/api-client";
import { tokenStore } from "./auth/tokenStore";

export const apiClient = createApiClient(tokenStore.apiBaseUrl, () => tokenStore.getState().accessToken);

// openapi-fetch's own middleware onResponse can't retry a fetch (Requests
// aren't safely re-fetchable after the body is read in every runtime), so
// the refresh-and-retry-once dance is done here as a thin wrapper. Only
// applied to authenticated calls (api-client already omits the header when
// there's no token, so a 401 on an unauthenticated call is a real 401, not
// an expired-token signal - no retry loop risk there).
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

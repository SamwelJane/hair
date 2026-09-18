import createClient from "openapi-fetch";
import type { paths } from "./schema";

export function createApiClient(baseUrl: string, getAccessToken?: () => string | null) {
  const client = createClient<paths>({ baseUrl });

  client.use({
    onRequest({ request }) {
      const token = getAccessToken?.();
      if (token) {
        request.headers.set("Authorization", `Bearer ${token}`);
      }
      return request;
    },
  });

  return client;
}

export type { components, operations, paths } from "./schema";

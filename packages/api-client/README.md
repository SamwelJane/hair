# @hiar-business/api-client

Generated TypeScript types + a typed fetch client from the FastAPI backend's
OpenAPI schema (`backend`). Consumed identically by `frontend` and
`mobile` so request/response shapes never drift between the two clients.

Regenerate after any backend route change, with the API running locally:

```bash
npm run generate
```

`src/schema.ts` is generated output — do not hand-edit it. `src/index.ts`
exports a configured `openapi-fetch` client built from that schema.

# Hiar Business monorepo

This repo was originally a Next.js app; it has since been fully migrated to a
FastAPI backend + React web frontend + Expo mobile app. No Next.js code or
dependency remains anywhere in the tree — ignore any stale references to it
you may find in old comments or docs, and do not reintroduce it.

## Layout

- `backend/` — FastAPI + async SQLAlchemy 2.0 (asyncpg) + Alembic + arq
  (Redis-backed job queue). See `backend/README.md` for the internal
  `core/db/models/schemas/services/integrations/routers/worker` structure.
- `frontend/` — React 19 + Vite + react-router v8 + TanStack Query. Customer
  storefront, supplier portal, and admin dashboard, each as a role-gated
  route tree (see `frontend/src/routes/router.tsx`).
- `mobile/` — Expo (React Native, file-based routing via expo-router).
  Customer-only surface, mirrors a subset of `frontend`.
- `packages/api-client` — TypeScript client generated from the backend's
  live OpenAPI schema (`npm run generate` inside that package, with the API
  running locally). Regenerate after any backend router change before
  relying on new endpoints from `frontend`/`mobile`.
- `packages/shared-types` — hand-written shared enums/constants (roles,
  order status groupings) consumed by `frontend` and `mobile`.

There is no root-level workspace tool (no turborepo/pnpm-workspace) — each
app is installed and run independently (`npm ci` / `pip install -e ".[dev]"`
inside its own folder). Cross-package linking uses plain `file:../packages/*`
dependencies.

## Conventions

- Backend: async SQLAlchemy sessions throughout, Pydantic schemas per
  router, role/permission checks enforced server-side via the
  `require_roles(...)` / `require_admin` / `require_supplier` dependency
  pattern in `backend/app/core/deps.py` — never rely on frontend route
  guards alone. Every mutating admin/supplier/warehouse action should call
  `log_audit()` (`backend/app/services/audit.py`).
- Frontend: feature-folder pattern (`src/features/<area>/{hooks.ts, *Page.tsx}`),
  role-gated layouts (`RequireAuth roles={[...]}`) per portal
  (`StorefrontLayout`, `SupplierLayout`, `AdminLayout`, and any new ones).
- Do not duplicate existing pricing, auth, payment, order, notification,
  tracking, or admin logic — extend the existing service modules in
  `backend/app/services/` instead of writing a parallel implementation.

## Roadmap

This codebase is being evolved into a Vietnam → Kenya managed commerce and
fulfilment platform. See [`docs/VNKE_ROADMAP.md`](docs/VNKE_ROADMAP.md) for
the phased plan, current status, and the audit of which existing systems
each phase extends — read it before starting any related work.

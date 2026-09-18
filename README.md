# Hiar Business

A managed Vietnam → Kenya hair/wig commerce and fulfilment platform, built as
a small monorepo:

- [`backend/`](backend/README.md) — FastAPI + async SQLAlchemy + Alembic + arq
- [`frontend/`](frontend/) — React + Vite web app (storefront, supplier portal, admin dashboard)
- [`mobile/`](mobile/) — Expo (React Native) customer app
- [`packages/api-client`](packages/api-client/README.md) — OpenAPI-generated TypeScript client shared by `frontend`/`mobile`
- [`packages/shared-types`](packages/shared-types/) — shared enums/constants (roles, order status groupings)

See [`AGENTS.md`](AGENTS.md) for conventions and the current architecture.

## Local development

Start Postgres + Redis:

```bash
docker-compose up -d
```

Backend:

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate   # or source .venv/bin/activate on macOS/Linux
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Web frontend:

```bash
cd frontend
npm ci
npm run dev
```

Mobile app:

```bash
cd mobile
npm ci
npm start
```

Regenerate the API client after any backend route change (with the API
running locally):

```bash
cd packages/api-client
npm run generate
```

## Tests

```bash
cd backend && ruff check . && mypy app && pytest
cd frontend && npm run lint && npm run build && npx vitest run
cd mobile && npx tsc --noEmit
```

Each app also has its own path-filtered CI workflow under `.github/workflows/`.

## Deployment runbook

The backend needs **two** long-running processes, not one - it's easy to
deploy only the API and forget the second:

1. **API server**: `uvicorn app.main:app --host 0.0.0.0 --port 8000` (put a
   real ASGI process manager/multiple workers in front of this for
   production, e.g. `uvicorn ... --workers 4` or a gunicorn+uvicorn-worker
   setup - this repo doesn't prescribe one).
2. **arq worker**: `arq app.worker.worker.WorkerSettings`, run as its own
   persistent process (not a request-scoped or serverless job) against the
   same Redis instance as the API. If this isn't running, supplier
   notifications are silently enqueued to Redis and never sent - nothing
   surfaces an error for it, so this is the single easiest thing to forget
   when standing up a new environment.

Steps, in order, for a fresh environment:

1. Provision Postgres and Redis reachable from both processes above.
2. Set every variable in `backend/.env.example` for the real environment
   (`DATABASE_URL`, `REDIS_URL`, `JWT_SECRET` - generate a real secret, the
   shipped default is not secure - Cloudinary/Resend/Twilio/M-Pesa
   credentials, `FRONTEND_URL`, `CORS_ORIGINS`). Set `APP_ENV=production` -
   this also switches the default log level from DEBUG to INFO (see
   `app/core/logging.py`).
3. Run `alembic upgrade head` from `backend/` before starting either
   process. Both `alembic upgrade head` and `alembic downgrade base` have
   been verified to run cleanly end-to-end against a fresh database (see
   `docs/VNKE_ROADMAP.md` Phase 12).
4. Start the API server and the arq worker (step-by-step above).
5. Create the initial ADMIN account directly against the database (there is
   no self-service admin signup, by design), then use that account's
   **Admin → Users** page to create STAFF/SUPPLIER/WAREHOUSE/KENYA_OPS
   accounts as needed - all five non-customer roles are creatable there.
   `backend/scripts/seed_demo_data.py` is for local/demo environments only
   (fixed, published passwords) - never run it against production.
6. Build and deploy `frontend/` (`npm run build`, serve `dist/`) pointed at
   the API's real URL, and publish `mobile/` through Expo/EAS as normal for
   that project.
7. After deploying, regenerate `packages/api-client` against the *deployed*
   backend if its schema has changed since the last local generation, so
   `frontend`/`mobile` builds are compiled against the real, live contract.
8. Smoke-check `GET /health` (should return `{"status": "ok"}`), then walk
   one order end-to-end (checkout → warehouse receive → consolidate →
   customs clear) using a WAREHOUSE and a KENYA_OPS account, confirming a
   WhatsApp/email notification actually arrives at each step - this is the
   fastest way to catch a missing worker process or misconfigured
   Twilio/Resend credentials before a real customer does.

# Hiar Business API

FastAPI backend. See `/docs` (this repo's root) and `backend/app/` for structure:
`core/` config+security+RBAC deps, `db/` SQLAlchemy session, `models/` ORM models,
`schemas/` Pydantic schemas, `services/` business logic (pricing, orders, payments,
notifications), `integrations/` third-party clients, `routers/` HTTP endpoints,
`worker/` arq background jobs.

## Local dev

```bash
python -m venv .venv
.venv/Scripts/activate   # or source .venv/bin/activate on macOS/Linux
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Supplier notifications (new order / status change) go through an arq job
queue, not straight to Twilio/Resend - run the worker alongside the API or
those notifications just sit in Redis unsent:

```bash
arq app.worker.worker.WorkerSettings
```

See the root [`README.md`](../README.md#deployment-runbook) for the full
production deployment runbook.

## Tests

```bash
pytest
```

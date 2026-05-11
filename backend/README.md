# SECE Backend

FastAPI · SQLAlchemy 2.0 async · PostgreSQL 15 · Alembic · JWT + bcrypt

## Setup

```bash
# Install deps
uv sync

# Apply migrations (Postgres must be running)
uv run alembic upgrade head

# Seed initial admin
uv run python -m app.scripts.seed_admin

# Run dev server
uv run uvicorn app.main:app --reload
```

API: http://localhost:8000  
Swagger: http://localhost:8000/docs

## Tests

```bash
uv run pytest
```

## Env vars

Copy `.env.example` to `.env`:

| Variable | Description |
|---|---|
| `DATABASE_URL` | asyncpg DSN for PostgreSQL |
| `JWT_SECRET` | Secret for signing JWT tokens |
| `JWT_EXPIRE_MINUTES` | Token expiry (default 30) |
| `ADMIN_EMAIL` | Initial admin email (seed script) |
| `ADMIN_PASSWORD` | Initial admin password (seed script) |

## Architecture

```
app/
├── main.py          FastAPI app entry point
├── core/            Config, DB session, JWT/bcrypt, role deps
├── models/          SQLAlchemy 2.0 ORM models
├── schemas/         Pydantic v2 request/response schemas
├── repositories/    Async data access layer
├── services/        Business logic layer
├── api/v1/          FastAPI routers (one per domain)
├── scripts/         CLI utilities
└── tests/           pytest suite
```

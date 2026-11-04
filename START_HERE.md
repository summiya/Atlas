# Atlas Milestone 1: FastAPI + PostgreSQL + Docker Compose

This milestone provides **only** a bootable control-plane skeleton and **persisted non-secret S3 source registration**. There is no network connection to S3, ingestion job, worker, embedding model or search service yet.

## Run locally

Requires Docker Engine with Compose v2. Create a local database password file before starting. It is ignored by Git.

```bash
mkdir -p .secrets
python -c "import secrets,pathlib;pathlib.Path('.secrets/db_password').write_text(secrets.token_urlsafe(32), encoding='utf-8')"
docker compose up --build -d
docker compose ps
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

Interactive OpenAPI documentation: http://localhost:8000/docs

Register a source *configuration* (no S3 request is made):

```bash
curl -X POST http://localhost:8000/v1/sources \
  -H 'content-type: application/json' \
  -d '{"name":"Research","kind":"s3","config":{"bucket":"example-documents","prefix":"papers/","region":"us-east-1"}}'
curl http://localhost:8000/v1/sources
```

Stop without removing DB data: `docker compose down`. Remove demo data with `docker compose down -v`. Changing the secret file does **not** change the password of an existing PostgreSQL volume; reset the volume only when you intentionally want to discard local data.

## Why is the database connection not in app.py?

`backend/atlas/database.py` constructs a SQLAlchemy URL internally from host, port, name, user and password file. Only **non-secret** database settings are supplied via the Compose environment. The password is read from a Compose-mounted secret file. Neither a password nor a full database URL is hardcoded or placed in the API environment. Never log the connection URL or mount secrets into publicly accessible paths.

This is a **local development** setup, not production secret management. In production use a managed secret provider, restricted network connectivity and role-specific DB permissions.

## Endpoints

| Method | Path | Status |
|---|---|---|
| GET | `/health/live` | Available |
| GET | `/health/ready` | Checks DB connection |
| GET | `/v1/connectors` | Advertises S3 config contract only |
| POST | `/v1/sources` | Persists non-secret S3 scope |
| GET | `/v1/sources` | Lists configured sources |
| GET | `/v1/sources/{id}` | Gets configured source |

## Architecture boundaries

- FastAPI is the control plane; PostgreSQL owns source configuration metadata.
- `backend/atlas/database.py` owns the connection construction and session factory.
- `backend/atlas/connectors.py` defines `check`, `discover`, `fetch` and a typed `SourceItem`.
- S3 credentials are **not accepted** in source payloads. A secrets reference / IAM role design must be added before real connections.
- No background work is triggered by API calls.
- Schema is bootstrapped by SQLAlchemy `create_all`, **not versioned migrations**. Add Alembic before schema evolution or production deployments.
- **Development only:** no authentication, no multi-tenancy, and no TLS. Do not expose the API publicly.

## Tests

```bash
cd backend
python -m pip install -e '.[test]'
python -m pytest -q
```

The smoke test uses isolated SQLite to verify the API contract. PostgreSQL integration tests should be added next.

## Next milestone

Implement S3 identity/permission checks, bucket discovery with pagination and durable cursors, safe object reads and a first ingestion run model.

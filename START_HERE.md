# Atlas Milestone 1: FastAPI + PostgreSQL + Docker Compose

This milestone provides **only** a bootable control-plane skeleton and **persisted non-secret S3 source registration**. There is no network connection to S3, ingestion job, worker, embedding model or search service yet.

## Run locally

Requires Docker Engine with Compose v2.

```bash
cp .env.example .env
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

Stop without removing DB data: `docker compose down`. Remove demo data with `docker compose down -v`.

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
- `backend/atlas/connectors.py` defines `check`, `discover`, `fetch` and a typed `SourceItem` as the contract for later S3 implementation.
- S3 credentials are **not accepted** in source payloads. A secrets reference / IAM role design must be added before real source connections.
- No background work is triggered by API calls in this milestone.
- Schema is bootstrapped by SQLAlchemy `create_all`, **not versioned migrations**. Add Alembic migrations before schema evolution or production deployments.
- **Development only:** there is no authentication or multi-tenancy, no TLS, and the local DB password is for Compose use only. Do not expose this API publicly.

## Tests

```bash
cd backend
python -m pip install -e '.[test]'
python -m pytest -q
```

The smoke test uses an isolated SQLite database to verify the API contract. PostgreSQL integration tests should be added in the next milestone.

## Next milestone

Implement S3 identity/permission checks, bucket discovery with pagination and durable cursors, safe object reads, first ingestion run model, and real PostgreSQL integration tests. After that add extraction, chunking, embeddings and Milvus.

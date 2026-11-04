"""API contract smoke tests with SQLite isolated from PostgreSQL."""
import os

os.environ.setdefault("ATLAS_DATABASE_URL", "sqlite+pysqlite:///:memory:")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from atlas.app import Base, app, db_session


def test_register_and_read_s3_source():
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    def override_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[db_session] = override_db
    try:
        client = TestClient(app)
        assert client.get("/health/live").json() == {"status": "ok"}
        assert client.get("/health/ready").status_code == 200
        assert client.get("/v1/connectors").json()["supported"] == ["s3"]
        create = client.post("/v1/sources", json={"name": "Research", "kind": "s3", "config": {"bucket": "example-documents", "prefix": "papers/"}})
        assert create.status_code == 201, create.text
        source = create.json()
        assert source["status"] == "configured_not_connected"
        assert source["config"]["prefix"] == "papers/"
        assert client.get(f"/v1/sources/{source['id']}").json()["id"] == source["id"]
        assert len(client.get("/v1/sources").json()) == 1
        assert client.get("/v1/sources/missing").status_code == 404
        assert client.post("/v1/sources", json={"name": "Bad", "config": {"bucket": "x", "access_key": "forbidden"}}).status_code == 422
    finally:
        app.dependency_overrides.clear()
        engine.dispose()

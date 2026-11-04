"""FastAPI control plane for source registration; ingestion not yet implemented."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, String, create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from pydantic_settings import BaseSettings, SettingsConfigDict

from .connectors import S3SourceConfig


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ATLAS_", extra="ignore")
    database_url: str = "postgresql+psycopg://atlas:atlas@localhost:5432/atlas"


settings = Settings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    bucket: Mapped[str] = mapped_column(String(63), nullable=False)
    prefix: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    region: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    kind: str = Field(default="s3", pattern="^s3$")
    config: S3SourceConfig


class SourceRead(BaseModel):
    id: str
    name: str
    kind: str
    config: S3SourceConfig
    created_at: datetime
    status: str = "configured_not_connected"


def db_session():
    with SessionLocal() as session:
        yield session


def serialize_source(source: Source) -> SourceRead:
    return SourceRead(
        id=source.id, name=source.name, kind=source.kind,
        config=S3SourceConfig(bucket=source.bucket, prefix=source.prefix, region=source.region),
        created_at=source.created_at,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Bootstrap only. Replace create_all with Alembic migrations before production deployment.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Atlas API", version="0.1.0", lifespan=lifespan)


@app.get("/health/live")
def live():
    return {"status": "ok"}


@app.get("/health/ready")
def ready(session: Session = Depends(db_session)):
    session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "reachable"}


@app.get("/v1/connectors")
def connectors():
    return {"supported": ["s3"], "connections_implemented": []}


@app.post("/v1/sources", status_code=status.HTTP_201_CREATED, response_model=SourceRead)
def create_source(payload: SourceCreate, session: Session = Depends(db_session)):
    source = Source(
        id=str(uuid4()), name=payload.name, kind=payload.kind,
        bucket=payload.config.bucket, prefix=payload.config.prefix,
        region=payload.config.region, created_at=datetime.now(timezone.utc),
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    return serialize_source(source)


@app.get("/v1/sources", response_model=list[SourceRead])
def list_sources(session: Session = Depends(db_session)):
    records = session.scalars(select(Source).order_by(Source.created_at.desc())).all()
    return [serialize_source(source) for source in records]


@app.get("/v1/sources/{source_id}", response_model=SourceRead)
def get_source(source_id: str, session: Session = Depends(db_session)):
    source = session.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return serialize_source(source)

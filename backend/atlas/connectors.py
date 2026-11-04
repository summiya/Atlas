"""Connector contract; no external connections are performed in this milestone."""
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field


class S3SourceConfig(BaseModel):
    """Non-secret S3 scope; credentials will be referenced via a secrets provider."""
    model_config = ConfigDict(extra="forbid")
    bucket: str = Field(min_length=3, max_length=63, pattern=r"^[a-z0-9][a-z0-9.-]*[a-z0-9]$")
    prefix: str = Field(default="", max_length=1024)
    region: str = Field(default="us-east-1", min_length=1, max_length=40)


@dataclass(frozen=True)
class SourceItem:
    external_id: str
    version: str | None
    content_type: str | None
    size_bytes: int | None


class Connector(ABC):
    """Future read-only source adapter; implement discovery and pagination next."""
    kind: str

    @abstractmethod
    def check(self, config: S3SourceConfig) -> None:
        """Validate configured read access, raising a safe connector error."""

    @abstractmethod
    def discover(self, config: S3SourceConfig, cursor: str | None = None) -> Iterator[SourceItem]:
        """Yield identifiers and versions, supporting resumable enumeration."""

    @abstractmethod
    def fetch(self, config: S3SourceConfig, item: SourceItem) -> bytes:
        """Fetch bounded source bytes for a discovered object."""
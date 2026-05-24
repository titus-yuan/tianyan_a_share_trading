"""Abstract data source interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Tweet:
    """Normalized tweet representation across all sources."""
    tweet_id: int
    username: str
    content: str
    posted_at: datetime
    raw_url: str = ""
    source: str = "unknown"


@dataclass
class SourceHealth:
    """Health check result for a data source."""
    url: str
    alive: bool
    latency_ms: int
    error: str = ""


class BaseSource(ABC):
    """Interface that all data sources must implement."""

    @abstractmethod
    def fetch(
        self,
        username: str,
        since_id: int | None = None,
        limit: int = 20,
    ) -> list[Tweet]:
        """Fetch tweets for a username.

        Args:
            username: Twitter username (without @)
            since_id: Only fetch tweets with ID > since_id (for incremental)
            limit: Max tweets to return

        Returns:
            List of normalized Tweet objects (newest first)
        """
        ...

    @abstractmethod
    def health(self) -> SourceHealth:
        """Check if this source is operational."""
        ...

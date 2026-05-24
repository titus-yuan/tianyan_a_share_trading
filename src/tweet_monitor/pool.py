"""Nitter instance pool — health checks + rotation."""

import logging

from .db import get_alive_instances, update_instance_status
from .sources.nitter import NitterSource

logger = logging.getLogger(__name__)


class InstancePool:
    """Manages a pool of Nitter instances with automatic health checks."""

    def __init__(self):
        self._sources: list[NitterSource] = []
        self._refresh()

    def _refresh(self):
        """Load alive instances from DB."""
        instances = get_alive_instances()
        self._sources = [NitterSource(i["url"]) for i in instances]
        if not self._sources:
            logger.warning("No alive Nitter instances in DB!")

    def get_source(self) -> NitterSource | None:
        """Get the best (fastest) working Nitter source."""
        if not self._sources:
            self._refresh()
        return self._sources[0] if self._sources else None

    def check_all(self):
        """Run a full health check on all instances in DB. Updates status."""
        from .db import get_alive_instances
        # Get ALL instances (not just alive)
        import subprocess
        from .config import BOT_PC_HOST, BOT_PC_USER, BOT_PC_DB, BOT_PC_DB_USER

        def _ssh_exec(sql):
            env = (
                f"psql -U {BOT_PC_DB_USER} -d {BOT_PC_DB} "
                f"--no-psqlrc -At -c '{sql}'"
            )
            result = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes",
                 f"{BOT_PC_USER}@{BOT_PC_HOST}", env],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                return ""
            return result.stdout.strip()

        raw = _ssh_exec("SELECT url FROM nitter_instances ORDER BY url")
        urls = [u.strip() for u in raw.split("\n") if u.strip()] if raw else []

        for url in urls:
            source = NitterSource(url)
            health = source.health()
            update_instance_status(
                url,
                status="alive" if health.alive else "dead",
                latency_ms=health.latency_ms,
                error_msg=health.error,
            )
            logger.info(
                "Health check: %s → %s (%dms)",
                url,
                "alive" if health.alive else "dead",
                health.latency_ms,
            )

        self._refresh()
        logger.info(
            "Pool refreshed: %d alive instances", len(self._sources)
        )

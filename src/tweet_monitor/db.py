"""Database operations — dual mode: direct PG (web on Bot PC) and SSH PG (monitor on 九章)."""

import subprocess
from datetime import datetime

import psycopg2
import psycopg2.extras

from .config import (
    BOT_PC_HOST, BOT_PC_USER, BOT_PC_DB, BOT_PC_DB_USER,
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
)


def get_pg_conn():
    """Direct PostgreSQL connection (for web app running on Bot PC)."""
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD,
    )


# ── SSH-based helpers (for monitor running on 九章) ──────────────────

def _ssh_sql(sql: str) -> str:
    """Execute a single SQL statement on Bot PC PG via SSH. Returns stdout."""
    # Escape single quotes for shell: ' → '\''
    safe_sql = sql.replace("'", "'\\''")
    cmd = (
        f"ssh -o ConnectTimeout=10 -o BatchMode=yes "
        f"{BOT_PC_USER}@{BOT_PC_HOST} "
        f"\"psql -U {BOT_PC_DB_USER} -d {BOT_PC_DB} --no-psqlrc -At -c '{safe_sql}'\""
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"SSH SQL failed: {result.stderr.strip()}")
    return result.stdout.strip()


def insert_tweets(tweets: list[dict]) -> int:
    """Insert new tweets via SSH (monitor mode). Skip duplicates."""
    if not tweets:
        return 0
    values = []
    for t in tweets:
        c = t["content"].replace("'", "''")
        dn = t.get("display_name", "").replace("'", "''")
        values.append(
            f"({t['tweet_id']}, '{t['username']}', '{c}', "
            f"'{t['posted_at']}', '{t.get('source', 'nitter')}', "
            f"'{t.get('raw_url', '')}', md5('{c}'), '{dn}')"
        )
    sql = (
        f"INSERT INTO tweets (tweet_id, username, content, posted_at, source, raw_url, content_hash, display_name) "
        f"VALUES {','.join(values)} "
        f"ON CONFLICT (username, tweet_id) DO NOTHING"
    )
    _ssh_sql(sql)
    return len(tweets)


def get_latest_tweet_id(username: str) -> int | None:
    """Get the most recent tweet_id for a username via SSH."""
    result = _ssh_sql(
        f"SELECT tweet_id FROM tweets WHERE username='{username}' ORDER BY tweet_id DESC LIMIT 1"
    )
    return int(result) if result else None


def insert_fetch_log(
    source_type: str, instance_url: str, username: str, mode: str,
    tweets_new: int, tweets_total: int, status: str = "ok",
    error_msg: str | None = None,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
):
    """Log a fetch operation via SSH."""
    err = error_msg.replace("'", "''") if error_msg else ""
    st = (started_at or datetime.now()).isoformat()
    ft = (finished_at or datetime.now()).isoformat()
    _ssh_sql(
        f"INSERT INTO fetch_log (source_type, instance_url, username, mode, tweets_new, tweets_total, "
        f"status, error_msg, started_at, finished_at) "
        f"VALUES ('{source_type}', '{instance_url}', '{username}', '{mode}', "
        f"{tweets_new}, {tweets_total}, '{status}', '{err}', '{st}', '{ft}')"
    )


def get_alive_instances() -> list[dict]:
    """Get alive Nitter instances via SSH."""
    result = _ssh_sql(
        "SELECT url, latency_ms FROM nitter_instances WHERE status='alive' ORDER BY latency_ms ASC NULLS LAST"
    )
    if not result:
        return []
    instances = []
    for line in result.split("\n"):
        if "|" in line:
            url, lat = line.split("|", 1)
            instances.append({"url": url, "latency_ms": int(lat) if lat else None})
    return instances


def update_instance_status(url: str, status: str, latency_ms: int | None = None, error_msg: str | None = None):
    """Update a Nitter instance's status via SSH."""
    err = error_msg.replace("'", "''") if error_msg else ""
    lat = f"{latency_ms}" if latency_ms is not None else "NULL"
    _ssh_sql(
        f"UPDATE nitter_instances SET status='{status}', latency_ms={lat}, "
        f"last_test=now(), error_msg='{err}' WHERE url='{url}'"
    )


def get_monitored_accounts(active_only: bool = True) -> list[str]:
    """Get list of monitored Twitter usernames via SSH."""
    where = "WHERE active=true" if active_only else ""
    result = _ssh_sql(f"SELECT username FROM monitored_accounts {where} ORDER BY username")
    if not result:
        return []
    return [line.strip() for line in result.split("\n") if line.strip()]

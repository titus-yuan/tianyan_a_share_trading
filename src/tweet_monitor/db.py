"""Database operations — dual mode: direct PG (web / monitor on Bot PC) and SSH PG (monitor on 九章)."""

import socket
import subprocess
from contextlib import contextmanager
from datetime import datetime

import psycopg2
import psycopg2.extras

from .config import (
    BOT_PC_HOST, BOT_PC_USER, BOT_PC_DB, BOT_PC_DB_USER,
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
)


def _is_bot_pc() -> bool:
    """Detect if we're running on the Bot PC itself (direct PG available)."""
    hostname = socket.gethostname()
    if "OptiPlex" in hostname:
        return True
    if DB_HOST in ("localhost", "127.0.0.1", "::1"):
        return True
    return False


def get_pg_conn():
    """Direct PostgreSQL connection (for anything running on Bot PC)."""
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD,
    )


@contextmanager
def _pg_cursor():
    """Context manager for a direct PG cursor (Bot PC mode)."""
    conn = get_pg_conn()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── SSH-based helpers (for monitor running on 九章) ──────────────────

def _ssh_sql(sql: str) -> str:
    """Execute a single SQL statement on Bot PC PG via SSH. Returns stdout."""
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


def _sql(sql: str) -> str:
    """Execute SQL — auto-choose direct PG or SSH based on host."""
    if _is_bot_pc():
        with _pg_cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            if not rows:
                return ""
            # Replicate psql -At output: tab-separated, one row per line
            return "\n".join("\t".join(str(c) for c in row) for row in rows)
    else:
        return _ssh_sql(sql)


def _sql_exec(sql: str) -> None:
    """Execute SQL that doesn't return rows (INSERT/UPDATE)."""
    if _is_bot_pc():
        with _pg_cursor() as cur:
            cur.execute(sql)
    else:
        _ssh_sql(sql)


# ── Public API ────────────────────────────────────────────────────────

def insert_tweets(tweets: list[dict]) -> int:
    """Insert new tweets. Skip duplicates."""
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
        f"INSERT INTO nitter_tweets (tweet_id, username, content, posted_at, source, raw_url, content_hash, display_name) "
        f"VALUES {','.join(values)} "
        f"ON CONFLICT (username, tweet_id) DO NOTHING"
    )
    _sql_exec(sql)
    return len(tweets)


def get_latest_tweet_id(username: str) -> int | None:
    """Get the most recent tweet_id for a username."""
    result = _sql(
        f"SELECT tweet_id FROM nitter_tweets WHERE username='{username}' ORDER BY tweet_id DESC LIMIT 1"
    )
    if not result:
        return None
    # Result is tab-separated; first field is the ID
    return int(result.split("\t")[0].strip())


def insert_fetch_log(
    source_type: str, instance_url: str, username: str, mode: str,
    tweets_new: int, tweets_total: int, status: str = "ok",
    error_msg: str | None = None,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
):
    """Log a fetch operation."""
    err = error_msg.replace("'", "''") if error_msg else ""
    st = (started_at or datetime.now()).isoformat()
    ft = (finished_at or datetime.now()).isoformat()
    _sql_exec(
        f"INSERT INTO nitter_fetch_log (source_type, instance_url, username, mode, tweets_new, tweets_total, "
        f"status, error_msg, started_at, finished_at) "
        f"VALUES ('{source_type}', '{instance_url}', '{username}', '{mode}', "
        f"{tweets_new}, {tweets_total}, '{status}', '{err}', '{st}', '{ft}')"
    )


def get_alive_instances() -> list[dict]:
    """Get alive Nitter instances."""
    result = _sql(
        "SELECT url, latency_ms FROM nitter_sources WHERE status='alive' ORDER BY latency_ms ASC NULLS LAST"
    )
    if not result:
        return []
    instances = []
    for line in result.split("\n"):
        line = line.strip()
        if "\t" in line:
            parts = line.split("\t", 1)
            url = parts[0]
            lat = parts[1] if len(parts) > 1 else None
            instances.append({"url": url, "latency_ms": int(lat) if lat and lat != "None" else None})
    return instances


def update_instance_status(url: str, status: str, latency_ms: int | None = None, error_msg: str | None = None):
    """Update a Nitter instance's status."""
    err = error_msg.replace("'", "''") if error_msg else ""
    lat = f"{latency_ms}" if latency_ms is not None else "NULL"
    _sql_exec(
        f"UPDATE nitter_instances SET status='{status}', latency_ms={lat}, "
        f"last_test=now(), error_msg='{err}' WHERE url='{url}'"
    )


def get_monitored_accounts(active_only: bool = True) -> list[str]:
    """Get list of monitored Twitter usernames."""
    where = "WHERE active=true" if active_only else ""
    result = _sql(f"SELECT username FROM nitter_accounts {where} ORDER BY username")
    if not result:
        return []
    return [line.strip() for line in result.split("\n") if line.strip()]

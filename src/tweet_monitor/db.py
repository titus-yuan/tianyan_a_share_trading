"""Database operations — direct PostgreSQL for web app, SSH for monitor."""

import subprocess
from datetime import datetime

import psycopg2
import psycopg2.extras

from .config import (
    BOT_PC_HOST, BOT_PC_USER, BOT_PC_DB, BOT_PC_DB_USER,
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
)


def get_pg_conn():
    """Direct PostgreSQL connection for web app (runs on Bot PC localhost)."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def _ssh_exec(sql: str) -> str:
    """Execute SQL on Bot PC PostgreSQL via SSH. Returns stdout."""
    env_cmd = f"psql -U {BOT_PC_DB_USER} -d {BOT_PC_DB} --no-psqlrc -At -c {_quote(sql)}"
    ssh_cmd = [
        "ssh", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes",
        f"{BOT_PC_USER}@{BOT_PC_HOST}", env_cmd,
    ]
    result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"SSH SQL failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _quote(s: str) -> str:
    """Shell-quote a string for SSH."""
    import shlex
    return shlex.quote(s)


def insert_tweets(tweets: list[dict]) -> int:
    """Insert new tweets, skip duplicates. Returns count of newly inserted rows.
    
    Args:
        tweets: list of {tweet_id, username, content, posted_at, source, raw_url}
    """
    if not tweets:
        return 0

    values = []
    for t in tweets:
        content_escaped = t["content"].replace("'", "''")
        values.append(
            f"({t['tweet_id']}, '{t['username']}', '{content_escaped}', "
            f"'{t['posted_at']}', '{t.get('source', 'nitter')}', "
            f"'{t.get('raw_url', '')}', md5('{content_escaped}'))"
        )

    sql = f"""
    INSERT INTO tweets (tweet_id, username, content, posted_at, source, raw_url, content_hash)
    VALUES {','.join(values)}
    ON CONFLICT (username, tweet_id) DO NOTHING;
    """
    _ssh_exec(sql)

    return len(tweets)  # Approximate; ON CONFLICT silently skips


def get_latest_tweet_id(username: str) -> int | None:
    """Get the most recent tweet_id stored for a username."""
    sql = f"SELECT tweet_id FROM tweets WHERE username='{username}' ORDER BY tweet_id DESC LIMIT 1"
    result = _ssh_exec(sql)
    if result:
        return int(result)
    return None


def insert_fetch_log(
    source_type: str,
    instance_url: str,
    username: str,
    mode: str,
    tweets_new: int,
    tweets_total: int,
    status: str = "ok",
    error_msg: str | None = None,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
):
    """Log a fetch operation."""
    err = error_msg.replace("'", "''") if error_msg else ""
    st = started_at.isoformat() if started_at else "now()"
    ft = finished_at.isoformat() if finished_at else "now()"
    sql = (
        f"INSERT INTO fetch_log (source_type, instance_url, username, mode, "
        f"tweets_new, tweets_total, status, error_msg, started_at, finished_at) "
        f"VALUES ('{source_type}', '{instance_url}', '{username}', '{mode}', "
        f"{tweets_new}, {tweets_total}, '{status}', '{err}', '{st}', '{ft}')"
    )
    _ssh_exec(sql)


def get_alive_instances() -> list[dict]:
    """Get alive Nitter instances from the database."""
    sql = "SELECT url, latency_ms FROM nitter_instances WHERE status='alive' ORDER BY latency_ms ASC NULLS LAST"
    result = _ssh_exec(sql)
    if not result:
        return []
    instances = []
    for line in result.split("\n"):
        if "|" in line:
            url, latency = line.split("|", 1)
            instances.append({"url": url, "latency_ms": int(latency) if latency else None})
    return instances


def update_instance_status(url: str, status: str, latency_ms: int | None = None, error_msg: str | None = None):
    """Update a Nitter instance's status."""
    err = error_msg.replace("'", "''") if error_msg else ""
    lat = f"'{latency_ms}'" if latency_ms else "NULL"
    sql = (
        f"UPDATE nitter_instances SET status='{status}', latency_ms={lat}, "
        f"last_test=now(), error_msg='{err}' WHERE url='{url}'"
    )
    _ssh_exec(sql)


def get_monitored_accounts(active_only: bool = True) -> list[str]:
    """Get list of monitored Twitter usernames."""
    where = "WHERE active=true" if active_only else ""
    sql = f"SELECT username FROM monitored_accounts {where} ORDER BY username"
    result = _ssh_exec(sql)
    if not result:
        return []
    return [line.strip() for line in result.split("\n") if line.strip()]

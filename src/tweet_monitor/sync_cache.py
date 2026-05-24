"""Sync tweets from Bot PC PostgreSQL to local SQLite cache.

Run this after each monitoring cycle to keep the web cache fresh.
Usage: python -m tweet_monitor.sync_cache
"""

import csv
import io
import sqlite3
import subprocess
import shlex
from datetime import datetime, timezone, timedelta

BJT = timezone(timedelta(hours=8))  # 北京时间 UTC+8
from pathlib import Path

from .config import BOT_PC_HOST, BOT_PC_USER, BOT_PC_DB, BOT_PC_DB_USER

CACHE_DIR = Path(__file__).parent.parent.parent / "cache"
CACHE_DB = CACHE_DIR / "tweets.db"


def _ssh_copy(sql: str) -> str:
    """Execute COPY TO STDOUT CSV on Bot PC PostgreSQL via SSH.
    Returns raw CSV text. Handles embedded newlines properly."""
    env_cmd = (
        f"psql -U {shlex.quote(BOT_PC_DB_USER)} "
        f"-d {shlex.quote(BOT_PC_DB)} "
        f"--no-psqlrc -At -c {shlex.quote(f'COPY ({sql}) TO STDOUT WITH CSV')}"
    )
    ssh_cmd = [
        "ssh", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes",
        f"{BOT_PC_USER}@{BOT_PC_HOST}", env_cmd,
    ]
    result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"SSH COPY failed: {result.stderr.strip()}")
    return result.stdout


def _init_cache(conn: sqlite3.Connection):
    """Create tables in SQLite if not exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tweets (
            id          INTEGER PRIMARY KEY,
            tweet_id    BIGINT NOT NULL,
            username    TEXT NOT NULL,
            content     TEXT NOT NULL,
            posted_at   TEXT,
            fetched_at  TEXT,
            source      TEXT,
            raw_url     TEXT,
            content_hash TEXT,
            UNIQUE(username, tweet_id)
        );
        CREATE INDEX IF NOT EXISTS idx_tweets_posted ON tweets(posted_at DESC);
        CREATE INDEX IF NOT EXISTS idx_tweets_username ON tweets(username);

        CREATE TABLE IF NOT EXISTS fetch_log (
            id           INTEGER PRIMARY KEY,
            source_type  TEXT,
            instance_url TEXT,
            username     TEXT,
            mode         TEXT,
            tweets_new   INTEGER,
            tweets_total INTEGER,
            status       TEXT,
            error_msg    TEXT,
            started_at   TEXT,
            finished_at  TEXT
        );

        CREATE TABLE IF NOT EXISTS sync_meta (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    conn.commit()


def sync_tweets(conn: sqlite3.Connection) -> int:
    """Pull latest tweets from PG via COPY CSV and insert into SQLite."""
    row = conn.execute(
        "SELECT value FROM sync_meta WHERE key='last_tweet_id'"
    ).fetchone()
    last_id = int(row[0]) if row else 0

    sql = (
        f"SELECT id, tweet_id, username, content, "
        f"COALESCE(posted_at::text,''), COALESCE(fetched_at::text,''), "
        f"COALESCE(source,''), COALESCE(raw_url,''), content_hash "
        f"FROM tweets WHERE id > {last_id} ORDER BY id ASC"
    )

    raw = _ssh_copy(sql)
    new_count = 0
    max_id = last_id

    if raw.strip():
        reader = csv.reader(io.StringIO(raw))

        for row_parts in reader:
            if len(row_parts) < 9:
                continue
            try:
                cur = conn.execute(
                    """INSERT OR IGNORE INTO tweets
                       (id, tweet_id, username, content, posted_at, fetched_at, source, raw_url, content_hash)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (int(row_parts[0]), int(row_parts[1]), row_parts[2], row_parts[3],
                     row_parts[4], row_parts[5], row_parts[6], row_parts[7], row_parts[8]),
                )
                if cur.rowcount:
                    new_count += 1
                    max_id = max(max_id, int(row_parts[0]))
            except (ValueError, sqlite3.IntegrityError):
                continue

    # Always update sync meta — even when no new tweets
    conn.execute(
        "INSERT OR REPLACE INTO sync_meta (key, value) VALUES ('last_tweet_id', ?)",
        (str(max_id),),
    )
    conn.execute(
        "INSERT OR REPLACE INTO sync_meta (key, value) VALUES ('last_sync', ?)",
        (datetime.now(BJT).strftime("%Y-%m-%d %H:%M:%S"),),
    )
    conn.commit()
    return new_count


def sync_fetch_log(conn: sqlite3.Connection) -> int:
    """Pull latest fetch_log entries from PG via COPY CSV."""
    sql = (
        "SELECT id, source_type, COALESCE(instance_url,''), username, mode, "
        "tweets_new, tweets_total, status, COALESCE(error_msg,''), "
        "COALESCE(started_at::text,''), COALESCE(finished_at::text,'') "
        "FROM fetch_log ORDER BY id DESC LIMIT 50"
    )

    raw = _ssh_copy(sql)
    if not raw.strip():
        return 0

    conn.execute("DELETE FROM fetch_log")
    reader = csv.reader(io.StringIO(raw))
    count = 0

    for row_parts in reader:
        if len(row_parts) < 10:
            continue
        try:
            conn.execute(
                """INSERT INTO fetch_log
                   (id, source_type, instance_url, username, mode,
                    tweets_new, tweets_total, status, error_msg, started_at, finished_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (int(row_parts[0]), row_parts[1], row_parts[2], row_parts[3],
                 row_parts[4], int(row_parts[5]), int(row_parts[6]),
                 row_parts[7], row_parts[8], row_parts[9], row_parts[10]),
            )
            count += 1
        except (ValueError, sqlite3.IntegrityError):
            continue

    conn.commit()
    return count


def main():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CACHE_DB))
    try:
        _init_cache(conn)
        n = sync_tweets(conn)
        m = sync_fetch_log(conn)
        print(f"Synced: {n} new tweets, {m} log entries")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

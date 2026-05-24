"""Tweet monitoring pipeline — fetch new tweets and store to PostgreSQL."""

import logging
import sys
from datetime import datetime, timezone

from . import config
from .db import (
    insert_tweets,
    insert_fetch_log,
    get_latest_tweet_id,
    get_monitored_accounts,
)
from .pool import InstancePool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def monitor_all() -> dict[str, int]:
    """Fetch new tweets for all monitored accounts. Returns {username: new_count}."""
    pool = InstancePool()
    source = pool.get_source()
    if not source:
        logger.error("No working Nitter instance available")
        return {}

    accounts = get_monitored_accounts(active_only=True)
    if not accounts:
        logger.warning("No monitored accounts configured")
        return {}

    results = {}
    for username in accounts:
        try:
            count = _monitor_one(username, source)
            results[username] = count
        except Exception as e:
            logger.error("Failed to monitor @%s: %s", username, e)
            results[username] = -1

    return results


def _monitor_one(username: str, source) -> int:
    """Monitor a single account. Returns number of new tweets."""
    started_at = datetime.now(timezone.utc)
    instance_url = source.instance_url

    # Get the highest tweet_id we've already stored
    since_id = get_latest_tweet_id(username)

    try:
        tweets = source.fetch(username, since_id=since_id)
    except Exception as e:
        insert_fetch_log(
            source_type="nitter",
            instance_url=instance_url,
            username=username,
            mode="monitor",
            tweets_new=0,
            tweets_total=0,
            status="failed",
            error_msg=str(e)[:500],
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
        )
        raise

    # Convert to dicts for DB insert
    tweet_dicts = []
    for t in tweets:
        tweet_dicts.append({
            "tweet_id": t.tweet_id,
            "username": t.username,
            "content": t.content,
            "posted_at": t.posted_at.isoformat() if t.posted_at else None,
            "source": t.source,
            "raw_url": t.raw_url,
        })

    new_count = 0
    if tweet_dicts:
        # All tweets from RSS are new (since_id filtered)
        new_count = insert_tweets(tweet_dicts)

    insert_fetch_log(
        source_type="nitter",
        instance_url=instance_url,
        username=username,
        mode="monitor",
        tweets_new=new_count,
        tweets_total=len(tweets),
        status="ok",
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
    )

    logger.info(
        "@%s: fetched %d, new %d | since_id=%s | %s",
        username, len(tweets), new_count, since_id, instance_url,
    )
    return new_count


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Tweet Monitor")
    parser.add_argument(
        "--username", "-u", type=str, help="Monitor a specific account (default: all active)",
    )
    parser.add_argument(
        "--health", action="store_true", help="Run health check on all Nitter instances",
    )
    args = parser.parse_args()

    if args.health:
        logger.info("Running health check...")
        pool = InstancePool()
        pool.check_all()
        return

    if args.username:
        logger.info("Monitoring @%s", args.username)
        pool = InstancePool()
        source = pool.get_source()
        if not source:
            logger.error("No working Nitter instance")
            sys.exit(1)
        new = _monitor_one(args.username, source)
        logger.info("Result: %d new tweets", new)
    else:
        logger.info("Monitoring all active accounts...")
        results = monitor_all()
        total = sum(max(0, v) for v in results.values())
        logger.info("Total: %d new tweets across %d accounts", total, len(results))

    # Sync local SQLite cache for web UI
    try:
        from .sync_cache import main as sync_main
        sync_main()
    except Exception as e:
        logger.warning("Cache sync failed: %s", e)


if __name__ == "__main__":
    main()

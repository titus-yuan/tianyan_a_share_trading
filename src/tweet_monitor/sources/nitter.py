"""Nitter RSS data source implementation."""

import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime

import httpx

from ..config import NITTER_UA, NITTER_TIMEOUT
from .base import BaseSource, Tweet, SourceHealth


class NitterSource(BaseSource):
    """Fetch tweets via Nitter RSS feeds."""

    def __init__(self, instance_url: str):
        self.instance_url = instance_url.rstrip("/")
        self._client = httpx.Client(
            timeout=NITTER_TIMEOUT,
            headers={"User-Agent": NITTER_UA},
            follow_redirects=False,
        )

    def fetch(
        self,
        username: str,
        since_id: int | None = None,
        limit: int = 20,
    ) -> list[Tweet]:
        """Fetch tweets from Nitter RSS. Returns newest-first.

        Note: Nitter RSS typically returns ~20 recent tweets.
        The `since_id` parameter is not supported by all instances;
        we filter client-side if needed.
        """
        url = f"{self.instance_url}/{username}/rss"
        resp = self._client.get(url)
        resp.raise_for_status()

        if not resp.text.strip():
            return []

        try:
            root = ET.fromstring(resp.text)
        except ET.ParseError:
            return []

        tweets = []
        for item in root.findall(".//item"):
            link_el = item.find("link")
            pubdate_el = item.find("pubDate")
            title_el = item.find("title")

            if link_el is None or not link_el.text:
                continue

            # Extract tweet ID from link: /STOCK6688/status/123456789#m
            match = re.search(r"/status/(\d+)", link_el.text)
            if not match:
                continue
            tweet_id = int(match.group(1))

            # Skip if we've already seen this (client-side filter)
            if since_id and tweet_id <= since_id:
                continue

            # Parse date
            posted_at = None
            if pubdate_el is not None and pubdate_el.text:
                try:
                    posted_at = datetime.strptime(
                        pubdate_el.text, "%a, %d %b %Y %H:%M:%S %Z"
                    )
                except ValueError:
                    posted_at = datetime.utcnow()

            # Content from title (RSS title = tweet text)
            content = title_el.text if title_el is not None and title_el.text else ""

            if not content:
                continue

            tweets.append(
                Tweet(
                    tweet_id=tweet_id,
                    username=username,
                    content=content.strip(),
                    posted_at=posted_at or datetime.utcnow(),
                    raw_url=link_el.text,
                    source="nitter",
                )
            )

            if len(tweets) >= limit:
                break

        return tweets

    def health(self) -> SourceHealth:
        """Test if the Nitter instance is reachable and serving RSS."""
        t0 = time.monotonic()
        try:
            resp = self._client.get(f"{self.instance_url}/STOCK6688/rss")
            latency = int((time.monotonic() - t0) * 1000)
            if resp.status_code == 200 and len(resp.text) > 0:
                return SourceHealth(
                    url=self.instance_url, alive=True, latency_ms=latency
                )
            return SourceHealth(
                url=self.instance_url,
                alive=False,
                latency_ms=latency,
                error=f"HTTP {resp.status_code}, {len(resp.text)} bytes",
            )
        except Exception as e:
            latency = int((time.monotonic() - t0) * 1000)
            return SourceHealth(
                url=self.instance_url,
                alive=False,
                latency_ms=latency,
                error=str(e)[:200],
            )

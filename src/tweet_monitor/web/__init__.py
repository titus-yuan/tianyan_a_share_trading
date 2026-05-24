"""Flask web app for viewing monitored tweets."""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

from flask import Flask, g, render_template, request, jsonify

CACHE_DB = Path(__file__).parent.parent.parent.parent / "cache" / "tweets.db"
PER_PAGE = 30

app = Flask(__name__)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(str(CACHE_DB))
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db:
        db.close()


# ── Routes ────────────────────────────────────────────────


@app.route("/")
def index():
    """Main page — tweet timeline."""
    db = get_db()

    # Summary stats
    stats = {}
    row = db.execute(
        "SELECT COUNT(*) as total FROM tweets"
    ).fetchone()
    stats["total"] = row["total"]

    row = db.execute(
        "SELECT COUNT(*) as cnt FROM tweets WHERE posted_at >= date('now')"
    ).fetchone()
    stats["today"] = row["cnt"]

    row = db.execute(
        "SELECT value FROM sync_meta WHERE key='last_sync'"
    ).fetchone()
    stats["last_sync"] = row["value"] if row else "—"

    row = db.execute(
        "SELECT MAX(posted_at) as latest FROM tweets"
    ).fetchone()
    stats["latest"] = row["latest"] if row else "—"

    # Last fetch log status
    row = db.execute(
        "SELECT * FROM fetch_log ORDER BY started_at DESC LIMIT 1"
    ).fetchone()
    last_log = dict(row) if row else None

    # Tweets — page 1
    page = request.args.get("page", 1, type=int)
    offset = (page - 1) * PER_PAGE

    tweets = db.execute(
        "SELECT * FROM tweets ORDER BY posted_at DESC LIMIT ? OFFSET ?",
        (PER_PAGE, offset),
    ).fetchall()

    total = stats["total"]
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)

    return render_template(
        "index.html",
        stats=stats,
        last_log=last_log,
        tweets=tweets,
        page=page,
        total_pages=total_pages,
        per_page=PER_PAGE,
    )


@app.route("/tweets")
def tweets_page():
    """HTMX partial — load a page of tweets."""
    db = get_db()

    page = request.args.get("page", 1, type=int)
    offset = (page - 1) * PER_PAGE

    tweets = db.execute(
        "SELECT * FROM tweets ORDER BY posted_at DESC LIMIT ? OFFSET ?",
        (PER_PAGE, offset),
    ).fetchall()

    total = db.execute("SELECT COUNT(*) as cnt FROM tweets").fetchone()["cnt"]
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)

    return render_template(
        "_tweet_list.html",
        tweets=tweets,
        page=page,
        total_pages=total_pages,
        per_page=PER_PAGE,
    )


@app.route("/search")
def search():
    """Search tweets by keyword."""
    db = get_db()
    q = request.args.get("q", "").strip()

    if not q:
        return tweets_page()

    page = request.args.get("page", 1, type=int)
    offset = (page - 1) * PER_PAGE

    like = f"%{q}%"
    count = db.execute(
        "SELECT COUNT(*) as cnt FROM tweets WHERE content LIKE ?",
        (like,),
    ).fetchone()["cnt"]

    tweets = db.execute(
        "SELECT * FROM tweets WHERE content LIKE ? ORDER BY posted_at DESC LIMIT ? OFFSET ?",
        (like, PER_PAGE, offset),
    ).fetchall()

    total_pages = max(1, (count + PER_PAGE - 1) // PER_PAGE)

    return render_template(
        "_tweet_list.html",
        tweets=tweets,
        page=page,
        total_pages=total_pages,
        per_page=PER_PAGE,
        search_query=q,
    )


@app.route("/api/refresh")
def api_refresh():
    """Trigger cache sync and return JSON status."""
    import subprocess
    import sys

    try:
        result = subprocess.run(
            [sys.executable, "-m", "tweet_monitor.sync_cache"],
            capture_output=True, text=True, timeout=60,
            cwd=str(Path(__file__).parent.parent.parent.parent),
        )
        return jsonify({
            "ok": result.returncode == 0,
            "output": result.stdout.strip() or result.stderr.strip(),
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ── Main ──────────────────────────────────────────────────


def launch(host="0.0.0.0", port=5500):
    """Launch the web server."""
    print(f"📊 Tweet Monitor → http://{host}:{port}")
    app.run(host=host, port=port, debug=False)

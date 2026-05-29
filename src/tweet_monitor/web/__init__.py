"""天演 Tianyan — Flask web app, direct PostgreSQL (warm beige theme)."""

from datetime import datetime

import psycopg2
import psycopg2.extras
from flask import Flask, g, render_template, request, jsonify

from ..db import get_pg_conn

from .dashboard import init_dashboard

PER_PAGE = 20
app = Flask(__name__)


@app.template_filter("bjt")
def bjt_filter(value):
    """Format a datetime/timestamp as Beijing time: MM-DD HH:MM"""
    if not value:
        return "—"
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return value[:16] if len(value) >= 16 else value
    return value.strftime("%Y-%m-%d %H:%M")


def get_db():
    if "db" not in g:
        conn = get_pg_conn()
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db:
        db.close()


# ── Routes ─────────────────────────────────────────────────


@app.route("/")
def index():
    """Main page — 3-column layout."""
    db = get_db()
    cur = db.cursor()

    # Stats
    cur.execute("SELECT COUNT(*) as total FROM nitter_tweets")
    stats = {"total": cur.fetchone()["total"]}

    cur.execute(
        "SELECT COUNT(*) as cnt FROM nitter_tweets WHERE posted_at >= current_date"
    )
    stats["today"] = cur.fetchone()["cnt"]

    cur.execute("SELECT MAX(posted_at) as latest FROM nitter_tweets")
    row = cur.fetchone()
    stats["latest"] = row["latest"].strftime("%Y-%m-%d %H:%M:%S") if row and row["latest"] else "—"

    cur.execute("SELECT COUNT(*) as cnt FROM nitter_accounts WHERE active=true")
    stats["accounts"] = cur.fetchone()["cnt"]

    cur.execute(
        "SELECT MAX(started_at) as last_sync FROM nitter_fetch_log WHERE status='ok'"
    )
    row = cur.fetchone()
    stats["last_sync"] = (
        row["last_sync"].strftime("%Y-%m-%d %H:%M:%S")
        if row and row["last_sync"] else "—"
    )

    # Tweets — page 1
    page = request.args.get("page", 1, type=int)
    offset = (page - 1) * PER_PAGE

    cur.execute(
        "SELECT * FROM nitter_tweets ORDER BY posted_at DESC LIMIT %s OFFSET %s",
        (PER_PAGE, offset),
    )
    tweets = cur.fetchall()

    total_pages = max(1, (stats["total"] + PER_PAGE - 1) // PER_PAGE)

    return render_template(
        "index.html",
        stats=stats,
        tweets=tweets,
        page=page,
        total_pages=total_pages,
        per_page=PER_PAGE,
    )


@app.route("/tweets")
def tweets_page():
    """HTMX partial — tweet list page."""
    db = get_db()
    cur = db.cursor()
    page = request.args.get("page", 1, type=int)
    offset = (page - 1) * PER_PAGE

    cur.execute(
        "SELECT * FROM nitter_tweets ORDER BY posted_at DESC LIMIT %s OFFSET %s",
        (PER_PAGE, offset),
    )
    tweets = cur.fetchall()

    cur.execute("SELECT COUNT(*) as cnt FROM nitter_tweets")
    total = cur.fetchone()["cnt"]
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
    """HTMX partial — search results."""
    db = get_db()
    cur = db.cursor()
    q = request.args.get("q", "").strip()
    if not q:
        return tweets_page()

    page = request.args.get("page", 1, type=int)
    offset = (page - 1) * PER_PAGE
    like = f"%{q}%"

    cur.execute("SELECT COUNT(*) as cnt FROM nitter_tweets WHERE content LIKE %s", (like,))
    count = cur.fetchone()["cnt"]

    cur.execute(
        "SELECT * FROM nitter_tweets WHERE content LIKE %s ORDER BY posted_at DESC LIMIT %s OFFSET %s",
        (like, PER_PAGE, offset),
    )
    tweets = cur.fetchall()

    total_pages = max(1, (count + PER_PAGE - 1) // PER_PAGE)

    return render_template(
        "_tweet_list.html",
        tweets=tweets,
        page=page,
        total_pages=total_pages,
        per_page=PER_PAGE,
        search_query=q,
    )


@app.route("/api/tweet/<int:tweet_id>")
def tweet_detail(tweet_id):
    """JSON API — return full tweet for detail panel."""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM nitter_tweets WHERE id = %s", (tweet_id,))
    row = cur.fetchone()
    if not row:
        return jsonify({"error": "not found"}), 404

    return jsonify({
        "id": row["id"],
        "tweet_id": row["tweet_id"],
        "username": row["username"],
        "display_name": row.get("display_name", ""),
        "content": row["content"],
        "posted_at": row["posted_at"].isoformat() if row["posted_at"] else None,
        "source": row["source"],
        "raw_url": row["raw_url"],
    })


@app.route("/api/refresh")
def api_refresh():
    """Trigger tweet fetch + return status."""
    import subprocess
    import sys
    from pathlib import Path

    try:
        result = subprocess.run(
            [sys.executable, "-m", "tweet_monitor.monitor"],
            capture_output=True, text=True, timeout=60,
            cwd=str(Path(__file__).parent.parent.parent.parent),
        )
        return jsonify({
            "ok": result.returncode == 0,
            "output": result.stdout.strip() or result.stderr.strip(),
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ── Account Management ────────────────────────────────────


@app.route("/api/accounts", methods=["GET"])
def api_accounts_list():
    """JSON API — list all monitored accounts."""
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "SELECT id, username, display_name, active, created_at "
        "FROM nitter_accounts ORDER BY username"
    )
    rows = cur.fetchall()
    accounts = []
    for r in rows:
        accounts.append({
            "id": r["id"],
            "username": r["username"],
            "display_name": r.get("display_name", ""),
            "active": r["active"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        })
    return jsonify({"accounts": accounts})


@app.route("/api/accounts", methods=["POST"])
def api_accounts_add():
    """JSON API — add a new monitored account."""
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip().lstrip("@")
    display_name = (data.get("display_name") or "").strip()

    if not username:
        return jsonify({"ok": False, "error": "username 不能为空"}), 400

    db = get_db()
    cur = db.cursor()
    try:
        cur.execute(
            "INSERT INTO monitored_accounts (username, display_name) "
            "VALUES (%s, %s) "
            "ON CONFLICT (username) DO UPDATE SET active=true, display_name=EXCLUDED.display_name "
            "RETURNING id, username, display_name, active",
            (username, display_name),
        )
        row = cur.fetchone()
        db.commit()
        return jsonify({
            "ok": True,
            "account": {
                "id": row["id"],
                "username": row["username"],
                "display_name": row.get("display_name", ""),
                "active": row["active"],
            },
        })
    except Exception as e:
        db.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/accounts/<username>", methods=["PATCH"])
def api_accounts_toggle(username):
    """JSON API — toggle active status of a monitored account."""
    data = request.get_json(silent=True) or {}
    active = data.get("active", None)
    if active is None:
        # Toggle
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "SELECT active FROM nitter_accounts WHERE username=%s",
            (username,),
        )
        row = cur.fetchone()
        if not row:
            return jsonify({"ok": False, "error": "未找到该推主"}), 404
        active = not row["active"]

    db = get_db()
    cur = db.cursor()
    cur.execute(
        "UPDATE monitored_accounts SET active=%s WHERE username=%s",
        (active, username),
    )
    db.commit()
    return jsonify({"ok": True, "username": username, "active": active})


# ── Main ───────────────────────────────────────────────────


def launch(host="0.0.0.0", port=5500):
    """Launch the web server."""
    init_dashboard(app)
    print(f"📊 天演 Tianyan → http://{host}:{port}")
    print(f"📊 Dash 仪表盘  → http://{host}:{port}/dashboard/")
    app.run(host=host, port=port, debug=False)

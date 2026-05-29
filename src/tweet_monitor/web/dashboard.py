"""天演 Tianyan — Dash 仪表盘蓝图 (嵌入 Flask :5500/dashboard/)"""

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Dash, dcc, html, Input, Output
from flask import Blueprint

from ..db import get_pg_conn


# ── 数据查询 ─────────────────────────────────────────────────


def get_tweet_stats():
    """获取推文统计数据"""
    conn = get_pg_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM nitter_tweets")
    total = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM nitter_tweets WHERE posted_at >= current_date"
    )
    today = cur.fetchone()[0]

    cur.execute("SELECT MAX(posted_at) FROM nitter_tweets")
    row = cur.fetchone()
    latest = row[0].strftime("%m-%d %H:%M") if row and row[0] else "—"

    # 各推主推文数
    cur.execute("""
        SELECT username, COUNT(*) as cnt
        FROM nitter_tweets
        GROUP BY username
        ORDER BY cnt DESC
    """)
    by_user = [{"username": r[0], "count": r[1]} for r in cur.fetchall()]

    conn.close()
    return {"total": total, "today": today, "latest": latest, "by_user": by_user}


def get_daily_bars(symbol="000001", limit=60):
    """获取个股日线数据"""
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT trade_date, open, high, low, close, volume "
        "FROM daily_klines WHERE stock_code=%s AND trade_date > '2026-04-01' "
        "ORDER BY trade_date DESC LIMIT %s",
        (symbol, limit),
    )
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=["trade_date", "open", "high", "low", "close", "volume"])
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    return df.sort_values("trade_date")


from flask import Blueprint


def create_dash(flask_app):
    """创建 Dash 应用,挂载到 Flask 的 /dashboard/ 路径"""
    dash_app = Dash(
        name="tianyan_dashboard",
        server=flask_app,
        url_base_pathname="/dashboard/",
        external_stylesheets=[dbc.themes.FLATLY],
        suppress_callback_exceptions=True,
    )

    dash_app.title = "天演仪表盘"

    dash_app.layout = dbc.Container(
        [
            html.H2("📊 天演仪表盘", className="my-4"),
            dbc.Row(
                [
                    dbc.Col(dbc.Card([dbc.CardBody([
                        html.H6("总推文", className="card-subtitle text-muted"),
                        html.H3(id="stat-total", className="card-title"),
                    ])]), md=3),
                    dbc.Col(dbc.Card([dbc.CardBody([
                        html.H6("今日新增", className="card-subtitle text-muted"),
                        html.H3(id="stat-today", className="card-title text-success"),
                    ])]), md=3),
                    dbc.Col(dbc.Card([dbc.CardBody([
                        html.H6("最新推文时间", className="card-subtitle text-muted"),
                        html.H5(id="stat-latest", className="card-title"),
                    ])]), md=3),
                    dbc.Col(dbc.Card([dbc.CardBody([
                        html.H6("同步状态", className="card-subtitle text-muted"),
                        html.H5("正常 ✅", className="card-title text-success"),
                    ])]), md=3),
                ],
                className="mb-4",
            ),
            dbc.Row(
                [
                    dbc.Col([
                        html.H5("📈 K线 (000001 平安银行)"),
                        dcc.Graph(id="kline-chart"),
                    ], md=8),
                    dbc.Col([
                        html.H5("👤 推文来源分布"),
                        dcc.Graph(id="tweet-pie"),
                    ], md=4),
                ]
            ),
        ],
        fluid=True,
    )

    # 回调：刷新统计卡片
    @dash_app.callback(
        [Output("stat-total", "children"),
         Output("stat-today", "children"),
         Output("stat-latest", "children")],
        Input("kline-chart", "id"),  # 页面加载时触发
    )
    def update_stats(_):
        stats = get_tweet_stats()
        return str(stats["total"]), str(stats["today"]), stats["latest"]

    # 回调：K线图
    @dash_app.callback(
        Output("kline-chart", "figure"),
        Input("kline-chart", "id"),
    )
    def update_kline(_):
        df = get_daily_bars("000001", 30)
        if df.empty:
            return {"data": [], "layout": {"title": "暂无数据"}}

        import plotly.graph_objects as go
        fig = go.Figure(data=[
            go.Candlestick(
                x=df["trade_date"],
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                name="000001",
            )
        ])
        fig.update_layout(
            template="plotly_white",
            height=400,
            margin=dict(l=20, r=20, t=10, b=20),
            xaxis_rangeslider_visible=False,
        )
        return fig

    # 回调：推文饼图
    @dash_app.callback(
        Output("tweet-pie", "figure"),
        Input("tweet-pie", "id"),
    )
    def update_pie(_):
        stats = get_tweet_stats()
        if not stats["by_user"]:
            return {"data": [], "layout": {"title": "暂无数据"}}

        import plotly.express as px
        fig = px.pie(
            names=[u["username"] for u in stats["by_user"]],
            values=[u["count"] for u in stats["by_user"]],
            height=400,
            template="plotly_white",
        )
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        return fig

    return dash_app


# ── Flask Blueprint ──────────────────────────────────────────

dashboard_bp = Blueprint("dashboard_bp", __name__)

# Dash 实例延迟初始化,等 Flask app 起来后再创建
_dash = None


def init_dashboard(flask_app):
    """在 Flask app 创建后调用,初始化 Dash"""
    global _dash
    _dash = create_dash(flask_app)
    return _dash

#!/usr/bin/env python3
"""
=============================================================================
 fetch_today_daily_kline_baostock_v1.2.py
=============================================================================

 脚本用途 (Purpose):
   采集沪深两市 A 股的「当日日线数据」并写入 PostgreSQL (Stocks_China_A)。
   - 数据源: Baostock, adjustflag="2"（前复权，唯一可靠值）
   - 覆盖范围: 沪深全部在市股票（sh.* / sz.*），跳过北交所（Baostock 不支持）
   - 入库表: daily_klines, source='baostock', adjustment='qfq'
   - 执行时机: A股收盘后 15:30（Baostock 盘后才更新当日K线）
   - 防重复: ON CONFLICT DO NOTHING（同一天同源同复权不重复插入）
   - 交易日校验: 优先查本地 trade_calendar 表，无数据时 fallback 到 Baostock API

 脚本命名解析 (Name Breakdown):
   fetch               = 采集 / 拉取
   today               = 当日（当天收盘数据）
   daily               = 日线（日级别K线，区别于周线/月线/分钟线）
   kline               = K线数据（OHLCV: Open/High/Low/Close/Volume）
   baostock            = 数据源（Baostock，无IP限制，调整价可靠）
   v1.2                = 版本号

 变更记录 (Changelog):
   v1.0 (2026-05-15)   初始版本，替代旧版 fetch_today_klines.py（AKShare/东方财富版）
                       由于东方财富全产品线限流，改用 Baostock

   v1.1 (2026-05-15)   新增交易日校验功能
                       - 新增 is_trading_day() 函数，通过 Baostock query_trade_dates()
                         检查当日是否为 A 股交易日
                       - run() 开头加入交易日判断：非交易日打印 [SKIP] 并直接退出，
                         避免周末/节假日空跑 5203 只股票（节省 ~43 分钟无效运行）
                       - 已覆盖：周末（周六日）+ 法定假日（春节/国庆/五一/端午等）

   v1.2 (2026-05-15)   交易日校验改为「本地优先 + API 兜底」
                       - is_trading_day() 重构：优先查本地 trade_calendar 表（瞬间返回），
                         本地无数据时 fallback 到 Baostock query_trade_dates() API
                       - 依赖交易日历表 trade_calendar（由 fetch_trade_calendar_baostock_v1.0.py 维护）
                       - 表结构: trade_calendar(trade_date PK, is_open BOOL, week_day SMALLINT)
                       - 效果: 交易日判断从 ~100ms API 调用降到 <1ms 本地查询

   v1.3 (2026-05-19)   新增前置探测机制，解决 Baostock 发布时间差问题
                       - 新增 probe_data_available() 函数：采集前先用 sh.600000 探测
                         今日数据是否已发布，最多 3 轮，每轮间隔 15 分钟
                       - 探测到数据后正常采集；3 轮仍无数据则退出（等 18:30 Hermes 检查兜底）
                       - 避免 16:30 全量空跑 5203 只（如 5/19 的情况）

 调用方式:
   python -u fetch_today_daily_kline_baostock_v1.2.py

 依赖:
   - baostock, psycopg2, pyyaml, pandas
   - 配置文件: config.yaml（数据库连接信息）
   - 交易日历表: trade_calendar（需先执行 fetch_trade_calendar_baostock_v1.0.py）
=============================================================================
"""
import os, sys, time, yaml, psycopg2, random, logging, socket
from datetime import date
import baostock as bs

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.yaml")


def load_config():
    # 先尝试脚本同级目录，再尝试项目目录
    for d in [SCRIPT_DIR, "/mnt/data/code/a-share-collector"]:
        p = os.path.join(d, "config.yaml")
        if os.path.exists(p):
            CONFIG_PATH = p
            break
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def get_db_conn(cfg):
    return psycopg2.connect(**cfg["database"])


def is_trading_day(trade_date_str, conn=None):
    """
    判断是否为 A 股交易日（本地表优先，API 兜底）。

    查询优先级:
      1. 本地 trade_calendar 表 → 找到即返回（<1ms）
      2. Baostock query_trade_dates() API → 本地表没数据时兜底

    Args:
        trade_date_str: 日期字符串 'YYYY-MM-DD'
        conn:           psycopg2 数据库连接（可选，传入则优先查本地表）

    Returns:
        bool: True=交易日, False=非交易日（周末/法定假日）
    """
    # ── 优先查本地 trade_calendar 表 ──────────────────────────────────
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT is_open FROM trade_calendar WHERE trade_date = %s",
                (trade_date_str,)
            )
            row = cur.fetchone()
            cur.close()
            if row is not None:
                return row[0]  # 本地表命中
        except Exception:
            pass  # 表不存在或查询失败，fallback 到 API

    # ── Fallback: Baostock API ────────────────────────────────────────
    rs = bs.query_trade_dates(trade_date_str, trade_date_str)
    if rs.error_code != '0':
        return False
    while rs.next():
        row = rs.get_row_data()
        # row = [calendar_date, is_trading_day]
        # is_trading_day = '1' → 交易日, '0' → 非交易日
        return row[1] == '1'
    return False


def get_stock_codes(conn, exchange_filter=None):
    """exchange_filter: None=全部, 'SSE'=沪市, 'SZSE'=深市"""
    cur = conn.cursor()
    if exchange_filter:
        cur.execute(
            "SELECT stock_code FROM stocks WHERE is_valid = true AND exchange = %s ORDER BY stock_code",
            (exchange_filter,)
        )
    else:
        cur.execute("SELECT stock_code FROM stocks WHERE is_valid = true ORDER BY stock_code")
    codes = [r[0] for r in cur.fetchall()]
    cur.close()
    return codes


def get_max_trade_date(conn, stock_code, source, adjustment):
    cur = conn.cursor()
    cur.execute("""
        SELECT MAX(trade_date) FROM daily_klines
        WHERE stock_code = %s AND source = %s AND adjustment = %s
    """, (stock_code, source, adjustment))
    row = cur.fetchone()
    cur.close()
    return row[0] if row[0] else None


def fetch_today_baostock(conn, code):
    """用Baostock拉单只今日日线（前复权），返回df或None"""
    today = date.today().strftime("%Y-%m-%d")
    try:
        rs = bs.query_history_k_data_plus(
            code,
            "date,open,high,low,close,volume,amount,adjustflag",
            start_date=today,
            end_date=today,
            frequency="d",
            adjustflag="2"
        )
        rows = []
        while rs.next():
            rows.append(rs.get_row_data())
        if not rows or rows[0][0] != today:
            return None

        import pandas as pd
        r = rows[0]
        vol = int(float(r[5])) if r[5] and r[5].strip() else 0
        amt = float(r[6]) if r[6] and r[6].strip() else 0.0
        df = pd.DataFrame([{
            "日期": r[0],
            "开盘": float(r[1]),
            "最高": float(r[2]),
            "最低": float(r[3]),
            "收盘": float(r[4]),
            "成交量": vol,
            "成交额": amt,
        }])
        return df
    except Exception as e:
        raise Exception(str(e))


def insert_klines(conn, stock_code, df, source, adjustment):
    if df is None or len(df) == 0:
        return 0
    cur = conn.cursor()
    sql = """
        INSERT INTO daily_klines
            (stock_code, trade_date, open, high, low, close,
             vol, amount, adjustment, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (stock_code, trade_date, source, adjustment) DO NOTHING
    """
    inserted = 0
    for _, row in df.iterrows():
        dt = str(row["日期"])[:10]

        def num(v):
            import pandas as pd
            if v is None or v == '' or (isinstance(v, float) and pd.isna(v)):
                return None
            return float(v)

        cur.execute(sql, (
            stock_code, dt,
            num(row.get("开盘")), num(row.get("最高")),
            num(row.get("最低")), num(row.get("收盘")),
            int(num(row.get("成交量")) or 0), num(row.get("成交额")) or 0,
            adjustment, source
        ))
        if cur.rowcount == 1:
            inserted += 1
    conn.commit()
    cur.close()
    return inserted


def probe_data_available(logger, probe_code="sh.600000", max_rounds=3, wait_minutes=15):
    """
    前置探测：检查 Baostock 是否已发布今日数据。
    用 sh.600000（浦发银行，高流动性，必有数据）作为探针。
    
    Args:
        logger:         logging.Logger
        probe_code:     探测用的股票代码
        max_rounds:     最大探测轮数
        wait_minutes:   每轮等待分钟数
    
    Returns:
        bool: True=数据已发布, False=超时仍无数据
    """
    today = date.today().strftime("%Y-%m-%d")
    for round_num in range(1, max_rounds + 1):
        try:
            rs = bs.query_history_k_data_plus(
                probe_code, "date,close",
                start_date=today, end_date=today,
                frequency="d", adjustflag="2"
            )
            rows = []
            while rs.next():
                rows.append(rs.get_row_data())
            if rows and rows[0][0] == today and rows[0][1] and rows[0][1].strip():
                logger.info(f"[PROBE] {probe_code} 今日数据已发布 (第{round_num}轮探测)")
                return True
        except Exception:
            pass
        
        if round_num < max_rounds:
            logger.info(f"[PROBE] {probe_code} 今日数据尚未发布，{wait_minutes}分钟后重试 (第{round_num}/{max_rounds}轮)")
            # 登出再登入，避免连接超时
            try:
                bs.logout()
            except Exception:
                pass
            time.sleep(wait_minutes * 60)
            bs.login()
    
    logger.warning(f"[PROBE] {max_rounds}轮探测({max_rounds*wait_minutes}分钟)后仍无数据，退出")
    logger.warning("[PROBE] 等待18:30 Hermes检查兜底")
    return False

def run():
    socket.setdefaulttimeout(30)
    cfg = load_config()
    source = "baostock"
    adjustment = "qfq"
    interval = 0.5
    max_retries = 3
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")

    logger = logging.getLogger("today_baostock")
    logger.setLevel(logging.INFO)
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
    logger.addHandler(h)

    # Baostock login
    bs.login()
    logger.info(f"Baostock login OK")

    # 先建立数据库连接（交易日校验需要）
    conn = get_db_conn(cfg)

    # ── 交易日校验（v1.2: 本地表优先 + API 兜底）─────────────────────
    if not is_trading_day(today_str, conn):
        logger.info(f"[SKIP] {today_str} 非交易日（周末/法定假日），退出")
        conn.close()
        bs.logout()
        return
    logger.info(f"[OK] {today_str} 是交易日，开始采集")
    # ───────────────────────────────────────────────────────────────────

    # ── 前置探测（v1.3: 检查 Baostock 是否已发布今日数据）───────────
    if not probe_data_available(logger):
        conn.close()
        bs.logout()
        return
    # ───────────────────────────────────────────────────────────────────

    exchanges = [("SSE", "沪市"), ("SZSE", "深市")]
    total_success = total_fail = total_skip = 0

    for exch_code, exch_name in exchanges:
        logger.info(f"====== 当日日线采集: {today_str} [{exch_name}] ======")
        codes = get_stock_codes(conn, exch_code)
        logger.info(f"Total: {len(codes)} stocks, interval={interval}s")

        success = fail = skip = 0
        for idx, code in enumerate(codes, 1):
            max_date = get_max_trade_date(conn, code, source, adjustment)
            if max_date and str(max_date) >= today_str:
                skip += 1
                continue

            df = None
            err = None
            for attempt in range(max_retries):
                try:
                    df = fetch_today_baostock(conn, code)
                    break
                except Exception as e:
                    err = str(e)
                    time.sleep(interval * (2 ** attempt) + random.uniform(0, 0.3))

            if df is None:
                logger.warning(f"  [FAIL] {code} ({idx}/{len(codes)}) — {err}")
                fail += 1
                continue

            if len(df) == 0:
                skip += 1
                continue

            inserted = insert_klines(conn, code, df, source, adjustment)
            action = "增量" if max_date else "首次"
            logger.info(f"  [OK] {code} ({idx}/{len(codes)}) {action} {inserted} new")
            success += 1
            time.sleep(interval + random.uniform(0, 0.1))

        logger.info(f"  [{exch_name}] success={success}, fail={fail}, skip={skip}")
        total_success += success
        total_fail += fail
        total_skip += skip

    conn.close()
    bs.logout()
    logger.info(f"\n[DONE] {today_str} 日线采集完成: success={total_success}, fail={total_fail}, skip={total_skip}")


if __name__ == "__main__":
    run()

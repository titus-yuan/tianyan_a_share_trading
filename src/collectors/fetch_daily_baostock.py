#!/usr/bin/env python3
"""fetch_daily_baostock.py — Baostock 前复权日线采集"""
import os, sys, time, yaml, psycopg2, random, logging, socket
from datetime import datetime, date, timedelta
import baostock as bs

socket.setdefaulttimeout(30)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.yaml")

def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def get_db_conn(cfg):
    return psycopg2.connect(**cfg["database"])

def get_all_stock_codes(conn):
    cur = conn.cursor()
    cur.execute("SELECT stock_code FROM stocks WHERE stock_code NOT LIKE 'bj.%' ORDER BY stock_code")
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

def fetch_klines(bs, code, start_date, end_date, adjustflag):
    rs = bs.query_history_k_data_plus(
        code, "date,open,high,low,close,volume,amount,adjustflag",
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        frequency="d", adjustflag=adjustflag
    )
    rows = []
    while rs.error_code == "0" and rs.next():
        rows.append(rs.get_row_data())
    if rs.error_code != "0":
        return None, rs.error_msg
    return rows, None

def insert_klines(conn, stock_code, rows, source, adjustment):
    if not rows:
        return 0
    cur = conn.cursor()
    sql = """
        INSERT INTO daily_klines
            (stock_code, trade_date, open, high, low, close,
             pre_close, change, pct_chg, vol, amount, adjustment, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (stock_code, trade_date, source, adjustment) DO NOTHING
    """
    prev_close = None
    inserted = 0
    for row in rows:
        date_str, open_, high, low, close, vol, amount, adjustflag = row
        def to_float(v):
            return None if v in ("", "None") else float(v)
        def to_int(v):
            return None if v in ("", "None") else int(float(v))
        close_f = to_float(close)
        pre_close_f = prev_close
        prev_close = close_f
        change_f = round(close_f - pre_close_f, 2) if (close_f and pre_close_f) else None
        pct_chg_f = round((close_f - pre_close_f) / pre_close_f * 100, 4) if (close_f and pre_close_f and pre_close_f != 0) else None
        cur.execute(sql, (
            stock_code, date_str,
            to_float(open_), to_float(high), to_float(low), close_f,
            pre_close_f, change_f, pct_chg_f,
            to_int(vol), to_float(amount),
            adjustment, source
        ))
        if cur.rowcount == 1:
            inserted += 1
    conn.commit()
    cur.close()
    return inserted

def run():
    cfg = load_config()
    source = "baostock"
    adjustment = cfg["collector"]["default_adjustment"]
    interval = float(cfg.get("baostock", {}).get("request_interval", 0.5))
    max_retries = int(cfg.get("baostock", {}).get("max_retries", 3))
    start_date = datetime.strptime(cfg["baostock"]["default_start_date"], "%Y-%m-%d").date()
    end_date = min(datetime.strptime(cfg["baostock"]["default_end_date"], "%Y-%m-%d").date(), date.today())

    log_dir = cfg["collector"]["log_dir"]
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("baostock")
    logger.setLevel(logging.INFO)
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
    logger.addHandler(h)

    logger.info(f"====== Baostock 前复权采集 ======")
    logger.info(f"Source: {source}, Adjustment: {adjustment}, adjustflag=2")
    logger.info(f"Date: {start_date} ~ {end_date}, interval={interval}s")

    bs.login()
    logger.info("Baostock logged in")

    conn = get_db_conn(cfg)
    stock_codes = get_all_stock_codes(conn)
    total = len(stock_codes)
    logger.info(f"Total stocks: {total}")

    success = fail = skip = 0
    for idx, code in enumerate(stock_codes, 1):
        try:
            max_date = get_max_trade_date(conn, code, source, adjustment)
            query_start = max_date + timedelta(days=1) if max_date else start_date

            if query_start > end_date:
                skip += 1
                continue

            rows = None
            err = None
            for attempt in range(max_retries):
                try:
                    rows, err = fetch_klines(bs, code, query_start, end_date, "2")
                except (socket.timeout, ConnectionError, OSError) as e:
                    err = f"网络错误: {e}"
                    rows = None
                if rows is not None:
                    break
                wait = interval * (2 ** attempt) + random.uniform(0, 0.5)
                logger.warning(f"  [RETRY] {code} ({idx}/{total}) attempt {attempt+1}: {err}, wait {wait:.1f}s")
                time.sleep(wait)

            if rows is None:
                logger.error(f"  [FAIL] {code} ({idx}/{total}) — {err}")
                fail += 1
                continue

            if not rows:
                skip += 1
                continue

            inserted = insert_klines(conn, code, rows, source, adjustment)
            success += 1
            action = "增量" if max_date else "首次"
            logger.info(f"  [OK] {code} ({idx}/{total}) — {action} {len(rows)} rows, {inserted} new")

            time.sleep(interval + random.uniform(0, 0.2))

        except Exception as e:
            logger.error(f"  [ERR] {code} ({idx}/{total}) — {e}")
            fail += 1

    bs.logout()
    conn.close()
    logger.info(f"\n[RESULT] success={success}, fail={fail}, skip={skip}")

if __name__ == "__main__":
    run()

#!/usr/bin/env python3
"""
fetch_stocks.py — Step 1：股票基本信息采集 (AKShare 版)
调用 AKShare 拉取全量 A 股列表（含退市），写入 stocks 表
"""
import os, sys, time, yaml, psycopg2
import akshare as ak

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.yaml")


def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"config.yaml not found: {CONFIG_PATH}")
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def get_db_conn(cfg):
    return psycopg2.connect(**cfg["database"])


def normalize_code(raw_code):
    """AKShare 返回 000001 → 存为 sz.000001 / sh.600000 / bj.830000"""
    code = str(raw_code).zfill(6)
    if code.startswith(("60", "68")):
        return f"sh.{code}", "SSE"
    elif code.startswith(("00", "30", "20")):
        return f"sz.{code}", "SZSE"
    elif code.startswith(("83", "87", "88", "92")):
        return f"bj.{code}", "BSE"
    else:
        return f"sz.{code}", "SZSE"


def upsert_stocks(conn, rows, source="akshare"):
    """批量 upsert 股票基本信息"""
    cur = conn.cursor()
    sql = """
        INSERT INTO stocks (stock_code, exchange, stock_name, list_date, delist_date, is_valid, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (stock_code) DO UPDATE SET
            stock_name = EXCLUDED.stock_name,
            list_date = EXCLUDED.list_date,
            delist_date = EXCLUDED.delist_date,
            is_valid = EXCLUDED.is_valid
    """
    count = 0
    for _, row in rows.iterrows():
        raw_code = str(row.iloc[0])
        name = str(row.iloc[1]) if len(row) > 1 else ""
        code, exchange = normalize_code(raw_code)
        cur.execute(sql, (code, exchange, name, None, None, True, source))
        count += 1
    conn.commit()
    cur.close()
    return count


def main():
    print("[INFO] ====== Step 1: Fetch Stock Basic Info (AKShare) =====")
    cfg = load_config()
    conn = get_db_conn(cfg)

    df = ak.stock_info_a_code_name()
    print(f"[INFO] AKShare returned {len(df)} active stocks")

    count = upsert_stocks(conn, df)
    print(f"[OK] {count} active stocks upserted")

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM stocks")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM stocks WHERE is_valid = true")
    active = cur.fetchone()[0]
    print(f"[VERIFY] Total: {total}, Active: {active}")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()

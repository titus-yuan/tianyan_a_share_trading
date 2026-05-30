#!/usr/bin/env python3
"""
fetch_valuation.py — A股估值快照采集（PE/PB/总市值/流通市值）

数据源: push2delay.eastmoney.com/api/qt/clist/get
采集字段: f9=PE动态, f23=PB, f20=总市值, f21=流通市值, f2=最新价

策略:
  - 批量分页 (pz=100, ~56页), ~30秒完成全A股
  - 间隔 0.3s/页 (push2delay 延迟行情, 无严格限制)
  - 仅写入 stocks 表中在市股票
  - ON CONFLICT DO UPDATE (幂等, 同天多次运行会更新)

用法:
  python fetch_valuation.py          # 采集当日估值快照
  python fetch_valuation.py --init   # 仅建表
"""
import os, sys, time, yaml, psycopg2
import httpx
from datetime import date

EM = "https://push2delay.eastmoney.com"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.yaml")
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")


def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"config.yaml not found: {CONFIG_PATH}")
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def get_db_conn(cfg):
    return psycopg2.connect(**cfg["database"])


def code_to_db(code: str) -> str:
    """东方财富纯数字代码 → stocks 表前缀格式: sh.600519 / sz.000001 / bj.920000"""
    code = str(code).zfill(6)
    if code.startswith("6"):
        return f"sh.{code}"
    elif code.startswith(("0", "3")):
        return f"sz.{code}"
    elif code.startswith(("4", "8", "9")):
        return f"bj.{code}"
    return f"sz.{code}"


def create_table(conn):
    """建表 + 索引"""
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_valuation (
            id              BIGSERIAL PRIMARY KEY,
            stock_code      VARCHAR(10) NOT NULL,
            trade_date      DATE NOT NULL,
            total_market_cap NUMERIC(20,2),
            float_market_cap NUMERIC(20,2),
            pe              NUMERIC(12,4),
            pb              NUMERIC(10,4),
            price           NUMERIC(10,4),
            created_at      TIMESTAMP DEFAULT NOW(),
            UNIQUE(stock_code, trade_date)
        )
    """)
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_valuation_stock_date ON stock_valuation(stock_code, trade_date)"
    )
    conn.commit()
    cur.close()
    print("[INIT] stock_valuation 表已就绪")


def fetch_page(page: int) -> tuple[list[dict], int]:
    """拉取一页估值数据，返回 (数据列表, 总条数)"""
    resp = httpx.get(
        f"{EM}/api/qt/clist/get",
        params={
            "pn": page,
            "pz": 100,
            "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
            "fields": "f2,f9,f12,f14,f20,f21,f23",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    total = data.get("data", {}).get("total", 0)
    if not data.get("data") or not data["data"].get("diff"):
        return [], total

    results = []
    for item in data["data"]["diff"].values():
        total_cap = item.get("f20", 0) or 0
        if total_cap == 0:  # 跳过退市/无效股票
            continue
        results.append(
            {
                "code": item["f12"],
                "name": item.get("f14", ""),
                "price": (item.get("f2", 0) or 0) / 100,
                "pe": (item.get("f9", 0) or 0) / 100,
                "pb": (item.get("f23", 0) or 0) / 100,
                "total_cap": total_cap,
                "float_cap": item.get("f21", 0) or 0,
            }
        )
    return results, total


def main():
    print("[INFO] ====== fetch_valuation ======")
    os.makedirs(LOG_DIR, exist_ok=True)

    cfg = load_config()
    conn = get_db_conn(cfg)

    # --init 模式：仅建表
    if "--init" in sys.argv:
        create_table(conn)
        conn.close()
        return

    # 确保表存在
    create_table(conn)

    today = date.today()
    print(f"[INFO] 采集日期: {today}")

    # ---- 分页拉取全 A 股估值 ----
    all_data = []
    page = 1
    total_from_api = 0
    while True:
        batch, api_total = fetch_page(page)
        if page == 1:
            total_from_api = api_total
            print(f"[INFO] API 返回总量: {total_from_api} 条, 预计 {max(total_from_api // 100, 1)} 页")
        if not batch:
            break
        all_data.extend(batch)
        print(f"  [PAGE {page:>2d}] {len(batch)} 条 (累计 {len(all_data)})")
        # 用 API 总量判断是否拉完（而非过滤后数量）
        max_pages = max((total_from_api + 99) // 100, 1)
        if page >= max_pages:
            break
        page += 1
        time.sleep(0.3)

    print(f"[INFO] 共获取 {len(all_data)} 条估值数据")

    # ---- 写入 stock_valuation（仅存入在市股票） ----
    sql = """
        INSERT INTO stock_valuation (stock_code, trade_date, total_market_cap, float_market_cap, pe, pb, price)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (stock_code, trade_date) DO UPDATE SET
            total_market_cap = EXCLUDED.total_market_cap,
            float_market_cap = EXCLUDED.float_market_cap,
            pe = EXCLUDED.pe,
            pb = EXCLUDED.pb,
            price = EXCLUDED.price
    """

    cur = conn.cursor()
    inserted = 0
    skipped = 0
    for item in all_data:
        db_code = code_to_db(item["code"])
        # 仅在 stocks 表中存在的股票才写入
        cur.execute("SELECT 1 FROM stocks WHERE stock_code = %s", (db_code,))
        if not cur.fetchone():
            skipped += 1
            continue
        cur.execute(
            sql,
            (
                db_code,
                today,
                item["total_cap"],
                item["float_cap"],
                item["pe"],
                item["pb"],
                item["price"],
            ),
        )
        inserted += 1

    conn.commit()
    cur.close()

    # ---- 验证 ----
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM stock_valuation WHERE trade_date = %s", (today,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()

    print(f"\n[DONE] 写入: {inserted} 条, 跳过(不在stocks表): {skipped} 条")
    print(f"[VERIFY] stock_valuation 当日记录: {count} 条")


if __name__ == "__main__":
    main()

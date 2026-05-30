#!/usr/bin/env python3
"""
fetch_capitalization_em_v1.0.py — 沪市股本数据采集（东方财富延迟行情版）

=== 变更记录 ===
v1.0 (2026-05-17):
  - 弃用 AKShare stock_individual_info_em()（push2.eastmoney.com 被封）
  - 改用 httpx 直连 push2delay.eastmoney.com/api/qt/stock/get
  - 字段映射: f84→总股本, f85→流通股, f57→代码, f58→名称
  - 仅采集沪市（sh.%），深市+北交所用 fetch_capitalization_sina.py
  - 间隔从 1s 改为 0.3s（延迟行情节点无速率限制）
  - 失败重试 3 次，间隔递增（1s/3s/5s）

v0 (被封前):
  - 使用 AKShare stock_individual_info_em(symbol) → push2.eastmoney.com

=== 数据源 ===
API: https://push2delay.eastmoney.com/api/qt/stock/get
参数: secid=1.{code}  (1=沪市)
      fields=f57,f58,f84,f85
返回: {"data": {"f57": "600519", "f58": "贵州茅台", "f84": 总股本, "f85": 流通股}}

入库: stocks 表（total_shares / float_shares）
策略: 单只遍历，间隔 0.3s/只，失败重试 3 次
"""
import os, sys, time, yaml, psycopg2, socket

import httpx

socket.setdefaulttimeout(30)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.yaml")
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")

# 东方财富延迟行情节点（Bot PC 可用）
EM_BASE = "https://push2delay.eastmoney.com"


def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"config.yaml not found: {CONFIG_PATH}")
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def get_db_conn(cfg):
    return psycopg2.connect(**cfg["database"])


def extract_code(stock_code: str) -> str:
    """从 'sh.600519' 提取 '600519'"""
    return stock_code.split(".", 1)[1]


def fetch_capitalization(stock_code: str) -> dict | None:
    """
    通过 push2delay.eastmoney.com 采集单只沪市股票股本
    返回 {'total_shares': int, 'float_shares': int, 'name': str} 或 None
    """
    code = extract_code(stock_code)
    url = f"{EM_BASE}/api/qt/stock/get"
    params = {
        "secid": f"1.{code}",  # 1 = 沪市
        "fields": "f57,f58,f84,f85",
    }

    delays = [1, 3, 5]  # 重试间隔递增
    for attempt in range(3):
        try:
            resp = httpx.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            if not data.get("data"):
                print(f"[WARN] {stock_code} empty response data")
                if attempt < 2:
                    time.sleep(delays[attempt])
                continue

            d = data["data"]
            total = int(d.get("f84", 0) or 0)
            float_s = int(d.get("f85", 0) or 0)

            if total == 0:
                print(f"[WARN] {stock_code} total_shares=0, skip")
                return None

            return {
                "total_shares": total,
                "float_shares": float_s,
                "name": d.get("f58", ""),
            }
        except Exception as e:
            print(f"[WARN] {stock_code} attempt {attempt+1}/3: {type(e).__name__}: {e}")
            if attempt < 2:
                time.sleep(delays[attempt])
    return None


def update_shares(conn, stock_code: str, total_shares: int, float_shares: int):
    """更新 stocks 表的股本字段"""
    cur = conn.cursor()
    cur.execute(
        "UPDATE stocks SET total_shares = %s, float_shares = %s WHERE stock_code = %s",
        (total_shares, float_shares, stock_code),
    )
    conn.commit()
    cur.close()


def main():
    print("[INFO] ====== fetch_capitalization_em_v1.0 (沪市 · push2delay) ======")
    os.makedirs(LOG_DIR, exist_ok=True)
    cfg = load_config()
    conn = get_db_conn(cfg)

    # 仅拉沪市在市股票
    cur = conn.cursor()
    cur.execute(
        "SELECT stock_code FROM stocks WHERE is_valid = true AND stock_code LIKE 'sh.%%' ORDER BY stock_code"
    )
    stocks = [row[0] for row in cur.fetchall()]
    cur.close()

    total = len(stocks)
    print(f"[INFO] 沪市在市股票: {total} 只")

    success_count = 0
    fail_count = 0
    zero_count = 0
    fail_log_path = os.path.join(LOG_DIR, "capitalization_sh_failed.log")

    with open(fail_log_path, "w") as fail_log:
        for i, stock_code in enumerate(stocks, 1):
            print(f"[{i}/{total}] {stock_code}", end=" ", flush=True)
            result = fetch_capitalization(stock_code)

            if result and result["total_shares"] > 0:
                update_shares(
                    conn, stock_code, result["total_shares"], result["float_shares"]
                )
                print(
                    f"OK  {result['name']} 总股本={result['total_shares']/1e8:.2f}亿 流通={result['float_shares']/1e8:.2f}亿"
                )
                success_count += 1
            elif result and result["total_shares"] == 0:
                print(f"SKIP (total_shares=0)")
                fail_log.write(f"{stock_code}\t股本为0\n")
                zero_count += 1
            else:
                print(f"FAIL")
                fail_log.write(f"{stock_code}\t3次重试均失败\n")
                fail_count += 1

            time.sleep(0.3)  # push2delay 无严格速率限制

    print()
    print(f"[DONE] 成功: {success_count}, 股本为0: {zero_count}, 失败: {fail_count}")
    print(f"[EST] 预计耗时: {total * 0.3 / 60:.1f} 分钟")
    if fail_count > 0:
        print(f"[FAIL_LOG] {fail_log_path}")

    # 验证
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM stocks WHERE is_valid = true AND stock_code LIKE 'sh.%%' AND total_shares IS NOT NULL"
    )
    filled = cur.fetchone()[0]
    print(f"[VERIFY] 沪市已有股本数据: {filled}/{total}")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()

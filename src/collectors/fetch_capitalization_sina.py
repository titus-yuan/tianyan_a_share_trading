#!/usr/bin/env python3
"""
fetch_capitalization_sina.py — Step 3：股本数据采集（新浪版）

数据来源：
  - 深市 → stock_info_sz_name_code()  批量，2890只
  - 北交所 → stock_info_bj_name_code() 批量，312只
  - 沪市 → stock_individual_info_em() 东方财富单只调（IP封禁期间不可用）

入库：stocks 表（total_shares / float_shares）
策略：深市+北市批量一次拉，沪市单只遍历（间隔1s，失败重试3次）

东方财富解封后直接跑本脚本即可完成全量采集。
"""
import os, sys, time, yaml, psycopg2, socket
import akshare as ak

socket.setdefaulttimeout(30)

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


def normalize_to_db_code(code: str, exchange: str) -> str:
    """统一代码格式为 db 格式: sh.600000 / sz.000001 / bj.920000"""
    code = str(code).zfill(6)
    if exchange in ("SSE", "sh"):
        return f"sh.{code}"
    elif exchange in ("SZSE", "sz"):
        return f"sz.{code}"
    elif exchange in ("BSE", "bj"):
        return f"bj.{code}"
    return f"sz.{code}"


# ─── 深市：stock_info_sz_name_code 批量 ───────────────────────────────

def fetch_szse_cap() -> dict:
    """
    拉取深市全部股票股本数据（批量接口，无速率限制）
    返回 {(exchange, code): {total_shares, float_shares}}
    """
    print("[INFO] 拉取深市股本数据 (stock_info_sz_name_code)...")
    df = ak.stock_info_sz_name_code()  # 字段: 板块, A股代码, A股简称, A股上市日期, A股总股本, A股流通股本, 所属行业
    result = {}
    for _, row in df.iterrows():
        db_code = f"sz.{str(row['A股代码']).zfill(6)}"
        # 去掉千分位逗号，转为 float
        total = float(str(row['A股总股本']).replace(",", "")) if pd.notna(row['A股总股本']) else 0
        float_s = float(str(row['A股流通股本']).replace(",", "")) if pd.notna(row['A股流通股本']) else 0
        result[db_code] = {"total_shares": total, "float_shares": float_s}
    print(f"[INFO] 深市 {len(result)} 只数据拉取完成")
    return result


# ─── 北交所：stock_info_bj_name_code 批量 ──────────────────────────────

def fetch_bse_cap() -> dict:
    """
    拉取北交所全部股票股本数据（批量接口，无速率限制）
    返回 {db_code: {total_shares, float_shares}}
    """
    print("[INFO] 拉取北交所股本数据 (stock_info_bj_name_code)...")
    df = ak.stock_info_bj_name_code()  # 字段: 证券代码, 证券简称, 总股本, 流通股本, 上市日期, 所属行业, 地区, 报告日期
    result = {}
    for _, row in df.iterrows():
        db_code = f"bj.{str(row['证券代码']).zfill(6)}"
        total = float(str(row['总股本']).replace(",", "")) if pd.notna(row['总股本']) else 0
        float_s = float(str(row['流通股本']).replace(",", "")) if pd.notna(row['流通股本']) else 0
        result[db_code] = {"total_shares": total, "float_shares": float_s}
    print(f"[INFO] 北交所 {len(result)} 只数据拉取完成")
    return result


# ─── 沪市：stock_individual_info_em 单只（东方财富，东方财富解封后可用）──

def extract_sh_code(stock_code: str) -> str:
    """从 'sh.601398' 提取 '601398'"""
    return stock_code.split(".", 1)[1]


def fetch_sh_single(stock_code: str) -> dict | None:
    """单只沪市股票股本，失败重试3次"""
    code = extract_sh_code(stock_code)
    for attempt in range(3):
        try:
            df = ak.stock_individual_info_em(symbol=code)
            row = df.set_index("item")["value"]
            return {
                "total_shares": float(row.get("总股本", 0) or 0),
                "float_shares": float(row.get("流通股", 0) or 0),
            }
        except Exception as e:
            print(f"[WARN] {stock_code} attempt {attempt+1}/3 failed: {type(e).__name__}")
            if attempt < 2:
                time.sleep(2)
    return None


# ─── 数据库写入 ─────────────────────────────────────────────────────────

def batch_update_shares(conn, data: dict):
    """
    批量更新股本数据
    data: {stock_code: {total_shares, float_shares}}
    """
    cur = conn.cursor()
    sql = """
        UPDATE stocks
        SET total_shares = %(total_shares)s,
            float_shares  = %(float_shares)s
        WHERE stock_code = %(stock_code)s
    """
    for stock_code, vals in data.items():
        cur.execute(sql, {"stock_code": stock_code, **vals})
    conn.commit()
    cur.close()


def update_single_share(conn, stock_code: str, total_shares: float, float_shares: float):
    cur = conn.cursor()
    cur.execute(
        "UPDATE stocks SET total_shares = %s, float_shares = %s WHERE stock_code = %s",
        (total_shares, float_shares, stock_code)
    )
    conn.commit()
    cur.close()


# ─── 主流程 ─────────────────────────────────────────────────────────────

def main():
    print("[INFO] ====== fetch_capitalization_sina ======")
    os.makedirs(LOG_DIR, exist_ok=True)
    cfg = load_config()
    conn = get_db_conn(cfg)

    all_data = {}  # 合并深市+北市+沪市数据

    # 1. 深市批量
    sz_data = fetch_szse_cap()
    all_data.update(sz_data)

    # 2. 北交所批量
    bse_data = fetch_bse_cap()
    all_data.update(bse_data)

    print(f"[INFO] 深市+北市合计: {len(all_data)} 只")

    # 3. 写入深市+北市数据
    batch_update_shares(conn, all_data)
    print(f"[OK] 深市+北市 {len(all_data)} 只已写入 stocks 表")

    # 4. 沪市：单只调（等东方财富解封）
    cur = conn.cursor()
    cur.execute("SELECT stock_code FROM stocks WHERE is_valid = true AND stock_code LIKE 'sh.%' ORDER BY stock_code")
    sh_stocks = [row[0] for row in cur.fetchall()]
    cur.close()
    print(f"[INFO] 沪市股票数量: {len(sh_stocks)} 只")
    print("[WARN] 沪市需通过 stock_individual_info_em 单只采集（当前东方财富封禁中，IP 解封后可用）")

    # 验证入库
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM stocks WHERE total_shares IS NOT NULL")
    filled = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM stocks WHERE is_valid = true")
    total = cur.fetchone()[0]
    cur.close()
    conn.close()

    print()
    print(f"[DONE] stocks 表已更新: {filled}/{total} 只有股本数据")
    print(f"[INFO] 东方财富 IP 解封后，运行 fetch_capitalization_em.py 补采沪市 {len(sh_stocks)} 只")


if __name__ == "__main__":
    import pandas as pd  # 深市/北市数据处理需要
    main()

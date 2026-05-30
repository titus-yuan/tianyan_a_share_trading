#!/usr/bin/env python3
"""
uptrend_scanner.py — 上升通道扫描器（沪市测试版）
思路1：均线多头排列 + 均线向上 + 量能配合
"""
import os, sys, traceback
import psycopg2
import pandas as pd
import numpy as np
from datetime import date, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.yaml")


def load_config():
    import yaml
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def get_db_conn(cfg):
    return psycopg2.connect(**cfg["database"])


def calc_slope(series, window=5):
    if len(series) < window:
        return 0.0
    recent = series.tail(window).values.astype(float)
    x = np.arange(window)
    slope = np.polyfit(x, recent, 1)[0]
    return slope


def scan_uptrend(conn, lookback=65):
    today = date.today()
    start_date = today - timedelta(days=lookback)
    start_str = str(start_date)

    # 查沪市在市股票数量
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM stocks WHERE is_valid = true AND exchange = 'SSE'")
    total_sh = cur.fetchone()[0]
    print(f"[INFO] 沪市股票数量: {total_sh}")

    # 取最近 lookback 天所有沪市日线（仅 baostock qfq 前复权）
    cur.execute("""
        SELECT 
            dl.stock_code,
            dl.trade_date::text,
            dl.close::numeric,
            dl.vol::bigint
        FROM daily_klines dl
        WHERE dl.source = 'baostock'
          AND dl.adjustment = 'qfq'
          AND dl.stock_code IN (
              SELECT stock_code FROM stocks
              WHERE is_valid = true AND exchange = 'SSE'
          )
          AND dl.trade_date >= %s
        ORDER BY dl.stock_code, dl.trade_date
    """, (start_str,))
    rows = cur.fetchall()
    cur.close()

    print(f"[INFO] 拉取日线记录: {len(rows)} 条")
    if not rows:
        print("[ERROR] 无日线数据")
        return pd.DataFrame()

    # 构建 DataFrame
    df = pd.DataFrame(rows, columns=["stock_code", "trade_date", "close", "vol"])
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date

    results = []
    sh_codes = df["stock_code"].unique()
    print(f"[INFO] 实际有数据的股票: {len(sh_codes)}")

    for code in sh_codes:
        stock_df = df[df["stock_code"] == code].sort_values("trade_date").reset_index(drop=True)
        if len(stock_df) < 30:
            continue

        close_arr = stock_df["close"].values.astype(float)
        vol_arr = stock_df["vol"].values.astype(float)

        # 计算 MA
        ma5_arr = pd.Series(close_arr).rolling(5).mean().values
        ma20_arr = pd.Series(close_arr).rolling(20).mean().values
        ma60_arr = pd.Series(close_arr).rolling(60).mean().values
        vol_ma20_arr = pd.Series(vol_arr).rolling(20).mean().values

        idx = len(stock_df) - 1
        close = close_arr[idx]
        ma5 = ma5_arr[idx]
        ma20 = ma20_arr[idx]
        ma60 = ma60_arr[idx]
        vol_today = vol_arr[idx]
        vol_ma20 = vol_ma20_arr[idx]

        if any(pd.isna([ma5, ma20, ma60, vol_ma20])):
            continue

        # 斜率
        ma5_s = pd.Series(ma5_arr[:idx+1])
        ma20_s = pd.Series(ma20_arr[:idx+1])
        slope_ma5 = calc_slope(ma5_s, 5)
        slope_ma20 = calc_slope(ma20_s, 5)

        # 4 个条件
        if not (close > ma5 > ma20 > ma60):
            continue
        if not (slope_ma5 > 0 and slope_ma20 > 0):
            continue
        if not (vol_today > vol_ma20):
            continue

        results.append({
            "stock_code": code,
            "close": round(close, 3),
            "MA5": round(ma5, 3),
            "MA20": round(ma20, 3),
            "MA60": round(ma60, 3),
            "slope_MA5": round(slope_ma5, 4),
            "slope_MA20": round(slope_ma20, 4),
            "vol_today": int(vol_today),
            "vol_MA20": int(vol_ma20),
            "vol_ratio": round(vol_today / vol_ma20, 2),
            "trade_date": str(stock_df.iloc[idx]["trade_date"]),
        })

    return pd.DataFrame(results)


def main():
    print("====== 上升通道扫描器 v1.1（沪市测试） ======")
    try:
        cfg = load_config()
        conn = get_db_conn(cfg)

        df = scan_uptrend(conn, lookback=65)

        if df.empty:
            print("\n[结果] 无符合上升通道条件的股票")
            conn.close()
            return

        df = df.sort_values("vol_ratio", ascending=False).reset_index(drop=True)

        print(f"\n{'='*85}")
        print(f"  上升通道股票清单（沪市，{date.today()}，共 {len(df)} 只）")
        print(f"{'='*85}")
        header = f"{'代码':<10} {'收盘':>8} {'MA5':>8} {'MA20':>8} {'MA60':>8} {'斜率MA5':>8} {'斜率MA20':>8} {'量比':>6}"
        print(header)
        print("-" * 85)

        for _, row in df.iterrows():
            print(f"{row['stock_code']:<10} {row['close']:>8.3f} {row['MA5']:>8.3f} {row['MA20']:>8.3f} "
                  f"{row['MA60']:>8.3f} {row['slope_MA5']:>8.4f} {row['slope_MA20']:>8.4f} {row['vol_ratio']:>6.2f}")

        print("-" * 85)
        print(f"共 {len(df)} 只符合条件\n")

        # 保存 CSV
        out_dir = os.path.join(SCRIPT_DIR, "data")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"uptrend_sse_{date.today()}.csv")
        df.to_csv(out_path, index=False)
        print(f"[保存] {out_path}")

        conn.close()

    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    main()
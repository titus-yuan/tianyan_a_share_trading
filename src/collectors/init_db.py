#!/usr/bin/env python3
"""
init_db.py — A 股数据采集层数据库初始化
读取 config.yaml，执行建表 SQL（stocks + daily_klines）
"""
import os, sys, yaml, psycopg2

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.yaml")

SQL = """
-- 1. 股票基本信息表
CREATE TABLE IF NOT EXISTS stocks (
    stock_code    VARCHAR(10) PRIMARY KEY,
    exchange      VARCHAR(4),
    stock_name    VARCHAR(32),
    list_date     DATE,
    delist_date   DATE,
    is_valid      BOOLEAN DEFAULT true,
    source        VARCHAR(16) DEFAULT 'baostock'
);

-- 2. 日线行情表（多数据源+多复权版）
CREATE TABLE IF NOT EXISTS daily_klines (
    id            BIGSERIAL PRIMARY KEY,
    stock_code    VARCHAR(10) NOT NULL,
    trade_date    DATE NOT NULL,
    open          NUMERIC(10,2),
    high          NUMERIC(10,2),
    low           NUMERIC(10,2),
    close         NUMERIC(10,2),
    pre_close     NUMERIC(10,2),
    change        NUMERIC(10,2),
    pct_chg       NUMERIC(10,4),
    vol           NUMERIC(20,0),
    amount        NUMERIC(20,2),
    adjustment    VARCHAR(8) NOT NULL,
    source        VARCHAR(16) NOT NULL,
    created_at    TIMESTAMP DEFAULT NOW(),
    UNIQUE(stock_code, trade_date, source, adjustment)
);

CREATE INDEX IF NOT EXISTS idx_daily_stock_date ON daily_klines(stock_code, trade_date);
CREATE INDEX IF NOT EXISTS idx_daily_date ON daily_klines(trade_date);
CREATE INDEX IF NOT EXISTS idx_daily_source_adj ON daily_klines(source, adjustment);
"""


def main():
    # 读取配置
    if not os.path.exists(CONFIG_PATH):
        print(f"[ERROR] config.yaml not found: {CONFIG_PATH}")
        sys.exit(1)

    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)

    db = cfg["database"]
    print(f"[INFO] Connecting to PostgreSQL {db['host']}:{db['port']}/{db['database']}")

    conn = psycopg2.connect(**db)
    conn.autocommit = False
    cur = conn.cursor()

    # 执行建表
    for statement in SQL.strip().split(";"):
        stmt = statement.strip()
        if stmt:
            cur.execute(stmt)

    conn.commit()
    print("[OK] Tables created successfully")

    # 验证
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('stocks', 'daily_klines')
        ORDER BY table_name
    """)
    rows = cur.fetchall()
    print(f"[OK] Verified tables: {[r[0] for r in rows]}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()

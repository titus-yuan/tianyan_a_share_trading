#!/usr/bin/env python3
"""
=============================================================================
 fetch_trade_calendar_baostock_v1.0.py
=============================================================================

 脚本用途 (Purpose):
   从 Baostock 一次性拉取 A 股全量交易日历数据（1990-12-19 ~ 当前年末），
   写入 PostgreSQL 表 trade_calendar（Stocks_China_A 库）。
   - 数据源: Baostock query_trade_dates()，覆盖沪深两市
   - 存储方案: 存全部日期 + is_open 标记（交易日/非交易日）
   - 执行时机: 一次性全量，之后每年初手动跑一次增量即可
   - 防重复: ON CONFLICT (trade_date) DO NOTHING
   - 行数: 约 13,000+（36 年 × 365 天）

 脚本命名解析 (Name Breakdown):
   fetch               = 采集 / 拉取
   trade               = 交易（A 股交易市场）
   calendar            = 日历（交易日历，含节假日/周末判断）
   baostock            = 数据源（Baostock，无 IP 限制）
   v1.0                = 版本号（初始版本 1.0）

 表结构 (trade_calendar):
   trade_date   DATE PRIMARY KEY   -- 日历日期
   is_open      BOOLEAN NOT NULL   -- TRUE=交易日, FALSE=非交易日
   week_day     SMALLINT           -- 星期几 (0=周一, 6=周日)
   source       VARCHAR(16)        -- 数据源 'baostock'
   created_at   TIMESTAMP          -- 入库时间

 变更记录 (Changelog):
   v1.0 (2026-05-15)   初始版本
                       - 一次性采集 1990-12-19 ~ 2026-12-31 全量交易日历
                       - 13,162 行，单次 API 调用即可（Baostock 支持全量范围）
                       - 包含周末 + 法定假日（春节/国庆/五一/端午等）标记
                       - 写入 trade_calendar 表（Stocks_China_A）

 调用方式:
   python -u fetch_trade_calendar_baostock_v1.0.py

 依赖:
   - baostock, psycopg2
=============================================================================
"""
import os, sys, logging, socket
from datetime import datetime, date
import baostock as bs
import psycopg2

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── 配置 ──────────────────────────────────────────────────────────────
DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'Stocks_China_A'
DB_USER = 'postgres'
DB_PASS = ''
SOURCE  = 'baostock'

# Baostock 交易日历查询范围
START_DATE = '1990-01-01'
END_DATE   = '2026-12-31'
# ───────────────────────────────────────────────────────────────────────


def setup_logger():
    logger = logging.getLogger('trade_cal')
    logger.setLevel(logging.INFO)
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
    logger.addHandler(h)
    return logger


def get_db_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME,
        user=DB_USER, password=DB_PASS
    )


def fetch_calendar_from_baostock(log):
    """
    从 Baostock 拉取全量交易日历。
    返回: list of (date_str, is_open_bool, week_day_int)
    """
    log.info(f'查询 Baostock 交易日历: {START_DATE} ~ {END_DATE}')
    rs = bs.query_trade_dates(START_DATE, END_DATE)
    if rs.error_code != '0':
        raise RuntimeError(f'Baostock query_trade_dates 失败: {rs.error_msg}')

    rows = []
    trading_count = 0
    non_trading_count = 0

    while rs.next():
        row_data = rs.get_row_data()
        # row_data = [calendar_date, is_trading_day]
        trade_date = row_data[0]
        is_open = (row_data[1] == '1')
        
        # 计算星期几 (0=周一, 6=周日)
        dt = datetime.strptime(trade_date, '%Y-%m-%d')
        week_day = dt.weekday()
        
        rows.append((trade_date, is_open, week_day))
        
        if is_open:
            trading_count += 1
        else:
            non_trading_count += 1

    log.info(f'获取完成: 总计 {len(rows)} 行 (交易日 {trading_count}, 非交易日 {non_trading_count})')
    return rows


def insert_calendar_to_db(conn, rows, log):
    """
    将交易日历写入 trade_calendar 表。
    ON CONFLICT DO NOTHING — 已存在的日期不重复插入。
    """
    cur = conn.cursor()
    sql = """
        INSERT INTO trade_calendar (trade_date, is_open, week_day, source)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (trade_date) DO NOTHING
    """
    
    inserted = 0
    skipped = 0
    
    log.info(f'开始写入数据库 (共 {len(rows)} 行)...')
    
    for trade_date, is_open, week_day in rows:
        cur.execute(sql, (trade_date, is_open, week_day, SOURCE))
        if cur.rowcount == 1:
            inserted += 1
        else:
            skipped += 1
    
    conn.commit()
    cur.close()
    log.info(f'写入完成: 新增 {inserted} 行, 跳过 {skipped} 行 (已存在)')


def verify(conn, log):
    """验证入库结果"""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*), MIN(trade_date), MAX(trade_date) FROM trade_calendar")
    total, min_date, max_date = cur.fetchone()
    
    cur.execute("SELECT COUNT(*) FROM trade_calendar WHERE is_open = TRUE")
    trading_days = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM trade_calendar WHERE is_open = FALSE")
    non_trading = cur.fetchone()[0]
    
    log.info(f'验证结果:')
    log.info(f'  总行数:    {total}')
    log.info(f'  日期范围:  {min_date} ~ {max_date}')
    log.info(f'  交易日:    {trading_days}')
    log.info(f'  非交易日:  {non_trading}')
    
    # 检查周末是否正确标记
    cur.execute("""
        SELECT trade_date, week_day, is_open FROM trade_calendar 
        WHERE trade_date = '2026-05-16'
    """)
    row = cur.fetchone()
    if row:
        dt, wd, is_open = row
        log.info(f'  抽查 2026-05-16: 星期{wd} (5=周六) is_open={is_open} {"✅" if not is_open else "❌ 应为False"}')
    
    cur.close()


def run():
    socket.setdefaulttimeout(30)
    log = setup_logger()
    
    log.info('=' * 60)
    log.info('fetch_trade_calendar_baostock_v1.0 — 全量交易日历采集')
    log.info('=' * 60)
    
    # 1. Baostock 登录
    bs.login()
    log.info('Baostock login OK')
    
    try:
        # 2. 拉取日历数据
        rows = fetch_calendar_from_baostock(log)
        
        # 3. 连接数据库并写入
        conn = get_db_conn()
        insert_calendar_to_db(conn, rows, log)
        
        # 4. 验证
        verify(conn, log)
        
        conn.close()
    finally:
        bs.logout()
    
    log.info('DONE')


if __name__ == "__main__":
    run()

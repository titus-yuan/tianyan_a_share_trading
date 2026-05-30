import { NextResponse } from "next/server";
import pool from "@/lib/db";

export async function GET() {
  try {
    const tables = [
      { source: "baostock", name: "daily_klines", label: "日线(前复权)" },
      { source: "easytdx", name: "easytdx_daily", label: "日线" },
      { source: "easytdx", name: "easytdx_daily_stat", label: "资金流向" },
      { source: "easytdx", name: "easytdx_finance", label: "财务" },
      { source: "easytdx", name: "easytdx_xdxr", label: "除权除息" },
      { source: "easytdx", name: "easytdx_stocks", label: "股票信息" },
    ];

    const sources: Record<string, { name: string; tables: Record<string, any> }> = {
      baostock: { name: "Baostock", tables: {} },
      easytdx: { name: "easy-tdx", tables: {} },
    };

    for (const t of tables) {
      const { rows } = await pool.query(`SELECT COUNT(*) as cnt FROM ${t.name}`);
      const cnt = parseInt(rows[0].cnt);
      const result: any = { rows: cnt, label: t.label };

      if (t.name === "easytdx_daily") {
        const range = await pool.query(
          `SELECT COUNT(DISTINCT stock_code) as stocks, MIN(trade_date) as date_from, MAX(trade_date) as date_to FROM ${t.name}`
        );
        result.stocks = parseInt(range.rows[0].stocks);
        result.date_from = range.rows[0].date_from;
        result.date_to = range.rows[0].date_to;
      } else if (t.name === "daily_klines") {
        const range = await pool.query(
          `SELECT COUNT(DISTINCT stock_code) as stocks, MIN(trade_date) as date_from, MAX(trade_date) as date_to FROM ${t.name}`
        );
        result.stocks = parseInt(range.rows[0].stocks);
        result.date_from = range.rows[0].date_from;
        result.date_to = range.rows[0].date_to;
      } else if (t.name === "easytdx_stocks") {
        result.stocks = cnt;
      }

      sources[t.source].tables[t.name] = result;
    }

    return NextResponse.json({ sources });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

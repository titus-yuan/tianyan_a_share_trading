import { NextRequest, NextResponse } from "next/server";
import pool from "@/lib/db";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const year = parseInt(searchParams.get("year") || String(new Date().getFullYear()));
  const month = parseInt(searchParams.get("month") || String(new Date().getMonth() + 1));

  const start = `${year}-${String(month).padStart(2, "0")}-01`;
  const end = new Date(year, month, 0);
  const endStr = `${year}-${String(month).padStart(2, "0")}-${String(end.getDate()).padStart(2, "0")}`;

  try {
    const { rows } = await pool.query(
      `SELECT trade_date::text as date, is_open, week_day
       FROM trade_calendar
       WHERE trade_date BETWEEN $1 AND $2
       ORDER BY trade_date`,
      [start, endStr]
    );

    const trading = rows.filter((r: any) => r.is_open).length;
    const nonTrading = rows.length - trading;

    return NextResponse.json({ year, month, days: rows, stats: { trading_days: trading, non_trading_days: nonTrading } });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

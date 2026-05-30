import { NextRequest, NextResponse } from "next/server";
import pool from "@/lib/db";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const market = searchParams.get("market") || "all";
  const search = searchParams.get("search") || "";
  const page = Math.max(1, parseInt(searchParams.get("page") || "1"));
  const pageSize = 20;

  let marketFilter = "";
  if (market === "sh") marketFilter = "AND d.stock_code LIKE 'sh.%'";
  else if (market === "sz") marketFilter = "AND d.stock_code LIKE 'sz.%'";

  const searchParams_arr: any[] = [];
  let searchFilter = "";
  if (search) {
    searchParams_arr.push(`%${search}%`, `%${search}%`);
    searchFilter = `AND (d.stock_code ILIKE $${searchParams_arr.length - 1} OR s.stock_name ILIKE $${searchParams_arr.length})`;
  }

  try {
    // 找最近两个交易日
    const datesRes = await pool.query(
      `SELECT DISTINCT trade_date::text as date FROM daily_klines ORDER BY date DESC LIMIT 2`
    );
    const dates = datesRes.rows.map((r: any) => r.date);
    if (dates.length < 2) {
      return NextResponse.json({ error: "数据不足（需要至少两个交易日）" }, { status: 404 });
    }
    const latest = dates[0];
    const prev = dates[1];

    // 计数
    const countSQL = `
      SELECT COUNT(DISTINCT d.stock_code)::int as total
      FROM daily_klines d
      JOIN stocks s ON d.stock_code = s.stock_code
      WHERE d.trade_date = '${latest}'
      ${marketFilter}
      ${searchFilter}
    `;
    const countRes = await pool.query(countSQL, searchParams_arr);
    const total = countRes.rows[0]?.total || 0;

    // 数据：JOIN 两天数据
    const offset = (page - 1) * pageSize;
    const dataSQL = `
      SELECT
        d.stock_code,
        s.stock_name,
        d.open,
        d.high,
        d.low,
        d.close,
        d.vol,
        d.amount,
        p.close AS prev_close,
        sv.float_market_cap
      FROM daily_klines d
      JOIN stocks s ON d.stock_code = s.stock_code
      LEFT JOIN daily_klines p ON d.stock_code = p.stock_code AND p.trade_date = '${prev}'
      LEFT JOIN stock_valuation sv ON d.stock_code = sv.stock_code AND sv.trade_date = d.trade_date
      WHERE d.trade_date = '${latest}'
      ${marketFilter}
      ${searchFilter}
      ORDER BY d.stock_code
      LIMIT ${pageSize} OFFSET ${offset}
    `;
    const dataRes = await pool.query(dataSQL, searchParams_arr);

    const rows = dataRes.rows.map((r: any) => {
      const prevClose = parseFloat(r.prev_close) || parseFloat(r.close);
      const change = parseFloat(r.close) - prevClose;
      const pctChg = prevClose !== 0 ? (change / prevClose) * 100 : 0;

      let turnover = null;
      if (r.float_market_cap && parseFloat(r.float_market_cap) > 0 && parseFloat(r.close) > 0) {
        const floatShares = parseFloat(r.float_market_cap) / parseFloat(r.close);
        turnover = (parseFloat(r.vol) / floatShares) * 100;
      }

      return {
        code: r.stock_code.replace(/^(sh|sz)\./, ""),
        name: r.stock_name,
        close: parseFloat(r.close).toFixed(2),
        open: parseFloat(r.open).toFixed(2),
        high: parseFloat(r.high).toFixed(2),
        low: parseFloat(r.low).toFixed(2),
        prev_close: prevClose.toFixed(2),
        change: change.toFixed(2),
        pct_chg: pctChg.toFixed(2),
        vol: parseFloat(r.vol),
        amount: parseFloat(r.amount),
        turnover: turnover != null ? turnover.toFixed(2) : null,
      };
    });

    return NextResponse.json({ date: latest, total, page, pageSize, totalPages: Math.ceil(total / pageSize), rows });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

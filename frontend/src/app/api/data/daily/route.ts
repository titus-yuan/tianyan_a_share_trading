import { NextRequest, NextResponse } from "next/server";
import pool from "@/lib/db";

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const source = searchParams.get("source") || "easytdx";
    const code = searchParams.get("code") || "";
    const adjust = searchParams.get("adjust") || "all";
    const page = Math.max(1, parseInt(searchParams.get("page") || "1"));
    const pageSize = Math.min(100, Math.max(1, parseInt(searchParams.get("pageSize") || "20")));
    const offset = (page - 1) * pageSize;

    let where = "";
    const params: any[] = [];

    if (source === "baostock") {
      // daily_klines: stock_code like 'sh.600000'
      if (code) {
        where += " WHERE stock_code = $1";
        params.push(code.includes(".") ? code : `sh.${code}`);
      }
      if (where) params[0] = params[0]; // re-index
      else where = " WHERE 1=1";

      const countSQL = `SELECT COUNT(*) as cnt FROM daily_klines${where.replace("WHERE 1=1", "")}${where === " WHERE 1=1" ? "" : ""}`;
      const dataSQL = `SELECT stock_code, trade_date, open, high, low, close, vol as volume, amount FROM daily_klines${where === " WHERE 1=1" ? "" : where} ORDER BY trade_date DESC LIMIT $${params.length + 1} OFFSET $${params.length + 2}`;

      const cntRes = await pool.query(
        where === " WHERE 1=1" ? "SELECT COUNT(*) as cnt FROM daily_klines" : countSQL,
        where === " WHERE 1=1" ? [] : params
      );
      const total = parseInt(cntRes.rows[0].cnt);
      const dataRes = await pool.query(dataSQL, [...params, pageSize, offset]);
      
      return NextResponse.json({ source: "baostock", data: dataRes.rows, total, page, pageSize });
    }

    // easytdx_daily
    if (code) {
      where += " WHERE d.stock_code = $1";
      params.push(code);
    }
    if (adjust !== "all") {
      where += where ? " AND d.adjust_type = $" + (params.length + 1) : " WHERE d.adjust_type = $1";
      params.push(adjust);
    }

    const countSQL = `SELECT COUNT(*) as cnt FROM easytdx_daily d${where}`;
    const dataSQL = `SELECT d.stock_code, s.stock_name, d.trade_date, d.adjust_type, d.open, d.high, d.low, d.close, d.volume, d.amount, d.float_shares FROM easytdx_daily d LEFT JOIN easytdx_stocks s ON d.stock_code = s.stock_code${where} ORDER BY d.trade_date DESC, d.stock_code ASC LIMIT $${params.length + 1} OFFSET $${params.length + 2}`;

    const cntRes = await pool.query(countSQL, params);
    const total = parseInt(cntRes.rows[0].cnt);
    const dataRes = await pool.query(dataSQL, [...params, pageSize, offset]);

    return NextResponse.json({ source: "easytdx", data: dataRes.rows, total, page, pageSize });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

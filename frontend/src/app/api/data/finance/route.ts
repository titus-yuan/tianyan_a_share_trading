import { NextRequest, NextResponse } from "next/server";
import pool from "@/lib/db";

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const code = searchParams.get("code") || "";
    const page = Math.max(1, parseInt(searchParams.get("page") || "1"));
    const pageSize = Math.min(100, Math.max(1, parseInt(searchParams.get("pageSize") || "20")));
    const offset = (page - 1) * pageSize;
    const params: any[] = [];

    let where = "";
    if (code) {
      where = " WHERE f.stock_code = $1";
      params.push(code);
    }

    const cntRes = await pool.query(`SELECT COUNT(*) as cnt FROM easytdx_finance f${where}`, params);
    const total = parseInt(cntRes.rows[0].cnt);
    const dataSQL = `SELECT f.stock_code, s.stock_name, f.report_date, f.eps, f.bvps, f.total_assets, f.net_assets, f.revenue, f.operating_profit, f.net_profit, f.operating_cf FROM easytdx_finance f LEFT JOIN easytdx_stocks s ON f.stock_code = s.stock_code${where} ORDER BY f.report_date DESC LIMIT $${params.length + 1} OFFSET $${params.length + 2}`;
    const dataRes = await pool.query(dataSQL, [...params, pageSize, offset]);

    return NextResponse.json({ data: dataRes.rows, total, page, pageSize });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

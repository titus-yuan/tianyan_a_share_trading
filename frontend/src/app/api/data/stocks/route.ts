import { NextRequest, NextResponse } from "next/server";
import pool from "@/lib/db";

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const search = searchParams.get("search") || "";
    const page = Math.max(1, parseInt(searchParams.get("page") || "1"));
    const pageSize = Math.min(100, Math.max(1, parseInt(searchParams.get("pageSize") || "20")));
    const offset = (page - 1) * pageSize;
    const params: any[] = [];

    let where = "";
    if (search) {
      where = " WHERE stock_code ILIKE $1 OR stock_name ILIKE $1";
      params.push(`%${search}%`);
    }

    const cntRes = await pool.query(`SELECT COUNT(*) as cnt FROM easytdx_stocks${where}`, params);
    const total = parseInt(cntRes.rows[0].cnt);
    const dataSQL = `SELECT stock_code, stock_name, market, industry_tdx, industry_sw, ipo_date FROM easytdx_stocks${where} ORDER BY stock_code ASC LIMIT $${params.length + 1} OFFSET $${params.length + 2}`;
    const dataRes = await pool.query(dataSQL, [...params, pageSize, offset]);

    return NextResponse.json({ data: dataRes.rows, total, page, pageSize });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

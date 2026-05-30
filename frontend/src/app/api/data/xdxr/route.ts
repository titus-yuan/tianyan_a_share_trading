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
      where = " WHERE x.stock_code = $1";
      params.push(code);
    }

    const cntRes = await pool.query(`SELECT COUNT(*) as cnt FROM easytdx_xdxr x${where}`, params);
    const total = parseInt(cntRes.rows[0].cnt);
    const dataSQL = `SELECT x.stock_code, s.stock_name, x.event_date, x.category, x.name, x.fenhong, x.songzhuangu, x.peigu FROM easytdx_xdxr x LEFT JOIN easytdx_stocks s ON x.stock_code = s.stock_code${where} ORDER BY x.event_date DESC LIMIT $${params.length + 1} OFFSET $${params.length + 2}`;
    const dataRes = await pool.query(dataSQL, [...params, pageSize, offset]);

    return NextResponse.json({ data: dataRes.rows, total, page, pageSize });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

import { NextRequest, NextResponse } from "next/server";
import pool from "@/lib/db";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const page = Math.max(1, parseInt(searchParams.get("page") || "1"));
  const limit = Math.min(50, Math.max(1, parseInt(searchParams.get("limit") || "20")));
  const q = searchParams.get("q") || "";
  const username = searchParams.get("username") || "";
  const offset = (page - 1) * limit;

  try {
    let whereClause = "";
    const params: any[] = [];
    let paramIdx = 1;

    if (q) { whereClause += ` AND (content ILIKE $${paramIdx} OR username ILIKE $${paramIdx})`; params.push(`%${q}%`); paramIdx++; }
    if (username) { whereClause += ` AND username = $${paramIdx}`; params.push(username); paramIdx++; }

    const countResult = await pool.query(
      `SELECT COUNT(*) as total FROM nitter_tweets WHERE 1=1${whereClause}`, params
    );
    const total = parseInt(countResult.rows[0].total);

    params.push(limit, offset);
    const { rows } = await pool.query(
      `SELECT id, tweet_id, username, display_name, content, posted_at::text, raw_url
       FROM nitter_tweets
       WHERE 1=1${whereClause}
       ORDER BY posted_at DESC
       LIMIT $${paramIdx} OFFSET $${paramIdx + 1}`,
      params
    );

    return NextResponse.json({
      tweets: rows,
      total,
      page,
      pages: Math.ceil(total / limit),
    });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

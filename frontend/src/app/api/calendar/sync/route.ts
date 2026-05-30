import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";
import pool from "@/lib/db";

const execAsync = promisify(exec);

export async function POST() {
  try {
    const script = "/mnt/data/code/a-share-collector/sync_holidays.py";
    const { stdout, stderr } = await execAsync(`python3 ${script}`, { timeout: 30000 });

    // 查最新审计记录
    const { rows } = await pool.query(
      `SELECT sync_type, status, rows_affected, message, started_at, finished_at
       FROM sync_log
       WHERE sync_type = 'calendar_holiday'
       ORDER BY started_at DESC LIMIT 1`
    );

    return NextResponse.json({
      success: true,
      output: stdout,
      error: stderr || null,
      log: rows[0] || null,
    });
  } catch (err: any) {
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}

// 查询最近同步记录
export async function GET() {
  try {
    const { rows } = await pool.query(
      `SELECT sync_type, status, rows_affected, message, started_at, finished_at
       FROM sync_log
       WHERE sync_type = 'calendar_holiday'
       ORDER BY started_at DESC LIMIT 5`
    );
    return NextResponse.json({ logs: rows });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

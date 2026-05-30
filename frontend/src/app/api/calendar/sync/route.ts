import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

export async function POST() {
  try {
    const script = "/mnt/data/code/a-share-collector/sync_holidays.py";
    const { stdout, stderr } = await execAsync(`python3 ${script}`, { timeout: 30000 });
    return NextResponse.json({ success: true, output: stdout, error: stderr || null });
  } catch (err: any) {
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}

import { NextResponse } from "next/server";

export async function POST() {
  return NextResponse.json({
    success: true,
    message: "同步已触发（演示模式 — 请联系司辰配置实际采集脚本）",
    new: 0,
  });
}

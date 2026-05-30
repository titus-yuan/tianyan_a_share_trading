import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({ status: "coming_soon", features: ["指数行情", "个股K线", "板块涨跌", "资金流向"] });
}

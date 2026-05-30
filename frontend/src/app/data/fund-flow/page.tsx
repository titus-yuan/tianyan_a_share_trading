
"use client";

import { useState } from "react";
import DataTable from "@/components/data/DataTable";

const COLS = [
  { key: "stock_code", label: "代码" },
  { key: "stock_name", label: "名称" },
  { key: "trade_date", label: "日期", render: (v: any) => v?.toString().slice(0, 10) },
  { key: "super_in", label: "超大买", render: (v: any) => v ? (v / 1e8).toFixed(2) + "亿" : "-" },
  { key: "super_out", label: "超大卖", render: (v: any) => v ? (v / 1e8).toFixed(2) + "亿" : "-" },
  { key: "large_in", label: "大单买", render: (v: any) => v ? (v / 1e8).toFixed(2) + "亿" : "-" },
  { key: "large_out", label: "大单卖", render: (v: any) => v ? (v / 1e8).toFixed(2) + "亿" : "-" },
  { key: "medium_in", label: "中单买", render: (v: any) => v ? (v / 1e8).toFixed(2) + "亿" : "-" },
  { key: "medium_out", label: "中单卖", render: (v: any) => v ? (v / 1e8).toFixed(2) + "亿" : "-" },
];

export default function FundFlowPage() {
  const [code, setCode] = useState("");
  const [trigger, setTrigger] = useState(0);

  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold text-zinc-200 mb-4">资金流向 <span className="text-xs text-zinc-500 ml-2">easy-tdx</span></h2>
      <div className="flex gap-3 mb-4">
        <input type="text" placeholder="输入代码" value={code} onChange={(e) => setCode(e.target.value)} onKeyDown={(e) => e.key === "Enter" && setTrigger((t) => t + 1)} className="bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-sm text-zinc-200 w-40" />
        <button onClick={() => setTrigger((t) => t + 1)} className="px-3 py-1.5 bg-emerald-700 text-white rounded text-sm hover:bg-emerald-600">搜索</button>
      </div>
      <DataTable endpoint={`/api/data/fund-flow?code=${code}`} columns={COLS} searchTrigger={trigger} />
    </div>
  );
}

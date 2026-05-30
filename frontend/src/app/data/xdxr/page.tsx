
"use client";

import { useState } from "react";
import DataTable from "@/components/data/DataTable";

const COLS = [
  { key: "stock_code", label: "代码" },
  { key: "stock_name", label: "名称" },
  { key: "event_date", label: "日期", render: (v: any) => v?.toString().slice(0, 10) },
  { key: "name", label: "类型" },
  { key: "fenhong", label: "分红(元/股)", render: (v: any) => v != null ? v.toFixed(2) : "-" },
  { key: "songzhuangu", label: "送转股", render: (v: any) => v != null && v > 0 ? v.toFixed(1) + "股" : "-" },
  { key: "peigu", label: "配股", render: (v: any) => v != null && v > 0 ? v.toFixed(1) + "股" : "-" },
];

export default function XdxrPage() {
  const [code, setCode] = useState("");
  const [trigger, setTrigger] = useState(0);

  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold text-zinc-200 mb-4">除权除息 <span className="text-xs text-zinc-500 ml-2">easy-tdx</span></h2>
      <div className="flex gap-3 mb-4">
        <input type="text" placeholder="输入代码" value={code} onChange={(e) => setCode(e.target.value)} onKeyDown={(e) => e.key === "Enter" && setTrigger((t) => t + 1)} className="bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-sm text-zinc-200 w-40" />
        <button onClick={() => setTrigger((t) => t + 1)} className="px-3 py-1.5 bg-emerald-700 text-white rounded text-sm hover:bg-emerald-600">搜索</button>
      </div>
      <DataTable endpoint={`/api/data/xdxr?code=${code}`} columns={COLS} searchTrigger={trigger} />
    </div>
  );
}


"use client";

import { useState } from "react";
import DataTable from "@/components/data/DataTable";

const COLS = [
  { key: "stock_code", label: "代码" },
  { key: "stock_name", label: "名称" },
  { key: "market", label: "市场", render: (v: any) => v === "SH" ? "沪市" : v === "SZ" ? "深市" : v || "-" },
  { key: "industry_tdx", label: "通达信行业" },
  { key: "industry_sw", label: "申万行业" },
  { key: "ipo_date", label: "上市日期", render: (v: any) => v?.toString().slice(0, 10) || "-" },
];

export default function StocksPage() {
  const [search, setSearch] = useState("");
  const [trigger, setTrigger] = useState(0);

  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold text-zinc-200 mb-4">股票信息 <span className="text-xs text-zinc-500 ml-2">easy-tdx</span></h2>
      <div className="flex gap-3 mb-4">
        <input type="text" placeholder="搜索代码或名称" value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => e.key === "Enter" && setTrigger((t) => t + 1)} className="bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-sm text-zinc-200 w-48" />
        <button onClick={() => setTrigger((t) => t + 1)} className="px-3 py-1.5 bg-emerald-700 text-white rounded text-sm hover:bg-emerald-600">搜索</button>
      </div>
      <DataTable endpoint={`/api/data/stocks?search=${search}`} columns={COLS} searchTrigger={trigger} />
    </div>
  );
}

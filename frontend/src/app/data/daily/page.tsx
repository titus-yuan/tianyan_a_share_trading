
"use client";

import { useState } from "react";
import DataTable from "@/components/data/DataTable";

const DAILY_COLS = [
  { key: "stock_code", label: "代码" },
  { key: "stock_name", label: "名称" },
  { key: "trade_date", label: "日期", render: (v: any) => v?.toString().slice(0, 10) },
  { key: "adjust_type", label: "复权", hide: "baostock" },
  { key: "open", label: "开盘" },
  { key: "high", label: "最高" },
  { key: "low", label: "最低" },
  { key: "close", label: "收盘" },
  { key: "volume", label: "成交量", render: (v: any) => v ? (v / 10000).toFixed(0) + "万" : "-" },
  { key: "amount", label: "成交额", render: (v: any) => v ? (v / 1e8).toFixed(2) + "亿" : "-" },
  { key: "float_shares", label: "流通股本", render: (v: any) => v ? (v / 1e8).toFixed(2) + "亿" : "-", hide: "baostock" },
];

const SOURCES = [
  { key: "easytdx", name: "easy-tdx" },
  { key: "baostock", name: "Baostock" },
];

const ADJUSTS = [
  { key: "all", name: "全部" },
  { key: "none", name: "不复权" },
  { key: "qfq", name: "前复权" },
];

export default function DailyPage() {
  const [source, setSource] = useState("easytdx");
  const [adjust, setAdjust] = useState("all");
  const [code, setCode] = useState("");
  const [searchTrigger, setSearchTrigger] = useState(0);

  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold text-zinc-200 mb-4">日线数据</h2>
      <div className="flex gap-3 mb-4 flex-wrap">
        <select value={source} onChange={(e) => setSource(e.target.value)} className="bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-sm text-zinc-200">
          {SOURCES.map((s) => <option key={s.key} value={s.key}>{s.name}</option>)}
        </select>
        {source === "easytdx" && (
          <select value={adjust} onChange={(e) => setAdjust(e.target.value)} className="bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-sm text-zinc-200">
            {ADJUSTS.map((a) => <option key={a.key} value={a.key}>{a.name}</option>)}
          </select>
        )}
        <input
          type="text"
          placeholder="输入代码 (如 600000)"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && setSearchTrigger((t) => t + 1)}
          className="bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-sm text-zinc-200 w-40"
        />
        <button onClick={() => setSearchTrigger((t) => t + 1)} className="px-3 py-1.5 bg-emerald-700 text-white rounded text-sm hover:bg-emerald-600">搜索</button>
      </div>
      <DataTable
        endpoint={`/api/data/daily?source=${source}&adjust=${adjust}&code=${code}`}
        columns={DAILY_COLS.filter((c) => !(c.hide && c.hide === source))}
        searchTrigger={searchTrigger}
      />
    </div>
  );
}

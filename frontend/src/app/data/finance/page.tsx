
"use client";

import { useState, useEffect } from "react";

export default function FinancePage() {
  const [code, setCode] = useState("");
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/data/finance?code=${code}`)
      .then((r) => r.json())
      .then((d) => { setData(d.data || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, [code]);

  const handleSearch = () => { setCode(code); /* trigger useEffect via key change */ };

  const cards = [
    { key: "eps", label: "每股收益", unit: "元", icon: "📊" },
    { key: "bvps", label: "每股净资产", unit: "元", icon: "💎" },
    { key: "total_assets", label: "总资产", unit: "亿", icon: "🏢", div: 1e8 },
    { key: "net_assets", label: "净资产", unit: "亿", icon: "📋", div: 1e8 },
    { key: "revenue", label: "营业收入", unit: "亿", icon: "💰", div: 1e8 },
    { key: "operating_profit", label: "营业利润", unit: "亿", icon: "📈", div: 1e8 },
    { key: "net_profit", label: "净利润", unit: "亿", icon: "✅", div: 1e8 },
    { key: "operating_cf", label: "经营现金流", unit: "亿", icon: "💵", div: 1e8 },
  ];

  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold text-zinc-200 mb-4">财务数据 <span className="text-xs text-zinc-500 ml-2">easy-tdx</span></h2>
      <div className="flex gap-3 mb-4">
        <input type="text" placeholder="输入代码 (如 600000)" value={code} onChange={(e) => setCode(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleSearch()} className="bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-sm text-zinc-200 w-40" />
        <button onClick={handleSearch} className="px-3 py-1.5 bg-emerald-700 text-white rounded text-sm hover:bg-emerald-600">搜索</button>
      </div>
      {loading && <div className="text-zinc-400 text-sm">加载中...</div>}
      {data.length === 0 && !loading && <div className="text-zinc-500 text-sm">输入代码搜索</div>}
      {data.map((item, i) => (
        <div key={i} className="border border-zinc-700 rounded-lg p-4 bg-zinc-800/50 mb-4">
          <div className="text-sm text-zinc-400 mb-3">{item.stock_name || item.stock_code} — 报告期: {item.report_date?.toString().slice(0, 10)}</div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {cards.map((c) => {
              const val = item[c.key];
              const display = val != null ? (c.div ? (val / c.div).toFixed(2) : val.toFixed(2)) : "-";
              return (
                <div key={c.key} className="border border-zinc-700 rounded p-3 bg-zinc-800">
                  <div className="text-zinc-500 text-xs mb-1">{c.icon} {c.label}</div>
                  <div className="text-zinc-200 font-medium">{display} {c.unit}</div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

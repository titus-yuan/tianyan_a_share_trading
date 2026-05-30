'use client';

import { useState, useEffect } from "react";
import MonthView from "@/components/calendar/month-view";
import type { CalendarMonth } from "@/lib/types";

export default function CalendarPage() {
  const [data, setData] = useState<CalendarMonth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [month, setMonth] = useState(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  });

  const [year, mon] = month.split("-").map(Number);

  useEffect(() => {
    setLoading(true);
    setError("");
    fetch(`/api/calendar?year=${year}&month=${mon}`)
      .then((r) => { if (!r.ok) throw new Error("加载失败"); return r.json(); })
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [month]);

  const goMonth = (delta: number) => {
    const d = new Date(year, mon - 1 + delta, 1);
    setMonth(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`);
  };

  const monthLabel = `${year}年 ${mon}月`;

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold tracking-tight">交易日历</h1>
        <div className="flex items-center gap-2">
          <button onClick={() => goMonth(-1)} className="px-3 py-1.5 text-sm rounded-lg border border-border hover:bg-surface-hover transition-colors">◀</button>
          <span className="text-sm font-medium min-w-[100px] text-center">{monthLabel}</span>
          <button onClick={() => goMonth(1)} className="px-3 py-1.5 text-sm rounded-lg border border-border hover:bg-surface-hover transition-colors">▶</button>
        </div>
      </div>

      {loading && (
        <div className="grid grid-cols-7 gap-1 animate-pulse">
          {Array.from({ length: 42 }).map((_, i) => (
            <div key={i} className="aspect-square rounded-lg bg-border/50" />
          ))}
        </div>
      )}

      {error && (
        <div className="text-center py-12 text-ink-muted">
          <p>加载失败: {error}</p>
          <button onClick={() => setMonth(month)} className="mt-2 text-accent text-sm hover:underline">重试</button>
        </div>
      )}

      {data && !loading && (
        <>
          <MonthView data={data} />
          <div className="mt-4 flex items-center gap-4 text-xs text-ink-muted">
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-accent inline-block" /> 交易日 ({data.stats.trading_days}天)</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-border inline-block" /> 非交易日 ({data.stats.non_trading_days}天)</span>
          </div>
        </>
      )}
    </div>
  );
}

'use client';

import { useState, useEffect } from "react";
import MonthView from "@/components/calendar/month-view";
import type { CalendarMonth } from "@/lib/types";
import { ArrowsClockwise } from "phosphor-react";

export default function CalendarPage() {
  const [data, setData] = useState<CalendarMonth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [syncing, setSyncing] = useState(false);
  const [month, setMonth] = useState(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  });

  const [year, mon] = month.split("-").map(Number);

  const fetchCalendar = () => {
    setLoading(true);
    setError("");
    fetch(`/api/calendar?year=${year}&month=${mon}`)
      .then((r) => { if (!r.ok) throw new Error("加载失败"); return r.json(); })
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchCalendar(); }, [month]);

  const goMonth = (delta: number) => {
    const d = new Date(year, mon - 1 + delta, 1);
    setMonth(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`);
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      const r = await fetch("/api/calendar/sync", { method: "POST" });
      const d = await r.json();
      if (d.success) {
        alert("同步完成");
        fetchCalendar();
      } else {
        alert("同步失败: " + (d.error || "未知错误"));
      }
    } catch {
      alert("同步请求失败");
    } finally {
      setSyncing(false);
    }
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
          <button
            onClick={handleSync}
            disabled={syncing}
            className="ml-4 px-3 py-1.5 text-sm rounded-lg border border-border hover:bg-surface-hover transition-colors disabled:opacity-50 flex items-center gap-1"
          >
            <ArrowsClockwise size={14} className={syncing ? "animate-spin" : ""} />
            {syncing ? "同步中…" : "同步"}
          </button>
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
          <button onClick={fetchCalendar} className="mt-2 text-accent text-sm hover:underline">重试</button>
        </div>
      )}

      {data && !loading && (
        <>
          <MonthView data={data} />
          <div className="mt-4 flex items-center gap-4 text-xs text-ink-muted">
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-emerald-500 inline-block" /> 交易日 ({data.stats.trading_days}天)</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-50 border border-red-200 inline-block" /> 法定假日 ({data.days.filter(d => !!d.holiday_name).length}天)</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-gray-100 inline-block" /> 周末 ({data.stats.non_trading_days - data.days.filter(d => !!d.holiday_name).length}天)</span>
          </div>
        </>
      )}
    </div>
  );
}

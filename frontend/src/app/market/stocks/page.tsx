"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { MagnifyingGlass, CaretLeft, CaretRight } from "phosphor-react";

interface StockRow {
  code: string;
  name: string;
  close: string;
  open: string;
  high: string;
  low: string;
  prev_close: string;
  change: string;
  pct_chg: string;
  vol: number;
  amount: number;
  turnover: string | null;
}

interface ApiResponse {
  date: string;
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  rows: StockRow[];
  error?: string;
}

const TABS = [
  { key: "all", label: "全部" },
  { key: "sh", label: "沪市" },
  { key: "sz", label: "深市" },
];

function fmtVol(v: number): string {
  if (v >= 1e8) return (v / 1e8).toFixed(2) + "亿";
  return (v / 1e4).toFixed(0) + "万";
}

function fmtAmount(a: number): string {
  if (a >= 1e8) return (a / 1e8).toFixed(2) + "亿";
  return (a / 1e4).toFixed(0) + "万";
}

function StocksContent() {
  const router = useRouter();
  const sp = useSearchParams();

  const [market, setMarket] = useState(sp.get("market") || "all");
  const [search, setSearch] = useState(sp.get("search") || "");
  const [page, setPage] = useState(parseInt(sp.get("page") || "1"));

  const [data, setData] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError("");
    const params = new URLSearchParams({ market, page: String(page) });
    if (search) params.set("search", search);
    try {
      const res = await fetch(`/api/stocks?${params}`);
      const json: ApiResponse = await res.json();
      if (json.error) setError(json.error);
      else setData(json);
    } catch {
      setError("网络错误");
    }
    setLoading(false);
  }, [market, search, page]);

  useEffect(() => {
    fetchData();
    const u = new URLSearchParams({ market, page: String(page) });
    if (search) u.set("search", search);
    router.replace(`/market/stocks?${u}`, { scroll: false });
  }, [market, search, page]); // eslint-disable-line

  const handleTab = (key: string) => { setMarket(key); setPage(1); };
  const handleSearch = (e: React.FormEvent) => { e.preventDefault(); setPage(1); fetchData(); };

  return (
    <div className="p-4 max-w-full">
      <h1 className="text-xl font-semibold text-ink-primary mb-3">个股行情</h1>

      {/* Tab 栏 */}
      <div className="flex items-center gap-1 mb-3 bg-surface-subtle rounded-lg p-0.5 w-fit">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => handleTab(t.key)}
            className={`px-4 py-1.5 text-sm rounded-md transition-colors ${
              market === t.key ? "bg-white text-accent font-medium shadow-sm" : "text-ink-secondary hover:text-ink-primary"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* 搜索栏 */}
      <form onSubmit={handleSearch} className="flex items-center gap-2 mb-4 max-w-sm">
        <div className="relative flex-1">
          <MagnifyingGlass size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-tertiary" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索代码或名称..."
            className="w-full pl-9 pr-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
          />
        </div>
        <button type="submit" className="px-4 py-2 bg-accent text-white text-sm rounded-lg hover:bg-emerald-600 transition-colors">
          搜索
        </button>
      </form>

      {/* 错误 */}
      {error && <div className="text-red-500 text-sm mb-3">⚠ {error}</div>}

      {/* 数据日期 */}
      {data?.date && <div className="text-xs text-ink-tertiary mb-2">数据日期: {data.date} · 共 {data.total} 只</div>}

      {/* 表格 */}
      <div className="overflow-x-auto border border-border rounded-lg">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-surface-subtle text-ink-secondary text-xs">
              <th className="text-left px-3 py-2.5 font-medium sticky left-0 bg-surface-subtle">代码</th>
              <th className="text-left px-3 py-2.5 font-medium">名称</th>
              <th className="text-right px-3 py-2.5 font-medium">涨幅%</th>
              <th className="text-right px-3 py-2.5 font-medium">涨跌额</th>
              <th className="text-right px-3 py-2.5 font-medium">最新价</th>
              <th className="text-right px-3 py-2.5 font-medium">成交量</th>
              <th className="text-right px-3 py-2.5 font-medium">成交额</th>
              <th className="text-right px-3 py-2.5 font-medium">换手率</th>
              <th className="text-right px-3 py-2.5 font-medium">今开</th>
              <th className="text-right px-3 py-2.5 font-medium">最高</th>
              <th className="text-right px-3 py-2.5 font-medium">最低</th>
              <th className="text-right px-3 py-2.5 font-medium">昨收</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={12} className="text-center py-8 text-ink-tertiary">加载中...</td></tr>
            )}
            {!loading && (!data || data.rows.length === 0) && (
              <tr><td colSpan={12} className="text-center py-8 text-ink-tertiary">无数据</td></tr>
            )}
            {!loading && data?.rows.map((r) => {
              const pct = parseFloat(r.pct_chg);
              const isUp = pct > 0;
              const isDown = pct < 0;
              const colorClass = isUp ? "text-red-500" : isDown ? "text-green-500" : "text-ink-secondary";
              return (
                <tr key={r.code} className="border-t border-border hover:bg-surface-hover transition-colors cursor-pointer"
                  onClick={() => router.push(`/market/stocks/${r.code}`)}>
                  <td className="px-3 py-2 font-mono text-ink-secondary sticky left-0 bg-white">{r.code}</td>
                  <td className="px-3 py-2 font-medium">{r.name}</td>
                  <td className={`px-3 py-2 text-right font-mono ${colorClass}`}>{isUp ? "+" : ""}{r.pct_chg}%</td>
                  <td className={`px-3 py-2 text-right font-mono ${colorClass}`}>{isUp ? "+" : ""}{r.change}</td>
                  <td className={`px-3 py-2 text-right font-mono font-medium ${colorClass}`}>{r.close}</td>
                  <td className="px-3 py-2 text-right font-mono text-ink-secondary">{fmtVol(r.vol)}</td>
                  <td className="px-3 py-2 text-right font-mono text-ink-secondary">{fmtAmount(r.amount)}</td>
                  <td className="px-3 py-2 text-right font-mono text-ink-secondary">{r.turnover ? `${r.turnover}%` : "-"}</td>
                  <td className="px-3 py-2 text-right font-mono text-ink-secondary">{r.open}</td>
                  <td className="px-3 py-2 text-right font-mono text-red-500">{r.high}</td>
                  <td className="px-3 py-2 text-right font-mono text-green-500">{r.low}</td>
                  <td className="px-3 py-2 text-right font-mono text-ink-secondary">{r.prev_close}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* 分页 */}
      {data && data.totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 mt-4 text-sm text-ink-secondary">
          <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}
            className="p-1.5 rounded hover:bg-surface-hover disabled:opacity-30">
            <CaretLeft size={16} />
          </button>
          <span>{data.page} / {data.totalPages}</span>
          <button onClick={() => setPage((p) => Math.min(data.totalPages, p + 1))} disabled={page >= data.totalPages}
            className="p-1.5 rounded hover:bg-surface-hover disabled:opacity-30">
            <CaretRight size={16} />
          </button>
        </div>
      )}
    </div>
  );
}

export default function StocksPage() {
  return (
    <Suspense fallback={<div className="p-4 text-ink-tertiary">加载中...</div>}>
      <StocksContent />
    </Suspense>
  );
}

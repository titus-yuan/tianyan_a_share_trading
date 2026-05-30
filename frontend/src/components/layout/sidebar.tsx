'use client';

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Calendar, Newspaper, ChartLineUp, Database } from "phosphor-react";
import { useState, useRef, useEffect } from "react";

export default function Sidebar() {
  const pathname = usePathname();
  const [marketOpen, setMarketOpen] = useState(false);
  const [newsOpen, setNewsOpen] = useState(false);
  const [dataOpen, setDataOpen] = useState(false);
  const marketRef = useRef<HTMLDivElement>(null);
  const newsRef = useRef<HTMLDivElement>(null);
  const dataRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (marketRef.current && !marketRef.current.contains(e.target as Node)) setMarketOpen(false);
      if (newsRef.current && !newsRef.current.contains(e.target as Node)) setNewsOpen(false);
      if (dataRef.current && !dataRef.current.contains(e.target as Node)) setDataOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const isMarketActive = pathname === "/market" || pathname.startsWith("/market/");
  const isNewsActive = pathname === "/news" || pathname.startsWith("/news/");
  const isDataActive = pathname === "/data" || pathname.startsWith("/data/");

  return (
    <aside className="w-14 bg-white border-r border-border flex flex-col items-center py-3 gap-1 shrink-0">
      {/* 交易日历 */}
      <Link
        href="/calendar"
        title="交易日历"
        className={`w-10 h-10 flex items-center justify-center rounded-lg transition-colors ${
          pathname.startsWith("/calendar") ? "bg-emerald-50 text-accent" : "text-ink-muted hover:bg-surface-hover hover:text-ink-secondary"
        }`}
      >
        <Calendar size={20} weight={pathname.startsWith("/calendar") ? "fill" : "regular"} />
      </Link>

      {/* 新闻 — 下拉 */}
      <div ref={newsRef} className="relative">
        <button
          onClick={() => { setNewsOpen(!newsOpen); setMarketOpen(false); setDataOpen(false); }}
          title="新闻"
          className={`w-10 h-10 flex items-center justify-center rounded-lg transition-colors ${
            isNewsActive ? "bg-emerald-50 text-accent" : "text-ink-muted hover:bg-surface-hover hover:text-ink-secondary"
          }`}
        >
          <Newspaper size={20} weight={isNewsActive ? "fill" : "regular"} />
        </button>
        {newsOpen && (
          <div className="absolute left-full top-0 ml-1 bg-white border border-border rounded-lg shadow-sm py-1 min-w-[120px] z-50">
            <Link href="/news/tweets" onClick={() => setNewsOpen(false)}
              className={`block px-4 py-2 text-sm whitespace-nowrap ${
                pathname === "/news/tweets" ? "text-accent bg-emerald-50" : "text-ink-secondary hover:bg-surface-hover"
              }`}>
              𝕏 推文
            </Link>
          </div>
        )}
      </div>

      {/* 行情 — 下拉 */}
      <div ref={marketRef} className="relative">
        <button
          onClick={() => { setMarketOpen(!marketOpen); setNewsOpen(false); setDataOpen(false); }}
          title="行情"
          className={`w-10 h-10 flex items-center justify-center rounded-lg transition-colors ${
            isMarketActive ? "bg-emerald-50 text-accent" : "text-ink-muted hover:bg-surface-hover hover:text-ink-secondary"
          }`}
        >
          <ChartLineUp size={20} weight={isMarketActive ? "fill" : "regular"} />
        </button>
        {marketOpen && (
          <div className="absolute left-full top-0 ml-1 bg-white border border-border rounded-lg shadow-sm py-1 min-w-[120px] z-50">
            <Link href="/market/stocks" onClick={() => setMarketOpen(false)}
              className={`block px-4 py-2 text-sm whitespace-nowrap ${
                pathname.startsWith("/market/stocks") ? "text-accent bg-emerald-50" : "text-ink-secondary hover:bg-surface-hover"
              }`}>
              📈 个股
            </Link>
          </div>
        )}
      </div>

      {/* 数据源 — 下拉 🆕 */}
      <div ref={dataRef} className="relative">
        <button
          onClick={() => { setDataOpen(!dataOpen); setMarketOpen(false); setNewsOpen(false); }}
          title="数据源"
          className={`w-10 h-10 flex items-center justify-center rounded-lg transition-colors ${
            isDataActive ? "bg-emerald-50 text-accent" : "text-ink-muted hover:bg-surface-hover hover:text-ink-secondary"
          }`}
        >
          <Database size={20} weight={isDataActive ? "fill" : "regular"} />
        </button>
        {dataOpen && (
          <div className="absolute left-full top-0 ml-1 bg-white border border-border rounded-lg shadow-sm py-1 min-w-[130px] z-50">
            <Link href="/data/overview" onClick={() => setDataOpen(false)}
              className={`block px-4 py-2 text-sm whitespace-nowrap ${
                pathname === "/data/overview" ? "text-accent bg-emerald-50" : "text-ink-secondary hover:bg-surface-hover"
              }`}>
              📋 数据总览
            </Link>
            <Link href="/data/daily" onClick={() => setDataOpen(false)}
              className={`block px-4 py-2 text-sm whitespace-nowrap ${
                pathname === "/data/daily" ? "text-accent bg-emerald-50" : "text-ink-secondary hover:bg-surface-hover"
              }`}>
              📊 日线数据
            </Link>
            <Link href="/data/fund-flow" onClick={() => setDataOpen(false)}
              className={`block px-4 py-2 text-sm whitespace-nowrap ${
                pathname === "/data/fund-flow" ? "text-accent bg-emerald-50" : "text-ink-secondary hover:bg-surface-hover"
              }`}>
              💰 资金流向
            </Link>
            <Link href="/data/finance" onClick={() => setDataOpen(false)}
              className={`block px-4 py-2 text-sm whitespace-nowrap ${
                pathname === "/data/finance" ? "text-accent bg-emerald-50" : "text-ink-secondary hover:bg-surface-hover"
              }`}>
              💼 财务数据
            </Link>
            <Link href="/data/xdxr" onClick={() => setDataOpen(false)}
              className={`block px-4 py-2 text-sm whitespace-nowrap ${
                pathname === "/data/xdxr" ? "text-accent bg-emerald-50" : "text-ink-secondary hover:bg-surface-hover"
              }`}>
              🔄 除权除息
            </Link>
            <Link href="/data/stocks" onClick={() => setDataOpen(false)}
              className={`block px-4 py-2 text-sm whitespace-nowrap ${
                pathname === "/data/stocks" ? "text-accent bg-emerald-50" : "text-ink-secondary hover:bg-surface-hover"
              }`}>
              🏷️ 股票信息
            </Link>
          </div>
        )}
      </div>
    </aside>
  );
}

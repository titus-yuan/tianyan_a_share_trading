'use client';

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Calendar, Newspaper, ChartLineUp, Database, CaretDown } from "phosphor-react";
import { useState, useRef, useEffect } from "react";

export default function TopNav() {
  const pathname = usePathname();
  const [newsOpen, setNewsOpen] = useState(false);
  const [marketOpen, setMarketOpen] = useState(false);
  const [dataOpen, setDataOpen] = useState(false);
  const newsRef = useRef<HTMLDivElement>(null);
  const marketRef = useRef<HTMLDivElement>(null);
  const dataRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (newsRef.current && !newsRef.current.contains(e.target as Node)) setNewsOpen(false);
      if (marketRef.current && !marketRef.current.contains(e.target as Node)) setMarketOpen(false);
      if (dataRef.current && !dataRef.current.contains(e.target as Node)) setDataOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const isMarketActive = pathname === "/market" || pathname.startsWith("/market/");
  const isDataActive = pathname === "/data" || pathname.startsWith("/data/");

  return (
    <header className="h-14 bg-white border-b border-border flex items-center px-4 shrink-0">
      <Link href="/" className="text-lg font-semibold tracking-tight text-ink-primary mr-8">
        天演 Tianyan
      </Link>
      <nav className="flex items-center gap-1">
        {/* 交易日历 — 普通链接 */}
        <Link
          href="/calendar"
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${
            pathname.startsWith("/calendar")
              ? "bg-emerald-50 text-accent font-medium"
              : "text-ink-secondary hover:bg-surface-hover hover:text-ink-primary"
          }`}
        >
          <Calendar size={16} weight={pathname.startsWith("/calendar") ? "fill" : "regular"} />
          交易日历
        </Link>

        {/* 新闻 — 下拉 */}
        <div ref={newsRef} className="relative">
          <button
            onClick={() => { setNewsOpen(!newsOpen); setMarketOpen(false); setDataOpen(false); }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${
              pathname.startsWith("/news/")
                ? "bg-emerald-50 text-accent font-medium"
                : "text-ink-secondary hover:bg-surface-hover hover:text-ink-primary"
            }`}
          >
            <Newspaper size={16} weight={pathname.startsWith("/news/") ? "fill" : "regular"} />
            新闻
            <CaretDown size={12} className={`transition-transform ${newsOpen ? "rotate-180" : ""}`} />
          </button>
          {newsOpen && (
            <div className="absolute top-full left-0 mt-1 bg-white border border-border rounded-lg shadow-sm py-1 min-w-[120px] z-50">
              <Link href="/news/tweets" onClick={() => setNewsOpen(false)}
                className={`block px-4 py-2 text-sm ${pathname === "/news/tweets" ? "text-accent bg-emerald-50" : "text-ink-secondary hover:bg-surface-hover"}`}>
                𝕏 推文
              </Link>
            </div>
          )}
        </div>

        {/* 行情 — 下拉 */}
        <div ref={marketRef} className="relative">
          <button
            onClick={() => { setMarketOpen(!marketOpen); setNewsOpen(false); setDataOpen(false); }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${
              isMarketActive
                ? "bg-emerald-50 text-accent font-medium"
                : "text-ink-secondary hover:bg-surface-hover hover:text-ink-primary"
            }`}
          >
            <ChartLineUp size={16} weight={isMarketActive ? "fill" : "regular"} />
            行情
            <CaretDown size={12} className={`transition-transform ${marketOpen ? "rotate-180" : ""}`} />
          </button>
          {marketOpen && (
            <div className="absolute top-full left-0 mt-1 bg-white border border-border rounded-lg shadow-sm py-1 min-w-[120px] z-50">
              <Link href="/market/stocks" onClick={() => setMarketOpen(false)}
                className={`block px-4 py-2 text-sm ${pathname.startsWith("/market/stocks") ? "text-accent bg-emerald-50" : "text-ink-secondary hover:bg-surface-hover"}`}>
                📈 个股
              </Link>
            </div>
          )}
        </div>

        {/* 数据源 — 下拉 🆕 */}
        <div ref={dataRef} className="relative">
          <button
            onClick={() => { setDataOpen(!dataOpen); setMarketOpen(false); setNewsOpen(false); }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${
              isDataActive
                ? "bg-emerald-50 text-accent font-medium"
                : "text-ink-secondary hover:bg-surface-hover hover:text-ink-primary"
            }`}
          >
            <Database size={16} weight={isDataActive ? "fill" : "regular"} />
            数据源
            <CaretDown size={12} className={`transition-transform ${dataOpen ? "rotate-180" : ""}`} />
          </button>
          {dataOpen && (
            <div className="absolute top-full left-0 mt-1 bg-white border border-border rounded-lg shadow-sm py-1 min-w-[130px] z-50">
              <Link href="/data/overview" onClick={() => setDataOpen(false)}
                className={`block px-4 py-2 text-sm ${pathname === "/data/overview" ? "text-accent bg-emerald-50" : "text-ink-secondary hover:bg-surface-hover"}`}>
                📋 数据总览
              </Link>
              <Link href="/data/daily" onClick={() => setDataOpen(false)}
                className={`block px-4 py-2 text-sm ${pathname === "/data/daily" ? "text-accent bg-emerald-50" : "text-ink-secondary hover:bg-surface-hover"}`}>
                📊 日线数据
              </Link>
              <Link href="/data/fund-flow" onClick={() => setDataOpen(false)}
                className={`block px-4 py-2 text-sm ${pathname === "/data/fund-flow" ? "text-accent bg-emerald-50" : "text-ink-secondary hover:bg-surface-hover"}`}>
                💰 资金流向
              </Link>
              <Link href="/data/finance" onClick={() => setDataOpen(false)}
                className={`block px-4 py-2 text-sm ${pathname === "/data/finance" ? "text-accent bg-emerald-50" : "text-ink-secondary hover:bg-surface-hover"}`}>
                💼 财务数据
              </Link>
              <Link href="/data/xdxr" onClick={() => setDataOpen(false)}
                className={`block px-4 py-2 text-sm ${pathname === "/data/xdxr" ? "text-accent bg-emerald-50" : "text-ink-secondary hover:bg-surface-hover"}`}>
                🔄 除权除息
              </Link>
              <Link href="/data/stocks" onClick={() => setDataOpen(false)}
                className={`block px-4 py-2 text-sm ${pathname === "/data/stocks" ? "text-accent bg-emerald-50" : "text-ink-secondary hover:bg-surface-hover"}`}>
                🏷️ 股票信息
              </Link>
            </div>
          )}
        </div>
      </nav>
    </header>
  );
}

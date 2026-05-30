'use client';

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Calendar, Newspaper, ChartLineUp, CaretRight } from "phosphor-react";
import { useState, useRef, useEffect } from "react";

export default function Sidebar() {
  const pathname = usePathname();
  const [marketOpen, setMarketOpen] = useState(false);
  const [newsOpen, setNewsOpen] = useState(false);
  const marketRef = useRef<HTMLDivElement>(null);
  const newsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (marketRef.current && !marketRef.current.contains(e.target as Node)) setMarketOpen(false);
      if (newsRef.current && !newsRef.current.contains(e.target as Node)) setNewsOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const isMarketActive = pathname === "/market" || pathname.startsWith("/market/");
  const isNewsActive = pathname === "/news" || pathname.startsWith("/news/");

  return (
    <aside className="w-14 bg-white border-r border-border flex flex-col items-center py-3 gap-1 shrink-0">
      {/* 交易日历 — 普通链接 */}
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
          onClick={() => { setNewsOpen(!newsOpen); setMarketOpen(false); }}
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
          onClick={() => { setMarketOpen(!marketOpen); setNewsOpen(false); }}
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
    </aside>
  );
}

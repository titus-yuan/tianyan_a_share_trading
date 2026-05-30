'use client';

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Calendar, Newspaper, ChartLineUp, CaretDown } from "phosphor-react";
import { useState, useRef, useEffect } from "react";

export default function TopNav() {
  const pathname = usePathname();
  const [newsOpen, setNewsOpen] = useState(false);
  const [marketOpen, setMarketOpen] = useState(false);
  const newsRef = useRef<HTMLDivElement>(null);
  const marketRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (newsRef.current && !newsRef.current.contains(e.target as Node)) setNewsOpen(false);
      if (marketRef.current && !marketRef.current.contains(e.target as Node)) setMarketOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const links = [
    { href: "/calendar", label: "交易日历", icon: Calendar },
    { href: "/news/tweets", label: "新闻", icon: Newspaper, hasSub: true },
    { href: "/market/stocks", label: "行情", icon: ChartLineUp, hasSub: true },
  ];

  const isMarketActive = pathname === "/market" || pathname.startsWith("/market/");

  return (
    <header className="h-14 bg-white border-b border-border flex items-center px-4 shrink-0">
      <Link href="/" className="text-lg font-semibold tracking-tight text-ink-primary mr-8">
        天演 Tianyan
      </Link>
      <nav className="flex items-center gap-1">
        {links.map((l) => {
          const isActive = l.hasSub
            ? (l.href === "/news/tweets"
                ? pathname === "/news/tweets" || pathname.startsWith("/news/")
                : isMarketActive)
            : pathname === l.href || pathname.startsWith(l.href + "/");

          // 新闻下拉
          if (l.href === "/news/tweets") {
            return (
              <div key={l.href} ref={newsRef} className="relative">
                <button
                  onClick={() => { setNewsOpen(!newsOpen); setMarketOpen(false); }}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${
                    isActive ? "bg-emerald-50 text-accent font-medium" : "text-ink-secondary hover:bg-surface-hover hover:text-ink-primary"
                  }`}
                >
                  <l.icon size={16} weight={isActive ? "fill" : "regular"} />
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
            );
          }

          // 行情下拉
          if (l.href === "/market/stocks") {
            return (
              <div key={l.href} ref={marketRef} className="relative">
                <button
                  onClick={() => { setMarketOpen(!marketOpen); setNewsOpen(false); }}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${
                    isActive ? "bg-emerald-50 text-accent font-medium" : "text-ink-secondary hover:bg-surface-hover hover:text-ink-primary"
                  }`}
                >
                  <l.icon size={16} weight={isActive ? "fill" : "regular"} />
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
            );
          }

          // 普通链接（交易日历）
          return (
            <Link key={l.href} href={l.href}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${
                isActive ? "bg-emerald-50 text-accent font-medium" : "text-ink-secondary hover:bg-surface-hover hover:text-ink-primary"
              }`}>
              <l.icon size={16} weight={isActive ? "fill" : "regular"} />
              {l.label}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}

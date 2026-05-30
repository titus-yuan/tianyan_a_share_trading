
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface TableStat {
  rows: number;
  label: string;
  stocks?: number;
  date_from?: string;
  date_to?: string;
}

interface SourceStat {
  name: string;
  tables: Record<string, TableStat>;
}

export default function DataOverviewPage() {
  const [sources, setSources] = useState<Record<string, SourceStat>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/data/overview")
      .then((r) => r.json())
      .then((d) => { setSources(d.sources); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-zinc-400">加载中...</div>;

  const sourceKeys = Object.keys(sources);

  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold text-zinc-200 mb-4">数据覆盖矩阵</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sourceKeys.map((key) => {
          const src = sources[key];
          const tables = Object.entries(src.tables);
          return (
            <div key={key} className="border border-zinc-700 rounded-lg p-4 bg-zinc-800/50">
              <h3 className="font-semibold text-emerald-400 mb-3">{src.name}</h3>
              <div className="space-y-2">
                {tables.map(([tname, stat]) => (
                  <div key={tname} className="flex items-center justify-between text-sm">
                    <span className="text-zinc-300">{stat.label}</span>
                    <span className="text-zinc-500">
                      {stat.rows?.toLocaleString()} 行
                      {stat.stocks ? ` · ${stat.stocks} 只` : ""}
                    </span>
                  </div>
                ))}
                {tables.length === 0 && <span className="text-zinc-600 text-sm">暂无数据</span>}
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-3">
        <LinkCard href="/data/daily" icon="📊" title="日线数据" desc="OHLCV 行情" />
        <LinkCard href="/data/fund-flow" icon="💰" title="资金流向" desc="主力资金" />
        <LinkCard href="/data/finance" icon="💼" title="财务数据" desc="季报年报" />
        <LinkCard href="/data/xdxr" icon="🔄" title="除权除息" desc="分红送股" />
        <LinkCard href="/data/stocks" icon="🏷️" title="股票信息" desc="基本信息" />
      </div>
    </div>
  );
}

function LinkCard({ href, icon, title, desc }: { href: string; icon: string; title: string; desc: string }) {
  return (
    <Link href={href} className="border border-zinc-700 rounded-lg p-4 bg-zinc-800/50 hover:border-emerald-600 transition-colors">
      <div className="text-2xl mb-1">{icon}</div>
      <div className="font-medium text-zinc-200 text-sm">{title}</div>
      <div className="text-zinc-500 text-xs">{desc}</div>
    </Link>
  );
}

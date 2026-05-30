
"use client";

import { useEffect, useState } from "react";

interface Column {
  key: string;
  label: string;
  render?: (value: any) => string;
  hide?: string;
}

export default function DataTable({
  endpoint,
  columns,
  searchTrigger,
}: {
  endpoint: string;
  columns: Column[];
  searchTrigger: number;
}) {
  const [data, setData] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const pageSize = 20;

  const fetchData = async (p: number) => {
    setLoading(true);
    try {
      const sep = endpoint.includes("?") ? "&" : "?";
      const res = await fetch(`${endpoint}${sep}page=${p}&pageSize=${pageSize}`);
      const json = await res.json();
      setData(json.data || []);
      setTotal(json.total || 0);
      setPage(json.page || p);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData(1);
  }, [endpoint, searchTrigger]);

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div>
      {loading && <div className="text-zinc-400 text-sm mb-3">加载中...</div>}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-700 text-zinc-400 text-xs">
              {columns.map((c) => (
                <th key={c.key} className="text-left py-2 px-3 whitespace-nowrap">{c.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.length === 0 && !loading && (
              <tr><td colSpan={columns.length} className="py-8 text-center text-zinc-600">暂无数据</td></tr>
            )}
            {data.map((row, i) => (
              <tr key={i} className="border-b border-zinc-800 hover:bg-zinc-800/50">
                {columns.map((c) => (
                  <td key={c.key} className="py-2 px-3 whitespace-nowrap text-zinc-300">
                    {c.render ? c.render(row[c.key]) : row[c.key] != null ? String(row[c.key]) : "-"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="flex items-center gap-2 mt-4 justify-center">
          <button onClick={() => fetchData(page - 1)} disabled={page <= 1} className="px-3 py-1 bg-zinc-800 border border-zinc-700 rounded text-sm text-zinc-300 disabled:opacity-40">◀</button>
          <span className="text-sm text-zinc-500">{page} / {totalPages}</span>
          <button onClick={() => fetchData(page + 1)} disabled={page >= totalPages} className="px-3 py-1 bg-zinc-800 border border-zinc-700 rounded text-sm text-zinc-300 disabled:opacity-40">▶</button>
        </div>
      )}
    </div>
  );
}

'use client';

import { useState, useEffect, useCallback } from "react";
import type { PaginatedTweets, TweetStats } from "@/lib/types";
import TweetItem from "@/components/tweets/tweet-item";
import TweetDetail from "@/components/tweets/tweet-detail";

export default function TweetsPage() {
  const [data, setData] = useState<PaginatedTweets | null>(null);
  const [stats, setStats] = useState<TweetStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [syncing, setSyncing] = useState(false);

  const fetchTweets = useCallback(async (p: number, q: string) => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams({ page: String(p), limit: "20" });
      if (q) params.set("q", q);
      const r = await fetch(`/api/tweets?${params}`);
      if (!r.ok) throw new Error("加载失败");
      setData(await r.json());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchTweets(page, query); }, [page]);
  useEffect(() => {
    fetch("/api/tweets/stats")
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {});
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchTweets(1, query);
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      const r = await fetch("/api/tweets/sync", { method: "POST" });
      const d = await r.json();
      alert(d.message || `同步完成`);
      fetchTweets(page, query);
      fetch("/api/tweets/stats").then(r => r.json()).then(setStats);
    } catch {
      alert("同步失败");
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-semibold tracking-tight">𝕏 推文</h1>
        {stats && (
          <div className="flex items-center gap-2 text-xs">
            <span className="px-2 py-1 rounded-full bg-white border border-border text-ink-secondary">总计 {stats.total}</span>
            {stats.today > 0 && <span className="px-2 py-1 rounded-full bg-emerald-50 text-accent font-medium">+{stats.today} 今日</span>}
            <span className="px-2 py-1 rounded-full bg-white border border-border text-ink-muted">{stats.accounts} 位推主</span>
          </div>
        )}
      </div>

      <div className="flex gap-2 mb-4">
        <form onSubmit={handleSearch} className="flex-1">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="搜索推文或推主..."
            className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-white placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent"
          />
        </form>
        <button
          onClick={handleSync}
          disabled={syncing}
          className="px-4 py-2 text-sm rounded-lg bg-accent text-white hover:bg-emerald-700 transition-colors disabled:opacity-50"
        >
          {syncing ? "同步中..." : "同步"}
        </button>
      </div>

      {loading && (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-20 bg-white rounded-lg border border-border animate-pulse" />
          ))}
        </div>
      )}

      {error && (
        <div className="text-center py-12 text-ink-muted">
          <p>{error}</p>
          <button onClick={() => fetchTweets(page, query)} className="mt-2 text-accent text-sm hover:underline">重试</button>
        </div>
      )}

      {data && !loading && data.tweets.length === 0 && (
        <div className="text-center py-12 text-ink-muted">
          <p className="text-lg mb-1">暂无推文</p>
          <p className="text-sm">点击「同步」按钮采集最新推文</p>
        </div>
      )}

      {data && data.tweets.length > 0 && (
        <>
          <div className="space-y-2">
            {data.tweets.map((t) => (
              <TweetItem key={t.id} tweet={t} onClick={() => setSelectedId(t.id)} />
            ))}
          </div>
          <div className="flex items-center justify-center gap-2 mt-4">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="px-3 py-1.5 text-sm rounded-lg border border-border hover:bg-surface-hover disabled:opacity-30 transition-colors"
            >◀</button>
            <span className="text-sm text-ink-muted">{page} / {data.pages}</span>
            <button
              disabled={page >= data.pages}
              onClick={() => setPage(page + 1)}
              className="px-3 py-1.5 text-sm rounded-lg border border-border hover:bg-surface-hover disabled:opacity-30 transition-colors"
            >▶</button>
          </div>
        </>
      )}

      {selectedId && <TweetDetail tweetId={selectedId} onClose={() => setSelectedId(null)} />}
    </div>
  );
}

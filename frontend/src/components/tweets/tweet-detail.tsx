'use client';

import { useState, useEffect } from "react";
import { X, ArrowSquareOut } from "phosphor-react";
import type { Tweet } from "@/lib/types";

export default function TweetDetail({ tweetId, onClose }: { tweetId: number; onClose: () => void }) {
  const [tweet, setTweet] = useState<Tweet | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/tweets/${tweetId}`)
      .then((r) => { if (!r.ok) throw new Error("加载失败"); return r.json(); })
      .then(setTweet)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [tweetId]);

  useEffect(() => {
    function handleKey(e: KeyboardEvent) { if (e.key === "Escape") onClose(); }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex justify-end" onClick={onClose}>
      <div className="absolute inset-0 bg-black/20" />
      <div
        className="relative w-[420px] max-w-full bg-white h-full overflow-auto shadow-xl border-l border-border"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-border">
          <span className="text-sm font-medium">推文详情</span>
          <button onClick={onClose} className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-hover">
            <X size={18} />
          </button>
        </div>

        <div className="p-4">
          {loading && <div className="animate-pulse space-y-2"><div className="h-4 bg-border rounded w-3/4" /><div className="h-20 bg-border rounded" /></div>}

          {tweet && (
            <>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-emerald-100 text-accent flex items-center justify-center font-semibold">
                  {(tweet.display_name || tweet.username)[0]?.toUpperCase()}
                </div>
                <div>
                  <div className="font-medium text-sm">{tweet.display_name}</div>
                  <div className="text-xs text-ink-muted">@{tweet.username}</div>
                </div>
              </div>

              <p className="text-sm text-ink-primary whitespace-pre-wrap leading-relaxed mb-4">{tweet.content}</p>

              <div className="space-y-2 text-xs text-ink-muted border-t border-border pt-4">
                <div className="flex justify-between"><span>推文 ID</span><span className="font-mono">{tweet.tweet_id}</span></div>
                <div className="flex justify-between"><span>发布时间</span><span>{new Date(tweet.posted_at).toLocaleString("zh-CN")}</span></div>
                {tweet.raw_url && (
                  <a href={tweet.raw_url} target="_blank" className="flex items-center gap-1 text-accent hover:underline mt-2">
                    <ArrowSquareOut size={14} /> 查看原文
                  </a>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

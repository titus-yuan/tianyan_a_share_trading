import type { Tweet } from "@/lib/types";

function formatBJT(iso: string) {
  try {
    const d = new Date(iso);
    return `${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  } catch {
    return "—";
  }
}

export default function TweetItem({ tweet, onClick }: { tweet: Tweet; onClick: () => void }) {
  const initial = (tweet.display_name || tweet.username)[0]?.toUpperCase() || "?";

  return (
    <div
      onClick={onClick}
      className="bg-white border border-border rounded-lg p-3 cursor-pointer hover:border-accent/30 hover:bg-surface-hover/50 transition-all"
    >
      <div className="flex gap-3">
        <div className="w-10 h-10 rounded-full bg-emerald-100 text-accent flex items-center justify-center text-sm font-semibold shrink-0">
          {initial}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-baseline gap-1.5 text-xs mb-1">
            <span className="font-medium text-ink-primary">{tweet.display_name}</span>
            <span className="text-ink-muted">@{tweet.username}</span>
            <span className="text-ink-faint">·</span>
            <span className="text-ink-muted">{formatBJT(tweet.posted_at)}</span>
          </div>
          <p className="text-sm text-ink-secondary line-clamp-2 whitespace-pre-wrap">{tweet.content}</p>
        </div>
        <span className="text-[10px] text-ink-faint font-mono shrink-0">{tweet.tweet_id}</span>
      </div>
    </div>
  );
}

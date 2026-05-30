'use client';

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Calendar, Newspaper, ChartLineUp } from "phosphor-react";

const items = [
  { href: "/calendar", label: "交易日历", icon: Calendar },
  { href: "/news/tweets", label: "新闻", icon: Newspaper },
  { href: "/market", label: "行情", icon: ChartLineUp },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-14 bg-white border-r border-border flex flex-col items-center py-3 gap-1 shrink-0">
      {items.map((item) => {
        const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
        return (
          <Link
            key={item.href}
            href={item.href}
            title={item.label}
            className={`w-10 h-10 flex items-center justify-center rounded-lg transition-colors ${
              isActive ? "bg-emerald-50 text-accent" : "text-ink-muted hover:bg-surface-hover hover:text-ink-secondary"
            }`}
          >
            <item.icon size={20} weight={isActive ? "fill" : "regular"} />
          </Link>
        );
      })}
    </aside>
  );
}

import type { CalendarMonth } from "@/lib/types";

const WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"];

export default function MonthView({ data }: { data: CalendarMonth }) {
  const today = new Date().toISOString().slice(0, 10);
  const firstDay = new Date(data.year, data.month - 1, 1);
  const startDayOfWeek = firstDay.getDay(); // 0=Sun -> we want Mon=0
  const offset = startDayOfWeek === 0 ? 6 : startDayOfWeek - 1;

  const cells: (typeof data.days[0] | null)[] = [];
  for (let i = 0; i < offset; i++) cells.push(null);
  for (const d of data.days) cells.push(d);
  while (cells.length < 42) cells.push(null);

  return (
    <div>
      <div className="grid grid-cols-7 gap-1 mb-1">
        {WEEKDAYS.map((wd) => (
          <div key={wd} className="text-center text-xs font-medium text-ink-muted py-1">{wd}</div>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1">
        {cells.map((cell, i) => {
          if (!cell) return <div key={`e${i}`} className="aspect-square rounded-lg" />;
          const dayNum = new Date(cell.date).getDate();
          const isToday = cell.date === today;
          return (
            <div
              key={cell.date}
              className={`aspect-square rounded-lg flex items-center justify-center text-sm transition-colors ${
                cell.is_open
                  ? `bg-accent text-white font-medium ${isToday ? "ring-2 ring-accent ring-offset-1" : ""}`
                  : `text-ink-muted bg-border/30 ${isToday ? "ring-2 ring-ink-muted ring-offset-1" : ""}`
              }`}
            >
              {dayNum}
            </div>
          );
        })}
      </div>
    </div>
  );
}

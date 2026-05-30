import type { CalendarMonth } from "@/lib/types";

const WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"];

function dayClass(day: { is_open: boolean; holiday_name?: string | null }, isToday: boolean) {
  if (day.is_open) {
    // 交易日
    return `bg-emerald-500 text-white font-medium ${isToday ? "ring-2 ring-emerald-600 ring-offset-1" : ""}`;
  }
  if (day.holiday_name) {
    // 法定假日
    return `bg-red-50 text-red-600 border border-red-200 font-medium ${isToday ? "ring-2 ring-red-400 ring-offset-1" : ""}`;
  }
  // 周末
  return `text-ink-muted bg-gray-100 ${isToday ? "ring-2 ring-ink-muted ring-offset-1" : ""}`;
}

export default function MonthView({ data }: { data: CalendarMonth }) {
  const today = new Date().toISOString().slice(0, 10);
  const firstDay = new Date(data.year, data.month - 1, 1);
  const startDayOfWeek = firstDay.getDay();
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
              className={`aspect-square rounded-lg flex flex-col items-center justify-center text-sm transition-colors ${dayClass(cell, isToday)}`}
            >
              <span>{dayNum}</span>
              {!cell.is_open && cell.holiday_name && (
                <span className="text-[9px] leading-none mt-0.5 opacity-80">{cell.holiday_name}</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// 数据源注册表 — 新增来源只需加一行
export interface SourceTable {
  table: string;
  label: string;
  shared?: boolean; // 跨来源共享（如日线可多源）
}

export interface DataSource {
  key: string;
  name: string;
  tables: SourceTable[];
}

export const DATA_SOURCES: DataSource[] = [
  {
    key: "baostock",
    name: "Baostock",
    tables: [
      { table: "daily_klines", label: "日线(前复权)", shared: true },
    ],
  },
  {
    key: "easytdx",
    name: "easy-tdx",
    tables: [
      { table: "easytdx_daily", label: "日线", shared: true },
      { table: "easytdx_daily_stat", label: "资金流向" },
      { table: "easytdx_finance", label: "财务" },
      { table: "easytdx_xdxr", label: "除权除息" },
      { table: "easytdx_stocks", label: "股票信息" },
    ],
  },
];

// 哪些数据类型是跨来源共享的
export const SHARED_TYPES = ["daily"];

export function getSourcesForType(type: string): DataSource[] {
  if (!SHARED_TYPES.includes(type)) return [];
  return DATA_SOURCES.filter((s) =>
    s.tables.some((t) => t.shared && t.table.includes(type) || t.table === `easytdx_${type}` || t.table === type)
  );
}

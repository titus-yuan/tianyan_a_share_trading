"use client";

import { ChartLineUp } from "phosphor-react";

export default function MarketPage() {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <ChartLineUp size={48} className="mx-auto mb-4 text-ink-muted" weight="duotone" />
        <h1 className="text-xl font-semibold mb-2">行情</h1>
        <p className="text-ink-muted mb-4">行情模块正在建设中，敬请期待</p>
        <div className="text-xs text-ink-muted space-y-1">
          <p>后续将包含：</p>
          <p>· 主要指数实时行情</p>
          <p>· 个股K线图</p>
          <p>· 板块涨跌榜</p>
          <p>· 资金流向</p>
        </div>
      </div>
    </div>
  );
}

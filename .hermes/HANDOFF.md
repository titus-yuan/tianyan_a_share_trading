# HANDOFF — 天演前端 Next.js 重构

> 从 PRD (SPEC.md v1.0) 拆解 | 目标 Agent: frontender (MiniMax-M2.7)
> 项目路径: `/home/titus/projects/tianyan-frontend/`

## 任务清单

### Task 1: 项目初始化
- `npx create-next-app@latest tianyan-frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm`
- 安装额外依赖: `npm install pg phosphor-react`
- 初始化 shadcn/ui (new-york style): `npx shadcn@latest init`

### Task 2: 全局布局 (layout.tsx)
- 顶部导航: logo "天演" + 三个菜单项 (交易日历/新闻下拉/行情)
- 左侧图标边栏 (56px)，Phosphor icons
- 底部状态栏: 版本号 + 同步时间
- 字体: Geist + PingFang SC (next/font)

### Task 3: 交易日历页 (`/calendar`)
- 月视图日历组件 (7列×6行网格)
- 月份切换 (◀ ▶ 按钮, URL query `?month=`)
- 🔴 交易日 (is_open=true) / ○ 非交易日
- 今日高亮蓝色边框
- API: `GET /api/calendar?year=&month=` 从 `trade_calendar` 表查询

### Task 4: X推文页 (`/news/tweets`)
- 搜索框 (debounce 300ms)
- 推文列表: 头像圆(首字母) + 显示名·@用户名·时间 + 内容 line-clamp-2
- 点击展开详情面板 (完整内容/链接/tweet_id)
- 分页 (每页20条)
- 统计胶囊 (总计/今日新增/推主数)
- 同步按钮 POST /api/tweets/sync
- API: `GET /api/tweets`, `GET /api/tweets/:id`, `POST /api/tweets/sync`, `GET /api/tweets/stats`

### Task 5: 行情占位页 (`/market`)
- "建设中"占位, 列出后续功能

### Task 6: API Routes
- `/api/calendar/route.ts` — 查询 trade_calendar
- `/api/tweets/route.ts` — 查询 nitter_tweets 分页/搜索
- `/api/tweets/[id]/route.ts` — 单条推文详情
- `/api/tweets/sync/route.ts` — 触发 monitor.py 采集
- `/api/tweets/stats/route.ts` — 统计信息
- `/api/market/status/route.ts` — 占位状态

### 数据库
- 库: `Stocks_China_A` (Bot PC PostgreSQL)
- 连接: `pg` 直连 localhost:5432
- 表: `nitter_tweets`, `trade_calendar`

### 设计约束（来自 frontend-dev skill）
- ❌ 不用 Inter 字体 → 用 Geist + PingFang SC
- ❌ 不用 AI blue (#2563EB) → 用 emerald-600 (#059669)
- ❌ 不用 emoji → 用 Phosphor icons
- ✅ 必须实现 loading/empty/error 三态
- ✅ 背景 #FAFAFA, 卡片 white + border

### 参考资料
- PRD: `九章/Project/tianyan/SPEC.md` (Obsidian)
- 设计令牌: 见 SPEC.md §3.4
- 表结构: 见 SPEC.md §6 附录

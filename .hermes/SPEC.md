# 天演前端重构 PRD (SPEC v1.0)

> 版本: 1.0 | 日期: 2026-05-30 | 作者: 九章 (Architect)
> 状态: 待审查 | Phase: 1/5 (产品架构)

---

## 1. 项目概述

### 1.1 背景

天演（Tianyan）当前前端为 Flask + HTMX + Tailwind v3 CDN 单页面应用，部署于 Bot PC 端口 5500。
因功能扩展（新增交易日历、行情模块），需要迁移至 Next.js 框架以获得更好的组件化和路由管理能力。

### 1.2 目标

将前端重构为 **Next.js (App Router)** 应用，支持三个一级菜单的独立页面，与现有 Flask 后端并存，
逐步替换为 Next.js API Routes 直连 PostgreSQL。

### 1.3 非目标（本期不做）

- 行情页面的具体图表（仅占位）
- 用户登录/权限系统
- 实时 WebSocket 推送
- 新闻 RSS 源（非 X 渠道）

---

## 2. 页面结构

### 2.1 全局布局

```
┌──────────────────────────────────────────────────────────┐
│ 天演 Tianyan                    [交易日历] [新闻▾] [行情] │ ← 顶部导航
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ← 左侧边栏 (56px icons)         主内容区                │
│                                                          │
│  📅 交易日历                   ┌──────────────────────┐ │
│  📰 新闻                       │                      │ │
│  📈 行情                       │   当前页面内容        │ │
│  ──────────                    │                      │ │
│  ⚙️  设置                      │                      │ │
│                                └──────────────────────┘ │
│                                                          │
├──────────────────────────────────────────────────────────┤
│  © 天演 v0.2.0  ·  上次同步: 2026-05-30 14:30           │ ← 底部状态栏
└──────────────────────────────────────────────────────────┘
```

### 2.2 导航结构

```
📅 交易日历         → /calendar          菜单第一位，默认页
📰 新闻             → /news              菜单第二位
    └─ 𝕏 推文       → /news/tweets       二级菜单（下拉或侧边栏子项）
📈 行情             → /market            菜单第三位（本期占位）
```

### 2.3 各页面详述

#### 2.3.1 交易日历 (`/calendar`)

**功能描述**：月视图日历，显示 A 股交易日/非交易日。

**页面布局**：
```
┌──────────────────────────────────────────────────────────┐
│  交易日历                                    2026年 5月  │
├──────────────────────────────────────────────────────────┤
│  ◀ 4月                       5月 2026               6月 ▶│
├──────────────────────────────────────────────────────────┤
│  一    二    三    四    五    六    日                   │
│                  1     2     3     4                     │
│  5     6🔴  7🔴  8🔴  9     10    11                     │
│  12🔴 13🔴 14🔴 15🔴 16    17    18                     │
│  19🔴 20🔴 21🔴 22🔴 23    24    25                     │
│  26🔴 27🔴 28🔴 29🔴 30    31                           │
├──────────────────────────────────────────────────────────┤
│  图例: 🔴 交易日 (22天)  ○ 非交易日 (9天)                │
│  本月交易日: 22天   |   最新数据: 2026-05-29              │
└──────────────────────────────────────────────────────────┘
```

**交互行为**：
- 月份切换：◀ ▶ 按钮切换月份，URL `?month=2026-05`
- 点击某一天：高亮选中，右侧滑出当日统计面板（涨跌家数、成交额等，本期做占位）
- 今日标记：当天加蓝色边框高亮
- 加载状态：骨架屏（7×6 格子占位）

**数据来源**：`trade_calendar` 表
| 字段 | 用途 |
|------|------|
| `trade_date` | 日期 |
| `is_open` | true=交易日(🔴), false=非交易日 |
| `week_day` | 星期几（0=日, 1-6） |

**API 路由**：`GET /api/calendar?year=2026&month=5`
```json
{
  "year": 2026, "month": 5,
  "days": [
    {"date": "2026-05-01", "is_open": false, "week_day": 5},
    ...
  ],
  "stats": {"trading_days": 22, "non_trading_days": 9}
}
```

---

#### 2.3.2 新闻 → X推文 (`/news/tweets`)

**功能描述**：继承并增强现有推文列表，支持搜索、分页、详情展开。

**页面布局**：
```
┌──────────────────────────────────────────────────────────┐
│  X 推文                             总计 1,234  +12 今日  │
├──────────────────────────────────────────────────────────┤
│  🔍 搜索推文或推主...                  [同步] [导出]      │
├──────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────┐ │
│ │ S  STOCK调研公社  · @STOCK6688  ·  05-29 14:30       │ │
│ │    今日行情分析：上证指数突破3300点...               │ │
│ │    ─────────────────────────────────────             │ │
│ │ Q  清风剑     · @QingFengJianZX  ·  05-29 14:15      │ │
│ │    个股推荐：关注新能源板块...                       │ │
│ │    ─────────────────────────────────────             │ │
│ │ M  美股勇士   · @Meiguyxs88  ·  05-29 13:50          │ │
│ │    美股盘前：纳指期货上涨...                         │ │
│ │    ─────────────────────────────────────             │ │
│ └──────────────────────────────────────────────────────┘ │
│                                          ◀ 1  2  3 ▶    │
└──────────────────────────────────────────────────────────┘
```

**推文列表项设计**：
- 左侧：推主头像圆（首字母，如 S/Q/M），40×40px
- 第一行：`显示名` · `@用户名` · 时间（MM-DD HH:MM 北京时间）
- 第二行：推文内容，`line-clamp-2`，最多 2 行
- 点击：展开详情面板（向右侧滑出）：
  - 完整推文内容
  - 推文链接（raw_url）
  - 推文 ID（tweet_id）
  - 采集时间

**交互行为**：
- 搜索：输入框 `debounce 300ms` → `GET /api/tweets?q=xxx`
- 分页：底部页码，每页 20 条
- 同步按钮 → `POST /api/tweets/sync` → 触发 Backend 采集 → 返回新增数量
- 导出按钮 → `GET /api/tweets/export?format=csv`（本期不做）

**数据来源**：`nitter_tweets` 表
| 字段 | 用途 |
|------|------|
| `tweet_id` | 推文唯一 ID |
| `username` | @用户名 |
| `display_name` | 显示名 |
| `content` | 推文内容（支持换行） |
| `posted_at` | 发布时间（timestamptz） |
| `raw_url` | 推文原始链接 |
| `fetched_at` | 采集时间 |

**API 路由**：
| 路由 | 方法 | 参数 | 返回 |
|------|------|------|------|
| `/api/tweets` | GET | `?page=1&limit=20&q=&username=` | 分页推文列表 + 总数 |
| `/api/tweets/:id` | GET | 推文 id | 单条推文详情 |
| `/api/tweets/sync` | POST | — | `{new: 12, total: 1234}` |
| `/api/tweets/stats` | GET | — | `{total, today, accounts}` |

---

#### 2.3.3 行情 (`/market`)

**功能描述**：本期占位页。

**页面布局**：
```
┌──────────────────────────────────────────────────────────┐
│  行情                                                   │
├──────────────────────────────────────────────────────────┤
│                                                          │
│          📈  行情模块正在建设中，敬请期待                 │
│                                                          │
│          后续将包含：                                     │
│          · 主要指数实时行情                               │
│          · 个股K线图                                     │
│          · 板块涨跌榜                                     │
│          · 资金流向                                      │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**API 路由**：
| 路由 | 方法 | 返回 |
|------|------|------|
| `/api/market/status` | GET | `{status: "coming_soon"}` |

---

## 3. 技术方案

### 3.1 技术栈

| 层 | 选型 | 版本 |
|----|------|------|
| 框架 | Next.js (App Router) | 15.x |
| 语言 | TypeScript | 5.x |
| 样式 | Tailwind CSS | v4 |
| 组件库 | shadcn/ui (new-york style) | latest |
| 图标 | Phosphor Icons | latest |
| 动画 | CSS transitions + framer-motion（按需） | 11.x |
| 数据获取 | Server Components + Route Handlers | — |
| 字体 | Geist (Vercel) + PingFang SC | — |
| 数据库 | pg (node-postgres) 直连 PostgreSQL | 8.x |

### 3.2 项目结构

```
tianyan-frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── app/
│   │   ├── layout.tsx            ← 全局布局 (导航+侧边栏+底部)
│   │   ├── page.tsx              ← 默认重定向 → /calendar
│   │   ├── calendar/
│   │   │   └── page.tsx          ← 交易日历页
│   │   ├── news/
│   │   │   ├── page.tsx          ← 新闻首页（可选，默认重定向到 tweets）
│   │   │   └── tweets/
│   │   │       └── page.tsx      ← X 推文列表页
│   │   └── market/
│   │       └── page.tsx          ← 行情占位页
│   ├── components/
│   │   ├── ui/                   ← shadcn/ui 基础组件
│   │   ├── layout/
│   │   │   ├── top-nav.tsx       ← 顶部导航栏
│   │   │   ├── sidebar.tsx       ← 左侧图标边栏
│   │   │   └── footer-bar.tsx    ← 底部状态栏
│   │   ├── calendar/
│   │   │   ├── month-view.tsx    ← 月视图主组件
│   │   │   ├── calendar-cell.tsx ← 单格
│   │   │   └── day-detail.tsx    ← 日详情面板
│   │   ├── tweets/
│   │   │   ├── tweet-list.tsx    ← 推文列表
│   │   │   ├── tweet-item.tsx    ← 推文单条
│   │   │   ├── tweet-detail.tsx  ← 推文详情面板
│   │   │   ├── tweet-search.tsx  ← 搜索框
│   │   │   └── tweet-stats.tsx   ← 统计胶囊
│   │   └── market/
│   │       └── coming-soon.tsx   ← 占位页
│   ├── lib/
│   │   ├── db.ts                ← PostgreSQL 连接池
│   │   ├── utils.ts             ← 工具函数（BJT 时间转换等）
│   │   └── types.ts             ← TypeScript 类型定义
│   └── app/api/
│       ├── calendar/
│       │   └── route.ts          ← GET /api/calendar
│       └── tweets/
│           ├── route.ts          ← GET /api/tweets
│           ├── [id]/
│           │   └── route.ts      ← GET /api/tweets/:id
│           ├── sync/
│           │   └── route.ts      ← POST /api/tweets/sync
│           └── stats/
│               └── route.ts      ← GET /api/tweets/stats
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.ts
├── components.json              ← shadcn/ui 配置文件
└── .env.local                   ← DB_HOST, DB_PORT, DB_NAME, DB_USER
```

### 3.3 组件树

```
<RootLayout>
  <TopNav>                          ← 顶部: logo + 一级菜单
    <NavItem href="/calendar">交易日历</NavItem>
    <NavDropdown label="新闻">       ← 下拉: 新闻 > X推文
      <NavSubItem href="/news/tweets">X推文</NavSubItem>
    </NavDropdown>
    <NavItem href="/market">行情</NavItem>
  </TopNav>
  <div className="flex">
    <Sidebar>                        ← 左侧图标导航（与顶部菜单同步高亮）
      <SideIcon href="/calendar" icon={Calendar} />
      <SideIcon href="/news/tweets" icon={Newspaper} />
      <SideIcon href="/market" icon={ChartLineUp} />
    </Sidebar>
    <main>{children}</main>          ← 页面内容
  </div>
  <FooterBar>                        ← 底部: 版本 + 同步状态
    <SyncStatus />
  </FooterBar>
</RootLayout>
```

### 3.4 设计令牌

遵循 frontend-dev skill 设计规范，适配数据仪表盘场景：

| Token | 值 | 用途 |
|-------|-----|------|
| 背景 | `#FAFAFA` | 全局背景 |
| 卡片 | `#FFFFFF` + `border border-slate-200` | 内容卡片 |
| 主文字 | `#171717` | 标题/正文 |
| 辅文字 | `#525252` | 辅助信息 |
| 弱文字 | `#A3A3A3` | 时间/标签 |
| 强调色 | `#059669` (emerald-600) | 交易日标记/选中态/链接 |
| 非交易日 | `#E5E5E5` | 日历灰格 |
| 导航背景 | `#FFFFFF` | 顶部+侧边导航 |
| 导航宽度 | `56px`（侧边）/ `h-14`（顶部） | — |
| 字体 | Geist + PingFang SC | 全局 |
| 等宽 | JetBrains Mono | tweet_id 显示 |
| 圆角 | `rounded-lg` (8px) 卡片/按钮 | 统一 |

> ⚠️ 不用 `#2563EB` (AI blue)，不用 Inter 字体，遵循 frontend-dev skill 强制规则。

---

## 4. 数据流

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Next.js     │────▶│  Route Handlers  │────▶│  PostgreSQL  │
│  Server      │     │  (pg 直连)        │     │  Bot PC      │
│  Components  │◀────│                   │◀────│  :5432       │
└──────────────┘     └──────────────────┘     └──────────────┘
```

- Server Components 直接调 `lib/db.ts` 查询数据库（RSC 模式）
- Client Components（搜索、分页）通过 fetch 调 Route Handlers
- 推文同步按钮 → `POST /api/tweets/sync` → Route Handler 内 exec monitor.py → 返回新增数

---

## 5. 迁移策略

### 5.1 与 Flask 并存

```
Bot PC :5500  →  Flask (旧前端，保持运行)     ← 推文监控 + 旧版 Dashboard
Bot PC :3000  →  Next.js (新前端)              ← 本期重构目标
```

- Flask 保留运行直到新前端稳定
- 数据采集 cron 不变（不受前端迁移影响）
- Next.js 直连 PostgreSQL 读数据，不依赖 Flask API

### 5.2 部署

```bash
# Bot PC 上
cd /mnt/data/code/tianyan-frontend
npm run build
npm start      # → :3000
```

### 5.3 里程碑

| 阶段 | 内容 | 产出 |
|------|------|------|
| Phase 1 ✅ | PRD 产出 | 本文档 |
| Phase 2 | Next.js 项目初始化 + 布局骨架 | 可导航的 3 页空壳 |
| Phase 3 | 交易日历页 | 月视图 + API |
| Phase 4 | X 推文页 | 列表 + 搜索 + 详情 |
| Phase 5 | QA + 部署 | TEST_REPORT + Bot PC 运行 |

---

## 6. 附录

### A. 数据库连接配置 (.env.local)

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=Stocks_China_A
DB_USER=titus
DB_PASSWORD=
```

### B. nitter_tweets 关键查询

```sql
-- 推文列表分页
SELECT id, tweet_id, username, display_name, content, posted_at, raw_url
FROM nitter_tweets
ORDER BY posted_at DESC
LIMIT 20 OFFSET 0;

-- 搜索结果
SELECT ... FROM nitter_tweets
WHERE content ILIKE '%keyword%' OR username ILIKE '%keyword%'
ORDER BY posted_at DESC LIMIT 20;

-- 统计
SELECT COUNT(*) as total,
       COUNT(*) FILTER (WHERE fetched_at::date = CURRENT_DATE) as today,
       COUNT(DISTINCT username) as accounts
FROM nitter_tweets;
```

### C. trade_calendar 关键查询

```sql
SELECT trade_date, is_open, week_day
FROM trade_calendar
WHERE trade_date BETWEEN '2026-05-01' AND '2026-05-31'
ORDER BY trade_date;
```

---

> **下一步**：用户审查本 PRD → 确认后 Phase 2 由 frontender Agent 实现。

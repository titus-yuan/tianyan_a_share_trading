# 天演 Tianyan

> **天道演化，水势推演。**  
> 以天道之规律，驱动财富之水不断繁衍、推演。

---

## 命名寓意

| 维度 | 解读 |
|------|------|
| **天道** | 天即天道，代表客观规律——市场的波动看似随机，实则符合某种内在秩序 |
| **演** | 演化、推演、计算。源自「天道运行，万物演化」，契合量化分析对历史数据的回测与未来的预测 |
| **水** | 「演」带三点水，本义水流展延、长流不息。以天道规律，引水聚财 |
| **气场** | 科技感与玄学融合——破译天道、引水聚财的量化工具 |

---

## 项目简介

天演是一个 **A 股量化交易辅助系统**，当前阶段聚焦于：

- 📡 **社交媒体情报采集** — 监控 A 股大 V 推文，提取股票提及与买卖推荐
- 📊 **数据持久化** — PostgreSQL 存储 + SQLite 本地缓存双轨
- 🌐 **Web 可视化** — Flask + HTMX 暗色主题仪表盘

后续规划：股票代码识别、NLP 买卖信号检测、推荐绩效追踪、实盘信号对接。

---

## 架构

```
┌──────────────────────────────────────────────┐
│                  天演 Tianyan                 │
│                                              │
│  ┌──────────┐    ┌──────────┐   ┌─────────┐ │
│  │ 推文采集   │───→│ PostgreSQL│←──│ Web 展示 │ │
│  │ Nitter RSS│    │ Bot PC   │   │ :5500   │ │
│  └──────────┘    └────┬─────┘   └─────────┘ │
│                       │                      │
│                  ┌────▼─────┐                │
│                  │  SQLite   │                │
│                  │  本地缓存  │                │
│                  └──────────┘                │
│                                              │
│  ┌──────────────────────────────────────┐    │
│  │  未来：股票识别 → 信号检测 → 绩效追踪  │    │
│  └──────────────────────────────────────┘    │
└──────────────────────────────────────────────┘
```

### 双机部署

| 机器 | IP | 角色 |
|------|------|------|
| **九章**（Hermes 本机） | 192.168.169.28 | 定时采集 + Web 服务 |
| **Bot PC** | 192.168.169.30 | PostgreSQL 数据存储 |

---

## 目录结构

```
tweet-monitor/                  # 当前开发目录
├── src/tweet_monitor/
│   ├── monitor.py              # 定时采集主逻辑
│   ├── sync_cache.py           # PG → SQLite 同步
│   ├── db.py                   # SSH 隧道 + PostgreSQL 操作
│   ├── pool.py                 # Nitter 实例池（测活/轮询）
│   ├── config.py               # 环境配置
│   ├── sources/
│   │   ├── base.py             # 数据源抽象接口
│   │   └── nitter.py           # Nitter RSS 采集实现
│   └── web/
│       ├── __init__.py         # Flask 应用
│       └── templates/
│           ├── index.html      # 主页面（暗色主题）
│           └── _tweet_list.html # HTMX 分页/搜索
├── scripts/
│   ├── run_monitor.sh          # 采集执行脚本
│   └── run_web.sh              # Web 启动脚本
└── pyproject.toml              # uv 项目配置
```

---

## 快速开始

### 环境要求

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) 包管理器
- Bot PC 上 PostgreSQL（192.168.169.30）
- SSH 免密登录 Bot PC

### 安装

```bash
git clone git@github.com:titus-yuan/tianyan_a_share_trading.git
cd tianyan_a_share_trading
uv sync
```

### 配置

复制并编辑环境变量：

```bash
cp .env.example .env
```

必填项：

```env
BOT_PC_HOST=192.168.169.30
BOT_PC_USER=titus
BOT_PC_DB=media_x_monitor
NITTER_INSTANCES=https://nitter.net
```

### 运行

**首次采集**：

```bash
uv run python -m tweet_monitor
```

**启动 Web 仪表盘**：

```bash
uv run python -c "from src.tweet_monitor.web import launch; launch()"
# → http://localhost:5500
```

### 定时任务

```bash
# 交易时段每 30 分钟，非交易时段每小时
*/30 9-15 * * 1-5 cd /path/to/project && uv run python -m tweet_monitor >> logs/cron.log 2>&1
0 * 0-8,16-23 * * 1-5 cd /path/to/project && uv run python -m tweet_monitor >> logs/cron.log 2>&1
```

---

## 数据库

### PostgreSQL（Bot PC）

| 表 | 说明 |
|------|------|
| `tweets` | 推文（id / 内容 / 时间 / 来源） |
| `fetch_log` | 采集日志 |
| `nitter_instances` | Nitter 实例健康状态 |
| `monitored_accounts` | 监控账号列表 |

### SQLite（本地缓存）

```bash
tree cache/
# cache/tweets.db    ← 与 PG 自动同步，Web 页面秒开
```

---

## 技术栈

| 层 | 技术 |
|------|------|
| 语言 | Python 3.12 |
| 包管理 | uv |
| 数据源 | Nitter RSS（可替换） |
| 持久化 | PostgreSQL + SQLite |
| Web | Flask + HTMX + Tailwind CSS |
| 调度 | cron |
| 远程 | SSH + psycopg2 |

---

## 路线图

- [x] @STOCK6688 推文增量监控
- [x] Web 仪表盘 + 搜索
- [ ] 多账号支持
- [ ] A 股代码自动提取（正则 + 校验）
- [ ] NLP 买卖信号识别（MiniMax API）
- [ ] 推荐绩效追踪（回查 PG 历史行情）
- [ ] Telegram 实时推送

---

## 协议

MIT License

---

<p align="center">
  <i>天之道，损有余而补不足。<br>人之道，损不足以奉有余。<br>—— 《道德经》</i>
</p>

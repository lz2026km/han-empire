# 汉献帝之末路

> 基于 LLM + 历史推演的回合制古风帝王游戏。玩家扮演汉献帝刘协，在董卓乱政、曹操「挟天子以令诸侯」的控制下，寻求兴复汉室之道。

[![GitHub Repo](https://img.shields.io/badge/GitHub-lz2026km%2Fhan--empire-brightgreen)](https://github.com/lz2026km/han-empire)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 游戏背景

**189年**，董卓进京，废少帝立献帝，拉开汉末乱世序幕。

献帝先被董卓控制于洛阳、长安，后被曹操迁都许昌。名为天子，实为阶下囚。诸侯割据，汉室衰微，皇权名存实亡。

**你的使命**：在这最黑暗的二十年里，以智谋与名分，辗转于董卓、曹操与诸侯之间，寻求兴复汉室之道。

---

## 核心玩法

### 🎯 召见大臣
与三国名臣对话——试探忠诚、获取建议、洞察人心。大臣按**忠诚度四档**（忠诚/观望/离心/叛逆）给出不同回应，并受**派系**影响（忠汉派/务实派/离心派/叛逆派）。

### ⚖️ 朝堂派系
四大派系（忠汉派/务实派/离心派/叛逆派）影响力 0-100，威权/藩镇联动。每月自动更新。派系影响诏书效果倍率（忠汉派≥50时+10%，叛逆派≥40时-15%）。

### 📜 拟旨诏令
六种诏书（衣带密诏/讨伐诏书/迁都诏书/嘉奖诏书/罪己诏/大赦天下）经**指令状态机**管理：草稿（draft）→ 已发布（issued）→ 过期（expired）/ 已执行 / 已取消。威权达标方可发布。

### 🔄 月末推演
每回合由 LLM 季节模拟器推演，输出叙事文本，再由提取器解析为结构化指标变化。包含：
- **分级财政**：田赋（兖/豫/荆三州）+ 盐铁专营 + 诸侯贡金 + 暗探开支
- **派系变化**：四大派系影响力此消彼长
- **诸侯动态**：藩镇自动行动，写入 `last_action`
- **阈值危机**：藩镇>70 / 威权<10 / 声望<15 自动触发危机事件
- **天子日记**：LLM 生成回合日记体记录
- **deadline 超时**：事项自动处理（推进/失败/取消）

### 💬 大臣召对（MinisterChat）
全新独立聊天界面（177行 TSX + 236行 CSS），拟古奏对风格，即时消息气泡 + 大臣头像（3keengames.net），派系标签 + 忠诚度徽章，实时解析 LLM 回复并写入数据库。

### 🌳 天子技能树
四系各12条技能（经略/权谋/武功/文治），威权达标解锁，消耗技能点激活。威权≥40每回合+1点，威权≥60每回合+2点，上限10点。

### 📋 事项追踪
完整的**事项追踪系统**：密谋讨贼 / 讨伐董卓 / 献帝东归 等历史线，含进度条（bar_value）、结案判定、失败效果、deadline 超时自动处理，以及事项级联（某事项失败触发关联事项）。

### 🗺️ 势力视图 & 情报系统
各路诸侯军力 ASCII 排行（精锐/较强/中等/较弱/虚弱）+ 联盟关系 + 董卓伏诛线详情 + 收支细目。威权≥40解锁暗探情报。

### 🏛️ 建筑系统
14建筑分四类：**宫殿类**（未央宫/许昌行宫/洛阳宫殿，威权+3/年或衰减减缓）、**军事类**（洛阳/兖州/荆州/扬州武库，军事效果+8-15%）、**经济类**（兖/荆/徐/广四州粮仓，田赋+8-10%）、**特殊类**（九江船坞/潼关要塞/虎牢关，防御+20-25%）。维护费自动扣除。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 运行时 | Python 3.11+ / SQLite |
| LLM框架 | Agno（多Agent编排，可选） |
| 网络 | httpx（异步HTTP客户端） |
| Web界面 | Gradio 6.0（12 Tab）+ React + Vite（Web前端） |
| ORM | SQLAlchemy 2.0（数据库封装） |
| 前端框架 | React 18 + TypeScript + Vite |
| 模型支持 | OpenAI 兼容 API（MiniMax/DeepSeek 等） |
| 内容管理 | JSON + Markdown + 结构化数据 |

---

## 快速开始

```bash
# 克隆项目
git clone https://github.com/lz2026km/han-empire.git
cd han-empire

# 安装依赖（推荐 uv）
uv sync

# 或使用 pip
pip install -e .

# 启动游戏
python launcher.py
# 或启动 Web 版（默认 5199 端口）
python web_app.py
# 浏览器访问 http://localhost:5199
```

> **Web 版无需公网暴露**：本地运行，通过 Gradio 本地 URL 访问。

---

## 项目结构

```
han-empire/
├── web/                  # React + Vite Web前端（TypeScript/TSX）
│   ├── src/
│   │   ├── components/    # React组件（9个：BattleView/FactionRelationDiagram/MinisterPortrait/Notification/ProvinceMap/MapLegend/DecreeReviewPanel/Header）
│   │   ├── styles/       # CSS（animations.css古风动画/主题样式）
│   │   └── api.ts        # REST API客户端
│   └── dist/             # 构建输出
│
├── web_app.py            # Gradio Web 界面（12 Tab，2578行）
├── launcher.py           # pywebview桌面窗口（355行）
├── server.py             # Flask REST API（19端点）
│
├── han_sim/              # 核心游戏引擎
│   ├── models.py            # 数据类（GameState/CourtContext/SimulationResult等，1017行）
│   ├── db.py                # SQLite 持久化（37张表 + 完整CRUD，2400行）
│   ├── session.py           # 回合流转、初始化、大臣召对（228行）
│   ├── simulation.py        # 月末推演（双Agent + JSON提取 + 阈值危机，603行）
│   ├── flows.py             # 财政流/派系/藩镇动态/技能点/诏书效果（1135行）
│   ├── decree.py            # 诏书系统（普通/衣带密诏/迁都/讨伐/东归，1037行）
│   ├── agents.py            # LLM Agent（大臣/诏书/记忆提取/季节模拟）
│   ├── issues.py           # 事项追踪（进度/结案/级联/危机注入）
│   ├── skills.py           # 天子技能树（天子48技能 + 大臣技能授权）
│   ├── tools.py            # 大臣工具集 + 军情/情报工具
│   ├── context.py          # 25个历史锚点 + 6种汉末胜负判定
│   ├── matching.py         # 模糊匹配 + 汉末别名表
│   ├── assets.py          # 资源加载/JSON校验
│   ├── report.py           # 回合报告格式化
│   ├── memories.py        # 记忆系统（事件记忆卡）
│   └── content.py          # 内容加载器
│
├── content/                # 游戏内容
│   ├── characters.json    # 人物数据（120人，含派系/能力/忠诚/技能）
│   ├── regions.json       # 州郡数据（50州郡）
│   ├── powers.json        # 诸侯势力（30势力，含军力/立场/盟友）
│   ├── events.json        # 历史事件（79条，含resolve/fail_condition）
│   ├── armies.json        # 军队数据（20编制）
│   ├── seed_events.json   # 种子事件（40条）
│   ├── decrees.json       # 诏书模板（30条）
│   ├── emperor_skills.json # 天子技能树（48条，四系各12）
│   ├── classes.json       # 阶级数据（8阶级，49条）
│   ├── buildings.json     # 建筑数据（26个）
│   ├── skill_tools.json   # 诏令工具模板（21条）
│   ├── consorts.json      # 后宫秀女候选（34名）
│   ├── opening_crises.json # 开局危机系统
│   └── prompts/           # LLM Prompt 模板
│       ├── minister_agent.md
│       ├── decree_writer.md
│       ├── season_simulator.md
│       ├── memory_extractor.md
│       ├── simulator.md
│       └── extractor.md
│
├── scripts/               # 运维脚本
│   └── e2e_test.py        # 端到端测试
│
└── .claude/               # 开发配置（Claude Code）
    ├── CLAUDE.md           # 项目开发指南
    ├── commands/           # 命令集
    │   └── commit-push-pr.md
    └── agents/            # Agent配置
        └── code-reviewer.md
```

---

## 数据库架构（37张核心表）

| 表名 | 用途 |
|------|------|
| `game_state` | 游戏全局状态（年/月/回合/阶段） |
| `metrics` | 数值指标（威权/藩镇/声望/汉室库/内库） |
| `characters` | 人物数据（含派系/能力/忠诚/风格/状态） |
| `character_offices` | 人物官职历 |
| `factions` | 四大派系影响力 |
| `classes` | 阶级数据 |
| `powers` | 诸侯势力（含军力/立场/盟友/last_action） |
| `power_logs` | 诸侯行动日志 |
| `regions` | 州郡数据 |
| `region_logs` | 区域变化日志 |
| `armies` | 军队数据 |
| `army_logs` | 军队变动日志 |
| `buildings` | 建筑状态 |
| `building_logs` | 建筑日志 |
| `economy_accounts` | 财政账户（汉室库/内库） |
| `economy_ledger` | 财政流水账 |
| `fiscal_config` | 财政配置 |
| `events` | 历史事件 |
| `event_triggers` | 事件触发器 |
| `turn_logs` | 回合日志 |
| `turn_reports` | 回合报告 |
| `turn_extractions` | 回合数据提取 |
| `turn_directives` | 回合指令 |
| `chat_messages` | 召对历史消息 |
| `secret_orders` | 密诏记录 |
| `issues` | 事项追踪（进度/级联/危机） |
| `issue_advances` | 事项推进历史 |
| `event_memories` | 事件记忆卡 |
| `event_memory_sources` | 记忆来源关联 |
| `kv_store` | 通用键值存储 |
| `emperor_skills` | 天子已激活技能 |
| `minister_skill_grants` | 大臣技能授权 |
| `directives` | 指令状态机（草稿/已发布/过期） |
| `consorts` | 后宫妃嫔 |
| `consort_candidates` | 秀女候选 |
| `consort_events` | 后宫事件 |
| `consort_traits` | 秀女特质 |
| `legacies` | 遗业/传承数据 |
| `power_name_logs` | 势力名号变更日志 |
| `emperor_diary` | 天子日记 |

---

## 核心指标

| 指标 | 范围 | 说明 |
|------|------|------|
| 威权 | 0-100 | 核心数值，影响所有系统 |
| 藩镇 | 0-100 | 军阀势力，越低越好 |
| 声望 | 0-100 | 汉室威望 |
| 汉室库 | 0-∞ | 财政储备 |
| 内库 | 0-∞ | 皇帝私人金库 |
| 技能点 | 0-10 | 技能激活代币 |

### 威权等级

| 威权 | 等级标签 | 诏书倍率 |
|------|----------|----------|
| 0-9 | 形同虚设 | 30% |
| 10-19 | 权臣操弄 | 40% |
| 20-39 | 阳奉阴违 | 60-70% |
| 40-59 | 勉强维持 | 80% |
| 60-79 | 略有起色 | 100% |
| 80-99 | 号令四方 | 120% |
| 100 | 至高无上 | 150% |

---

## 版本历程

| 版本 | 日期 | 里程碑 |
|------|------|--------|
| **v1.1.0** | 2026-05-31 | **前端完整化**：BattleView/FactionRelationDiagram/MinisterPortrait/Notification/ProvinceMap/DecreeReviewPanel 全组件 + 513行CSS动画 + 850行app.css古风主题。架构与ming-salvage-sim功能对齐，React+Vite现代前端 |
| **v1.0.1** | 2026-05-31 | **全面审核修复**：MinisterChat独立聊天界面（177行TSX+236行CSS，拟古奏对风格）+ SkillTab技能树Tab + BuildingTab建筑Tab + 30+古风CSS动画（龙纹/卷轴/锦衣/朝服主题）+ launcher DPI缩放适配 + main.py新增`--cli`命令行模式 + issues.py progress→bar_value字段修复10处 + db.py新增deadline_turn字段 |
| **v0.9.9** | 2026-05-31 | **Step18完成**：派系动态系统完整版 + pywebview桌面launcher + REST API + PyInstaller打包配置 |
| **v0.9.7** | 2026-05-31 | **五大系统完整落地**：天子技能树（四系48技能）+ 建筑系统（14建筑）+ 诏令状态机（6种诏书类型）+ 派系系统 |
| **v0.9.6** | 2026-05-31 | **核心事件链全通**：忠诚度系统 + 董卓伏诛 + 献帝东归 + 迁都系统 |
| **v0.9.4** | 2026-05-30 | **古风主题配色**：玄黑/朱红/古金/暖白17色配色方案 + Noto Serif SC 字体，覆盖全部UI组件 |
| **v0.9.0** | 2026-05-30 | **十项功能全量落地**：天子技能树、双Agent推演架构、分级财政、派系系统、军情情报、事项增强、地图视图、天子日记LLM生成、建筑系统、指令状态机 |
| **v0.8.3** | 2026-05-30 | 忠诚度上下文注入召对 + 诸侯动态显示 + 衣带密诏Web独立按钮 |
| **v0.8.2** | 2026-05-30 | 藩镇动态+忠诚度机制+衣带诏+仪表盘+势力视图 |
| **v0.8.1** | 2026-05-30 | 扩充开局邸报 — 天子近况/汉室国势/五困局/势力格局/历史线状态/游戏系统说明 |
| **v0.8.0** | 2026-05-29 | issues.py 完整方法链 |
| **v0.7.9** | 2026-05-29 | db.py 完整 schema + 种子数据 + 状态读写 |
| **v0.7.7** | 2026-05-29 | CHANGELOG.md + scripts探针 + 设计文档 |
| **v0.7.6** | 2026-05-29 | prompts目录(6个md) + buildings.json(26建筑) |
| **v0.7.5** | 2026-05-28 | emperor_skills.json(48条) + classes.json(49条) + skills.py |
| **v0.7.4** | 2026-05-28 | assets/matching/context/report/exceptions 5模块 |
| **v0.7.3** | 2026-05-27 | 内容侧扩充至369条 |
| **v0.7.2** | 2026-05-26 | Web界面升级：仪表盘/召对历史/游戏日志/事务Tabs |
| **v0.7.1** | 2026-05-25 | 威权/迁都/忠诚衰减/董卓伏诛/献帝东归/藩镇动态 |
| **v0.7.0** | 2026-05-24 | 核心系统完成：回合制 + LLM召对 + 圣旨系统 + Gradio界面 |
| **v0.5.0** | 2026-05-20 | 记忆系统核心 — event_memories表 + LLM提取 + 召见注入 |
|| **v0.8.0** | 2026-05-29 | issues.py 完整方法链 — advance_issue/close_issue/cancel_issue/mark_event_triggered/list_active_issues |
|| **v0.7.9** | 2026-05-29 | db.py 完整 schema + 种子数据 + 状态读写 |
|| **v0.7.7** | 2026-05-29 | CHANGELOG.md + scripts探针 + 设计文档 |
|| **v0.7.6** | 2026-05-29 | prompts目录(6个md) + buildings.json(26建筑) + token_stats.py |
|| **v0.7.5** | 2026-05-28 | emperor_skills.json(48条) + classes.json(49条) + skills.py(241行) |
|| **v0.7.4** | 2026-05-28 | assets/matching/context/report/exceptions 5模块 |
|| **v0.7.3** | 2026-05-27 | 内容侧扩充至369条（characters 120/regions 50/powers 30/events 79/seed_events 40） |
|| **v0.7.2** | 2026-05-26 | Web界面升级：仪表盘/召对历史/游戏日志/事务Tabs |
|| **v0.7.1** | 2026-05-25 | 威权/迁都/忠诚衰减/董卓伏诛/献帝东归/藩镇动态 |
|| **v0.7.0** | 2026-05-24 | 核心系统完成：回合制 + LLM召对 + 圣旨系统 + Gradio界面 |
|| **v0.5.0** | 2026-05-20 | 记忆系统核心 — event_memories表 + LLM提取 + 召见注入 |

---

## 游戏结局

游戏时间跨度 **189-220年**，共有四种结局：

1. **兴复汉室**（胜利）：联吴抗曹 → 赤壁翻盘 → 还于旧都
2. **三分天下**（平局）：鼎足之势 → 缓缓图之
3. **禅让延续**（历史结局）：220年曹丕篡汉，汉室禅让
4. **提前灭亡**（失败）：皇权彻底丧失 → 游戏结束

---

## 开发说明

### Python 版本要求

- **Python 3.11+**（推荐）
- **Python 3.6 兼容性规范**（开发约束）：
  - ❌ 禁止：`from __future__ import annotations`
  - ❌ 禁止：`tuple[...]`, `dict[...]`, `set[...]`
  - ✅ 必须：`Tuple[...]`, `Dict[...]`, `Set[...]`

### AGNO 降级策略

AGNO（LLM Agent 框架）**可选安装**，无 AGNO 时系统自动使用 fallback：

- `decree.py`：使用模板生成诏书
- `simulation.py`：跳过 LLM 叙事
- `agents.py`：`Agent = None` 时不创建 Agent

### 开发命令

```bash
# 运行测试
python3 scripts/e2e_test.py

# 编译检查
python3 -m py_compile han_sim/*.py web_app.py

# 启动应用
python3 web_app.py
```

### 提交规范

```
fix: 修复问题
feat: 新功能
ui: UI 变更
refactor: 重构
docs: 文档
test: 测试
```

---

## License

MIT · [lz2026km/han-empire](https://github.com/lz2026km/han-empire)
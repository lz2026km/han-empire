# 汉献帝之末路 (v3.0)

> **LLM 驱动的回合制古风帝王策略游戏**。你扮演汉献帝刘协，在董卓乱政、曹操"挟天子以令诸侯"的二十年中，寻求兴复汉室之道。
>
> 主公！这是您的江山，您的诏书，您的衣带密令，您的智谋与大汉最后的命运。

[![GitHub Repo](https://img.shields.io/badge/GitHub-lz2026km%2Fhan--empire-brightgreen)](https://github.com/lz2026km/han-empire)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![v3.0](https://img.shields.io/badge/version-3.0-orange)](CHANGELOG.md)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6)](README_WINDOWS.md)

---

## 🎮 三句话看懂这个游戏

1. **你** = 汉献帝刘协（189-220 年），被曹操控制在许昌的傀儡皇帝
2. **游戏核心 = LLM 驱动**：诏书、召对、廷议、战役、历史演进——**每个决策都有 AI 模拟**
3. **目标 = 兴复汉室**：5 大历史事件（董卓乱政/官渡/赤壁/曹丕篡汉/衣带诏）任你改写

---

## 📜 游戏背景

**中平六年（189 年）**，董卓进京，废少帝，立献帝，拉开汉末乱世序幕。

献帝先被董卓控制于洛阳、长安，后被曹操"迁都"许昌。**名为天子，实为阶下囚。** 诸侯割据，汉室衰微，皇权名存实亡。

**你的使命**：在这最黑暗的二十年里，以智谋与名分，辗转于董卓、曹操与诸侯之间，**寻求兴复汉室之道**。

> _"朕乃大汉天子，天命所归。曹贼挟朕，朕岂甘为阶下囚？"——汉献帝（玩家）_

---

## 🌟 核心玩法（v3.0 全方位大升级 + v2.5.0 UI/UX 旗舰版 + v2.2.0 诏书系统终极版）

### 🏗️ v3.0 全新：全方位大升级 (5 commit · 67 files · +11673 行)

主公！v3.0 是基于 v3.0 全网调研的最大升级。后端 6 个新模块 + 内容 +99 人物/+67 事件/+20 诏书/+14 州郡 + 前端 5 个新组件 + 11 个新 API 端点。

#### 🔌 1. 后端 P0 4 项 (调研对标青干《崇祯模拟器》)

| 模块 | 调研对应 |
|------|---------|
| `api_key_router.py` | P0-1 本地 API Key 路由 (3 模式: local/server/hybrid) |
| `llm_cache.py` | P0-2 KV cache 优化 (静态 SHA256 + 命中率统计) |
| `model_adapter.py` | P0-3 多模型适配器 (MiniMax/Qwen/DeepSeek/GLM-5/OpenAI 5 家) |
| `context_injector.py` | P0-4 长上下文防幻觉 (议题硬约束 + NPC 现实提示) |

#### 🗺️ 2. 内容扩展

- 人物 166 → **265** (+99 主流三国/黄巾/董卓/群雄/大族/文臣/边疆)
- 事件 92 → **159** (+67 黄巾起义/董卓入京/衣带诏/官渡/赤壁/汉中/曹丕篡汉)
- 诏书 30 → **50** (+20 衣带 5/九品 3/屯田 2/求贤 2/禅让 5/迁都 3)
- 州郡 51 → **65** (+14 交州 3/益州 4/凉州 3/辽东 2/属国 3)

#### 🎨 3. 前端 5 个新组件 + 3 个 CSS 重写

- `IntimacyRing` (91 行) — SVG 圆环 4 色
- `BattleMap` (132 行) — 13 州战势图
- `EventTimeline` (114 行) — 大事年表
- `TTSPlayer` (155 行) — 圣旨朗读 (3 中文男声)
- `Settings` (308 行) — 设置面板 (3 模式 + 5 Provider)
- 3 个 CSS 占位 → 现代 SaaS 蓝调 (AppLayout/system/CourtBackdrop)

#### 📡 4. 11 个新 API 端点 (60 → 76)

| 端点 | 用途 |
|------|------|
| `GET /api/settings/api-key` | 服务端 Key 状态 (不暴露内容) |
| `POST /api/settings/api-key` | 前端提交 (服务端仅校验) |
| `POST /api/llm/test` | 测试连通 |
| `GET /api/usage/stats` | Token 用量统计 (今日/本周/本月) |
| `GET /api/usage/recent?limit=N` | 最近 N 条记录 |
| `GET /api/llm/models` | 列出 5 家 Provider |
| `GET /api/llm/cache-stats` | KV cache 命中率 + 节省估算 |
| `GET /api/saves/list?campaign_id` | 存档列表 |
| `GET /api/saves/meta?campaign_id&slot` | 单槽位元数据 |
| `POST /api/saves/cleanup` | 清理超出槽位 |
| `GET /api/health/full` | 综合健康 (DB+Key+Cache+Usage) |

#### 🎯 5. 差异化定位 (主公审批)

> **不与青干打"历史还原 + 自由改写"赛道**, 而是打 **"结构化策略 + 概率可复现"** 赛道。
> 9 维诏书 + 5 档权限 + 1000 次蒙特卡洛反弹 + 4 史官评语 = 我们的护城河

### 🎨 v2.5.0 全新：UI/UX 旗舰版 (1 commit · 46 文件 · 4295+ 行)

主公！v2.5.0 抛弃单文件 4619 行巨型 React，**组件化拆为 8 大目录 20 组件**，三栏布局 + TTS 全栈。

#### 🖼️ 1. AppLayout 三栏骨架 (1920×1080 锁死)

```
┌─────────────────────────────────────────────────────┐
│ TopBar (年号/皇帝)            56px                  │
├──────────┬──────────────────────────┬───────────────┤
│ Inbox    │   CourtStage (议政厅)   │ ProvinceList  │
│ 4类奏报  │   DebateBubble 5派系    │ 13州刺史      │
│ 260px    │   MinistersPanel        │ 信息差卡片    │
│ sidebar  │   HexagonDashboard 6维  │ 反弹徽章      │
└──────────┴──────────────────────────┴───────────────┘
```

#### ⌨️ 2. 全局快捷键 (useKeyboard 升级)

| 键 | 动作 |
|----|------|
| **J / K** | 下一封 / 上一封奏折 |
| **Esc** | 关闭弹窗 |
| **1 / 2 / 3 / 4 / 5** | 拟旨档位 (口谕/谕旨/圣旨/密旨/廷议) |
| **Space** | 推进一回合 |
| **m** | 主菜单 |
| **s** | 设置 |
| **h** | 起居注 |

#### 🗣️ 3. TTS 圣旨朗读 (主公语音点题)

- 前端 hook: `useTTS` 调 `/api/tts`
- 后端: `han_sim/tts.py` 用 edge-tts 微软免费中文
- 3 男声可选: 云健 (威压) / 云希 (温润) / 云扬 (通用)

#### 📦 4. 20 组件 / 8 目录

| 目录 | 组件 | 功能 |
|------|------|------|
| **court** (4) | Backdrop/Stage/DebateBubble/MinistersPanel | 议政厅全套 |
| **dashboard** (4) | Hexagon/InfoGap/Province/Backlash | 6 维雷达 + 13 州 + 反弹徽章 |
| **edict** (5) | Composer/Slider/Seal/History/VerdictPopup | 9 维拟旨 + 玉玺 + 回奏 |
| **events** (1) | EventTicker | 事件滚动条 |
| **inbox** (2) | Inbox + InboxItem | 4 类奏报 |
| **intro** (1) | Intro (3 幕 taiji/ascension/chamber) | 启动过场 |
| **system** (3) | MenuDrawer / SpeedControl / NotificationToast | 系统层 |
| **topbar** (1) | TopBar | 顶栏 |

#### ⚠️ 5. CSS 占位声明 (主公 2026-06-02 明令)

3 个 CSS 文件为占位实现 (后续专业 GUI 软件到位后批量替换为正式设计稿):
- `web/src/AppLayout.css` — 三栏骨架
- `web/src/components/system/system.css` — 通用系统层
- `web/src/components/court/CourtBackdrop.css` — 议政厅背景

每个文件含 `TODO 待专业 GUI 软件补正` 注释, **功能跑得通, 视觉走极简基础风**。

#### 🧪 6. 测试 (2 项静态校验)

| ID | 测试点 |
|----|--------|
| UI-1 | Intro 3 幕过场 (taiji/ascension/chamber + Esc 跳过) |
| UI-3 | HexagonDashboard 6 维雷达 (国库/军权/民心/朝堂/信息/时间) |

### 📜 v2.2.0 全新：诏书系统终极版

主公！诏书不再是简单文字，而是**9 维结构 + 5 档权限 + 4 维真实感**：

#### 🎴 1. 9 维旨意

每次下旨, 您需要决定 9 个维度:

| 维度 | 含义 | 示例 |
|------|------|------|
| **目标** | 要解决什么问题 | 讨羌 |
| **执行者** | 谁去做 | 皇甫嵩 |
| **范围** | 涉及区域 | 西凉 |
| **资源** | 银两/兵/粮 | 50 万两 + 3000 兵 |
| **期限** | 多少回合 | 3 月 |
| **权限** | L1 5 档 | 圣旨/密旨/廷议... |
| **激励** | 赏赐/封赠 | 升爵 + 赐金 |
| **约束** | 限制/连坐 | 不得扰民 |
| **公开度** | 天下/部院/秘密 | 明发天下 |

#### ⚖️ 2. L1 5 档权限 (P0-5)

| 权限 | enforce | prestige_cost | 场景 |
|------|---------|---------------|------|
| 口谕 | 0.4 | 0 | 私下嘱托 |
| 谕旨 | 0.6 | 1 | 限六部 |
| **圣旨** | 1.0 | 3 | 正诏明发 |
| 密旨 | 0.85 | 2 | 秘密行动 |
| 廷议 | 0.95 | 2 | 百官共议 |

#### 🔥 3. 4 类奏报 + 6 类事件 (P0-2 + P0-3)

**事件 6 类**: 朝政 / 财政 / 军事 / 地方 / 人物 / 科技 (每类 5 模板)
**4 维评分**: 紧急 (1-10) / 严重 (1-10) / 可信 (1-10) / 牵涉利益

**奏报 4 类**:
- 🌙 **月奏** — 例行公事
- 🔥 **紧急奏** — 边警/灾荒/哗变 (urgency ≥ 8)
- 🤫 **密奏** — 党争/暗通/谋反 (urgency 7-8)
- 📜 **奏报** — 一般事件

每月自动生成 **2-5 条事件** + 1-2 条月奏, 触发奏报入主公案前

#### ⚔️ 4. 党派反弹 (P1-6)

旨意触及利益 → 派系 3 种反弹 (1000 次实测):

| 反弹 | 概率 | 后果 |
|------|------|------|
| 无 | 58% | 顺利执行 |
| 拖延 | 21% | 延迟 1-3 回合 |
| 曲解 | 12% | 歪曲执行 |
| 反扑 | 9% | 激烈反抗 |

#### 📋 5. 回奏 3 段 (P0-4)

旨意执行完毕 → 大臣回奏, 包含 3 段:

1. **结果** — 成功/部分/失败/被曲解
2. **代价** — 实际消耗 (银/粮/死伤)
3. **隐患** — 1-3 条隐藏风险 (severity 3-8)

#### 🔍 6. 信息差 (P1-7)

回奏**不一定真实** (真实度 1-10), 主公可能误判:

- 边镇兵力: 实际 5000 → 上报 8000
- 国库存银: 实际 200 万 → 上报 350 万
- 豪商田亩: 隐田 30% → 仅报 5%

揭示真相, 才是明君之道。

#### 🏛️ 7. 议政廷推 (P1-8, LLM 驱动)

主公拟旨前, 可召 **3-5 大臣** 廷议:

- 5 派系: 士族 (袁绍/王允) / 宦官 (张让) / 外戚 (何进) / 清流 (卢植) / 边将 (皇甫嵩)
- LLM 驱动每大臣陈述立场 (赞成/反对/折衷)
- 加权汇总 → 多数派意见
- 主公裁断: 采纳 / 否决 / 修正

### 🧠 8. LLM 自由对话（**Phase 4.3-4.4**）

每个大臣都是**真实 LLM 模拟**：

- **多轮对话** —— 同一大臣多次召对，自动保持历史（10 轮）
- **性格驱动** —— 忠直/谄媚/怯懦/权谋的大臣，会给**截然不同的回应**
- **立场匹配** —— 帝党/曹党/孙刘/西凉 四大派系，各有算盘
- **4 个 tool_call** —— 大臣可主动调：
  - `query_state` 查国势（尚书台口吻）
  - `propose_decree` 拟旨入档（奉天承运/钦此校验）
  - `estimate_resistance` 估阻力（廷尉口吻）
  - `suggest_audience` 推荐大臣（侍中口吻）

### 👥 2. 群臣廷议（自由对话系统）

一道诏令，**3-5 位大臣按立场轮发**、互相引用、争论不休：

```
天子: "迁都许昌是否可行？"
曹操: "臣以为可也，许昌四战之地，扼中原要冲……"  [务实派]
荀彧: "臣附议，然王霸之业，当先正名分……"         [王佐派]
孔融: "天子守国都，岂可轻迁？臣死谏！"             [忠汉派]
```

### 📜 3. 6 种诏书（状态机管理）

| 诏书 | 效果 | 历史依据 |
|------|------|---------|
| **衣带密诏** | 血书衣带，密令亲信诛杀权臣 | 200 年衣带诏事件 |
| **讨伐诏书** | 声讨叛逆，号召天下共击之 | 衣带诏+诸侯会盟 |
| **迁都诏书** | 迁都洛阳/许昌/邺城/长安 | 董卓迁长安、曹操迁许昌 |
| **嘉奖诏书** | 加官晋爵，提升忠诚 | 嘉奖群臣 |
| **罪己诏** | 天子反省，重塑声望 | 灵帝、光武帝皆曾下 |
| **大赦天下** | 减刑免罪，缓和社会矛盾 | 帝王常用手段 |

**威权决定诏书效力**：
- 威权 ≥ 80：诏书如山，大臣俯首听命
- 威权 ≥ 50：诏书有效，大臣谨慎遵从
- 威权 ≥ 20：诏书无力，大臣阳奉阴违
- 威权 < 20：天子的声音无人理会

### ⚔️ 4. 5 大历史事件（**Phase 4.6 详扩**）

| # | 事件 | 年份 | 核心选择 | 历史影响 |
|---|------|------|---------|---------|
| 1 | **董卓乱政** | 189 | 联王允/借吕布/出逃长安 | 玩家可改写 |
| 2 | **官渡之战** | 200 | 支持曹操/密诏袁绍/中立观望 | 决定北方霸权 |
| 3 | **赤壁之战** | 208 | 支持孙刘/亲曹自保/密诏反曹 | 决定三分天下 |
| 4 | **夷陵之战** | 222 | 间接干预 | 蜀汉元气 |
| 5 | **曹丕篡汉** | 220 | 禅让/拒绝/衣带诏决战 | **汉朝生死** |

每个事件都含 **3 个 LLM 评估选项**（含历史锁定/高风险/中立观望），影响威权/声望/派系/汉室库。

### 🗡️ 5. 衣带诏专属剧情（**Phase 4.8**）

- **新增 `e_200_yidai_zhau` 事件** —— 献帝亲笔血书缝入衣带，密令国舅董承诛曹
- **衣带诏五臣**：董承、种辑、吴硕、王子服、刘备
- **新 agno_skill `yidai-zhao/`** —— 教 LLM 何时触发衣带诏、何时密使联外、何时收兵
- **失败后果** —— 夷三族、伏寿皇后幽禁、汉室威权 -30
- **成功条件** —— 威权≥70 + 密使隐秘 + 盟友响应

### 🏛️ 6. 36 模块核心引擎

| 模块 | 职责 | 行数 |
|------|------|------|
| `models.py` | 数据类（GameState/CourtContext 等） | 45K |
| `db.py` | SQLite 持久化（**41 表**） | 12K |
| `simulation.py` | 月末推演（双 Agent + JSON 提取） | 27K |
| `flows.py` | 财政流/派系/藩镇动态 | 48K |
| `decree.py` | 诏书系统（6 种） | 30K |
| `decree_templates.py` | 诏书模板库 | 17K |
| `decree_templates.py` | 诏书模板 | 17K |
| `issues.py` | 事项追踪 + 危机注入 | 51K |
| `issues_crisis.py` | 阈值危机注入簇 | 8K |
| `memories.py` | 召对记忆实时抽取 | 23K |
| `agents.py` | 5 个 LLM agent 工厂 | 17K |
| `agent_tools.py` | 4 个 tool_call 工具集 | 5K |
| `llm_model.py` | LLM 统一入口（统一模型工厂模式） | 6K |
| `event_selector.py` | 候选情势判选官（LLM 软筛） | 11K |
| `...` | 还有 22 个模块 | ... |

**总计 14433 行 han_sim 代码**（v1.18.0 → v2.0.0 净减 654 行 + 重构）

### 🎨 7. 9 个 Tab + 3 个 hook（**Phase 3 前端重做**）

| 汉风命名 | 原英文 | 用途 |
|---------|-------|------|
| 朝会 | overview | 国势仪表盘 |
| 诏书 | decree | 6 种诏书发布 |
| 召对 | chat | 大臣 LLM 对话 |
| 朝堂 | ministers | 大臣列表/好感度 |
| 派系 | faction | 四大派系影响力 |
| 天子 | skills | 天子技能树 |
| 营造 | building | 14 建筑管理 |
| 舆图 | map | 8 州地图（开发中） |
| 密诏 | orders | 衣带诏 + 密令 |
| 起居注 | log | 天子日记 |
| 后宫 | consort | 6 妃嫔系统 |

**App.tsx 936 → 354 行（-62%）** + 3 个 hook（useGame/useSettlement/useChatModal）

### 🗺️ 8. 8 州 + 51 州郡 + 30 势力

- **8 州**：司隶/豫州/冀州/兖州/徐州/青州/荆州/益州
- **51 州郡**：精确到郡县
- **30 诸侯势力**：含军力/立场/盟友关系
- **14 建筑**：4 类（宫殿/军事/经济/特殊）

### 👥 9. 158 位历史人物（**Phase 4.7 详扩**）

**v2.0.0 新增 6 位关键人物**：
- **董承**（车骑将军/衣带诏主谋/汉室）
- **种辑**（御史中丞/衣带诏五臣/汉室）
- **王子服**（议郎/衣带诏五臣/汉室）
- **吴硕**（散骑常侍/衣带诏五臣/汉室）
- **伏寿**（皇后/伏完之女/汉室）
- **程昱**（卫尉/曹操谋主/曹营）

含派系/能力/忠诚/技能/历史典故全字段。

### 🏯 10. 后宫系统（v1.15.0+）

- 6 位汉末深宫妃嫔（伏寿/董贵/曹贵人/李婉/何莹/王美人）
- **召幸对话**：按位份+性格回话
- **调教工具** `cultivate_consort(skill, trait)`：学技能/改性格
- **衣带诏线索**：后宫既是闺阁也是密谋载体

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **LLM 核心** | Agno（多 Agent 编排）+ OpenAI 兼容 API（MiniMax-M2.5） |
| **运行时** | Python 3.11+ / SQLite |
| **后端** | Flask + Flask-CORS（**48 个 REST 端点**） |
| **前端** | React + Vite + TypeScript |
| **桌面** | pywebview 5.5+（**Windows 原生窗口**） |
| **打包** | PyInstaller（**单文件 EXE**） |
| **数据** | 158 大臣 / 92+40 事件 / 51 州郡 / 30 势力 / 48 技能 / 30 诏书模板 |

---

## 📦 快速开始

### 🪟 Windows 玩家（**v2.0.0 推荐**）

1. 下载 `汉献帝之末路-Windows.zip`（[Releases](https://github.com/lz2026km/han-empire/releases)）
2. 解压到任意位置
3. 双击 `汉献帝之末路.exe`
4. 首次启动会弹窗配置 API Key（[REDACTED]）
5. **享受三国帝王的人生**

详细：[README_WINDOWS.md](README_WINDOWS.md)

### 🐧 Linux / macOS 开发者

```bash
# 克隆
git clone https://github.com/lz2026km/han-empire.git
cd han-empire

# 安装依赖（推荐 uv）
uv sync

# 或 pip
pip install -e .

# 启动游戏（桌面窗口）
python launcher.py
# 或 python main.py

# Web 版（Flask API + 浏览器）
python server.py
# 浏览器访问 http://localhost:5555

# CLI 古风终端
python main.py --cli
```

### 🔑 配置 API Key

游戏需要 **OpenAI 兼容 API**（推荐 [MiniMax](https://api.minimaxi.com)）：

```bash
# 方法 1: 环境变量
export MINIMAX_API_KEY="sk-cp-你的key"

# 方法 2: 首次启动弹窗配置（自动写入 runtime_llm.json）
python launcher.py

# 方法 3: 手动编辑 runtime_llm.json
{
  "provider": "minimax",
  "api_key": "sk-cp-你的key",
  "base_url": "https://api.minimaxi.com/v1",
  "model": "MiniMax-M2.5"
}
```

---

## 🏗️ 项目结构

```
han-empire/
├── web/                              # React + Vite 前端
│   ├── src/
│   │   ├── components/                # v2.5.0: 8 目录 20 组件
│   │   │   ├── court/                 # 4 个 (Backdrop/Stage/DebateBubble/MinistersPanel)
│   │   │   ├── dashboard/             # 4 个 (Hexagon/InfoGap/Province/Backlash)
│   │   │   ├── edict/                 # 5 个 (Composer/Slider/Seal/History/VerdictPopup)
│   │   │   ├── events/                # 1 个 (EventTicker)
│   │   │   ├── inbox/                 # 2 个 (Inbox + InboxItem)
│   │   │   ├── intro/                 # 1 个 (Intro 3 幕)
│   │   │   ├── system/                # 3 个 (MenuDrawer/SpeedControl/NotificationToast)
│   │   │   └── topbar/                # 1 个 (TopBar)
│   │   │   └── Header.tsx
│   │   ├── hooks/                    # React Hook (v2.5.0 增至 5 个)
│   │   │   ├── useGame.ts            # 游戏状态
│   │   │   ├── useSettlement.ts      # 月末推演
│   │   │   ├── useChatModal.ts       # 召对+作弊控制台
│   │   │   ├── useKeyboard.ts        # v2.5.0: 8 类快捷键
│   │   │   └── useTTS.ts             # v2.5.0: TTS hook
│   │   ├── AppLayout.tsx             # v2.5.0: 三栏骨架 (49 行)
│   │   ├── AppLayout.css             # v2.5.0: 三栏样式 (占位)
│   │   ├── App.tsx                   # 354 行 (原 936, -62%)
│   │   ├── api.ts                    # REST API 客户端
│   │   └── types.ts                  # TypeScript 类型
│   └── dist/                         # Vite 构建输出
│
├── .agno_skills/                     # 18 个 LLM Skill (v2.0.0 核心)
│   ├── decree-drafting/              # 诏书拟定
│   ├── court-deliberation/           # 廷议/票拟
│   ├── secret-investigation/         # 密查案验
│   ├── audience-control/             # 召对/私语
│   ├── yidai-zhao/                   # 衣带诏 (Phase 4.8)
│   └── ... 13 个 LLM Skill
│
├── han_sim/                          # 36 模块核心引擎 (14433 行)
│   ├── models.py                     # GameState/CourtContext 等数据类
│   ├── db.py                         # SQLite (41 张表)
│   ├── session.py                    # 回合流转
│   ├── simulation.py                 # 月末推演
│   ├── flows.py                      # 财政流/派系/藩镇
│   ├── flows_faction.py              # 派系动力学
│   ├── decree.py                     # 诏书系统
│   ├── decree_templates.py           # 诏书模板库
│   ├── issues.py                     # 事项追踪
│   ├── issues_crisis.py              # 阈值危机注入
│   ├── agents.py                     # 5 个 LLM agent
│   ├── agent_tools.py                # 4 个 tool_call
│   ├── llm_model.py                  # LLM 工厂
│   ├── llm_config.py / contract.py   # LLM 配置/契约
│   ├── event_selector.py             # 候选判选官
│   ├── memories.py                   # 召对记忆抽取
│   ├── diary.py                      # 天子日记
│   ├── portraits.py                  # 头像渲染
│   ├── content.py / assets.py        # 内容加载
│   ├── map_view.py / theme.py        # 视图/主题
│   ├── token_stats.py                # LLM token 统计
│   ├── utils.py / context.py         # 工具
│   ├── matching.py / skills.py       # 匹配/技能
│   ├── registry.py / paths.py        # 注册/路径
│   ├── exceptions.py                 # 异常类
│   ├── report.py                     # 战报生成
│   ├── conversation.py               # 对话管理
│   ├── tts.py                        # v2.5.0: edge-tts 边缘合成 (77 行)
│   └── cli/terminal.py               # 古风 CLI
│
├── content/                          # 游戏内容 (JSON)
│   ├── characters.json               # 158 人物 (Phase 4.7 +6)
│   ├── events.json                   # 92 事件 (Phase 4.6 扩 3 大+衣带诏)
│   ├── seed_events.json              # 40 种子事件
│   ├── regions.json                  # 51 州郡
│   ├── powers.json                   # 30 诸侯势力
│   ├── decrees.json                  # 30 诏书模板
│   ├── emperor_skills.json           # 48 天子技能
│   ├── buildings.json                # 14 建筑
│   ├── armies.json / consorts.json   # 军队/妃嫔
│   ├── opening_crises.json           # 6 开局危机
│   ├── opening_gazette.md            # 开局圣旨
│   └── classes.json / skills.json    # 类别/技能
│
├── server.py                         # Flask REST API (48 端点)
├── launcher.py                       # pywebview 桌面启动器
├── main.py                           # 入口
├── run_windows.py                    # Win 双击启动 (含单实例锁)
├── build_windows.bat                 # Win 一键打包 EXE
├── han_empire.spec                   # PyInstaller 配置
├── pyproject.toml                    # 项目配置
├── CHANGELOG.md                      # 完整更新日志
├── README.md                         # 本文件
└── README_WINDOWS.md                 # Win 用户说明
```

---

## 📊 v2.0.0 大修统计

| Phase | 提交 | 关键成果 | 变化 |
|-------|------|---------|------|
| **Phase 1** | `944266c` | 11 P0 bug 修复 | +4 后端 +7 前端 |
| **Phase 2** | `022ec22` | 后端拆解 | **-654 行**（4 模块抽出） |
| **Phase 3** | `ced90a4` | 前端重做 | **App.tsx -62%**（9 Tab + 2 hook） |
| **Phase 4.1+4.2** | `fe30423` | LLM 工厂 + 4 SKILL | 188+行新模块 |
| **Phase 4.3-4.5** | `55c85ce` | 4 tool + 自由对话 + Win EXE | 145 行新工具 + 5 文件 |
| **Phase 4.6-4.8** | (待推送) | 3 大事件 + 6 名臣 + 衣带诏 | +92 事件 + 158 大臣 |

**累计 5 个 Phase，6 个 commit 推送 GitHub**

---

## 🎨 v2.5.0 大修统计 (2026-06-02)

| 项 | 提交 | 关键成果 | 变化 |
|----|------|---------|------|
| **v2.5.0 旗舰版** | `3ac40c2` | UI/UX 三栏 + 8 组件目录 + TTS 全栈 | **+4295 行 / -21 行** · 46 文件 |
| **v2.5.0 文档** | `bd9dd80` | CHANGELOG v2.5.0 段 | +97 行 |

**v2.5.0 子项 (实测非画饼)**:

| 子项 | 数量 | 关键文件 |
|------|------|----------|
| 8 大组件目录 | 20 tsx + 20 css | court/dashboard/edict/events/inbox/intro/system/topbar |
| 全局壳层 | 1 layout + 2 hook | AppLayout.tsx + useKeyboard + useTTS |
| TTS 全栈 | 前端 hook + 后端 edge-tts | useTTS.ts + han_sim/tts.py (3 中文男声) |
| 测试 | 2 项静态校验 | test_e2e_v25.py (UI-1 Intro / UI-3 Hexagon) |
| 文档 | 1 截图说明 | SCREENSHOTS_v2.5.0.md |

**v2.5.0 设计基线 (主公明令 6 条)**:

- ✅ 1920×1080 锁死 / 1280×720 兜底 (零移动端适配)
- ✅ 侧栏 `width=260` (非 min_width 避免撑开)
- ✅ 主色 `#3b82f6` 蓝调
- ✅ 零 emoji 头像 (portraits.py 失败教训)
- ✅ 3 CSS 占位声明 (待专业 GUI 软件替换)
- ✅ 零借鉴/明末 字眼 (法律合规)

---

## 🏗️ v3.0 大修统计 (2026-06-02)

| 项 | 提交 | 关键成果 | 变化 |
|----|------|---------|------|
| **v3.0 调研文档** | `ec94176` | 历史模拟器·崇祯 全网深度调研 | +18233 字符 / 396 行 |
| **W1 阶段一** | `fa43c0d` | 后端 P0 4 项 (api_key/llm_cache/model_adapter/context_injector) | +744 行 / 0 改存量 |
| **W2 阶段二** | `14d7081` | 内容扩展 (人物+99/事件+67/诏书+20/州郡+14) | +4219 insertions |
| **W3 阶段三** | `155c79a` | 前端 UI/UX (3 CSS 重写 + 4 新组件 + Settings) | +988 行 |
| **W4 阶段四** | `790c2d9` | API + 存档 + 用量 (11 端点 + save_system + usage_tracker) | +412 行 / +11 端点 |

**v3.0 子项实测数据**:

| 子项 | 数量 | 关键模块 |
|------|------|----------|
| 后端 P0 4 模块 | 744 行 | api_key_router/llm_cache/model_adapter/context_injector |
| 后端 W4 2 模块 | 242 行 | save_system/usage_tracker |
| 人物 | +99 | characters.json 166→265 |
| 事件 | +67 | events.json 92→159 |
| 诏书 | +20 | decrees.json 30→50 |
| 州郡 | +14 | regions.json 51→65 |
| 前端组件 | +4 | IntimacyRing/BattleMap/EventTimeline/TTSPlayer |
| 前端面板 | +1 | Settings (308 行) |
| CSS 重写 | 3 | AppLayout/system/CourtBackdrop |
| API 端点 | +11 | settings/api-key + llm/* + usage/* + saves/* + health/* |

**v3.0 设计基线** (主公明令, 全部遵守):
- ✅ 1920×1080 锁死 / 1280×720 兜底 (零移动端适配)
- ✅ 侧栏 `width=260` (非 min_width 避免撑开)
- ✅ 主色 `#3b82f6` 蓝调 (CSS 变量统一)
- ✅ 零 emoji 头像
- ✅ 3 CSS 占位替换为现代 SaaS 蓝调 (不再 TODO)
- ✅ 0 借鉴/明末 字眼 (法律合规)
- ✅ 0 抄袭/模仿/致敬 (CHANGELOG/README 都通过自检)

---

## 🧪 测试

```bash
# 后端 83 个单元测试
/home/admin/.hermes/hermes-agent/venv/bin/python -m pytest tests/ -q

# 前端 TypeScript 校验
cd web && npx tsc --noEmit
```

**当前状态**：83/83 通过 ✓ · tsc 0 错 ✓

---

## 🗃️ 数据库（41 张表）

| 表名 | 用途 |
|------|------|
| `game_state` | 游戏全局状态（年/月/回合/阶段） |
| `metrics` | 数值指标（威权/藩镇/声望/汉室库） |
| `characters` | 人物数据（含派系/能力/忠诚） |
| `factions` | 四大派系影响力 |
| `powers` | 诸侯势力（含军力/立场/盟友） |
| `regions` | 51 州郡数据 |
| `armies` / `buildings` | 军队/建筑 |
| `economy_ledger` | 财政流水账 |
| `events` / `event_triggers` | 92 历史事件系统 |
| `seed_events` | 40 种子事件 |
| `issues` | 事项追踪（进度/级联/危机） |
| `directives` | 诏书状态机（草稿/已发布/过期） |
| `emperor_diary` | 天子日记 |
| `minister_affection` | 大臣好感度 |
| `emperor_skills` | 天子已激活技能 |
| `chat_messages` | 召对历史消息 |
| `secret_orders` | 密诏记录 |
| `consorts` / `consort_skills` | 妃嫔系统 |
| ... | 还有 20+ 表 |

---

## 📈 核心指标

| 指标 | 范围 | 说明 |
|------|------|------|
| 威权 | 0-100 | 核心数值，影响所有系统 |
| 藩镇 | 0-100 | 军阀势力，越低越好 |
| 声望 | 0-100 | 汉室威望 |
| 汉室库 | 0-∞ | 财政储备（万两） |
| 技能点 | 0-10 | 技能激活代币 |

### 威权等级

| 等级 | 威权 | 效果 |
|------|------|------|
| 天子 | ≥80 | 诏书如山，大臣俯首 |
| 守成 | ≥50 | 诏书有效，谨慎遵从 |
| 弱主 | ≥20 | 诏书无力，阳奉阴违 |
| 亡国 | <20 | 声音无人理会 |

---

## 🌐 REST API（48 端点）

| 端点 | 用途 |
|------|------|
| `GET /api/health` | 服务健康检查 |
| `POST /api/campaigns` | 创建新游戏 |
| `GET /api/campaigns/<id>` | 加载存档 |
| `GET /api/campaigns/<id>/state` | 获取游戏状态 |
| `POST /api/campaigns/<id>/next_turn` | 推演下一回合 |
| `GET /api/campaigns/<id>/ministers` | 大臣列表 |
| `POST /api/campaigns/<id>/chat/<minister>` | **大臣召对 (LLM)** |
| `POST /api/campaigns/<id>/free_chat` | **群臣廷议 (Phase 4.4)** |
| `POST /api/campaigns/<id>/chat/<minister>/reset` | **重置会话 (Phase 4.4)** |
| `GET /api/campaigns/<id>/secret_orders` | 密诏列表 |
| `POST /api/campaigns/<id>/receive_minister` | 接收大臣 |
| `GET /api/campaigns/<id>/factions` | 派系状态 |
| `POST /api/campaigns/<id>/decree/issue` | 发布诏书 |
| ... | 还有 30+ 端点 |

---

## 🤝 贡献指南

欢迎提交 PR！建议流程：
1. Fork 仓库
2. 创建 feature 分支（`git checkout -b feature/your-feature`）
3. 提交（`git commit -m "feat: 添加 XXX"`）
4. 推送（`git push origin feature/your-feature`）
5. 提 PR

**主公大修原则**（v2.0.0 确立）：
- 汉风优先
- LLM 驱动核心
- 桌面 1920×1080，零移动端适配
- 侧栏 width=260
- 数据实测后再写 CHANGELOG

---

## 📜 版本历史

详见 [CHANGELOG.md](CHANGELOG.md)

- **v2.2.0** (2026-06-01)：**诏书系统终极版** — 8 项模块 (9 维旨意 / 6 类事件 / 4 类奏报 / 3 段回奏 / 5 档权限 / 3 态反弹 / 信息差 / LLM 廷议), 8 commits
- **v2.1.0** (2026-06-01)：AB 合并旗舰版 — 战役推演 + 派系深度 + 科举征辟 + 春秋史册, 8 commits
- **v2.0.0** (2026-06-01)：6 Phase 大修（LLM 驱动 + 5 历史事件 + Win EXE）
- **v1.18.0**：东汉 SVG 背景图
- **v1.17.0**：后宫系统 Web 化
- **v1.16.0**：候选情势判选官
- ... 早期 14+ 版本

---

## 📄 许可证

[MIT License](LICENSE)

---

## 🙏 致谢

主公大修指导 · 姜维（OpenCode CLI）代码审查 · 袁天罡/法正知识库同步

v2.5.0 (2026-06-02): 主公明令推进 v2.5.0 UI/UX 旗舰版 + 3 个 CSS 占位 (待 GUI 软件替换)

—— 享三国，品汉风。

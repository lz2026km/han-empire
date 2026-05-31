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
四大派系（忠汉派/务实派/离心派/叛逆派）影响力 0-100，威权/藩镇联动。每月自动更新。派系影响诏书效果倍率。

### 📜 拟旨诏令
六种诏书（衣带密诏/讨伐诏书/迁都诏书/嘉奖诏书/罪己诏/大赦天下）经**指令状态机**管理：草稿→已发布→过期/已执行/已取消。威权达标方可发布。

### 🔄 月末推演
每回合由 LLM 季节模拟器推演，输出叙事文本，再由提取器解析为结构化指标变化。包含：分级财政、派系变化、诸侯动态、阈值危机、天子日记。

### 🗺️ 势力视图
各路诸侯军力 ASCII 排行（精锐/较强/中等/较弱/虚弱）+ 联盟关系 + 董卓伏诛线详情。威权≥40解锁暗探情报。

### ⚔️ 战役推演
支持两军对战推演（随机骰子系统，最多10回合），返回古风风格战报，含伤亡统计与胜负判定。

### 🏛️ 建筑系统
14建筑分四类：**宫殿类**（未央宫/许昌行宫/洛阳宫殿）、**军事类**（四州武库）、**经济类**（四州粮仓）、**特殊类**（九江船坞/潼关要塞/虎牢关）。维护费自动扣除。

### 🌳 天子技能树
四系各12条技能（经略/权谋/武功/文治），威权达标解锁，消耗技能点激活。威权≥40每回合+1点，威权≥60每回合+2点，上限10点。

### 💬 大臣召对
独立聊天界面，拟古奏对风格，即时消息气泡 + 大臣头像，派系标签 + 忠诚度徽章。

### 📋 事项追踪
完整**事项追踪系统**：密谋讨贼/讨伐董卓/献帝东归等历史线，含进度条、结案判定、失败效果与 deadline 超时自动处理。

### ❤️ 大臣好感度
与大臣互动影响好感度数值（0-100），好感度决定头像边框颜色：≥70金色 / 40-69银色 / <40灰色。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 运行时 | Python 3.11+ / SQLite |
| LLM框架 | Agno（多Agent编排，可选） |
| 网络 | httpx（异步HTTP客户端） |
| Web界面 | Flask REST API + React + Vite（Web前端） |
| 桌面 | pywebview（launcher.py） |
| 模型支持 | OpenAI 兼容 API（MiniMax/DeepSeek 等） |

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

# 启动游戏（桌面窗口）
python launcher.py

# 启动 Web 版（Flask API，默认 5555 端口）
python server.py
# 浏览器访问 http://localhost:5555
```

> **Web 版无需公网暴露**：本地运行，通过浏览器访问。

---

## 项目结构

```
han-empire/
├── web/                     # React + Vite Web前端
│   ├── src/
│   │   ├── components/      # React组件
│   │   ├── styles/          # CSS（古风动画/主题样式）
│   │   ├── hooks/           # React hooks
│   │   └── api.ts           # REST API客户端
│   └── dist/                # 构建输出
│
├── web_app.py               # Gradio Web 界面
├── launcher.py              # pywebview 桌面窗口
├── server.py                # Flask REST API（36端点）
│
├── han_sim/                 # 核心游戏引擎
│   ├── models.py            # 数据类（GameState/CourtContext等）
│   ├── db.py                # SQLite 持久化（40+张表）
│   ├── session.py           # 回合流转、初始化、大臣召对
│   ├── simulation.py        # 月末推演（双Agent + JSON提取）
│   ├── flows.py             # 财政流/派系/藩镇动态
│   ├── decree.py            # 诏书系统
│   ├── diary.py             # 天子日记生成器
│   ├── portraits.py         # 头像渲染（含好感度边框）
│   ├── cli/terminal.py      # 古风CLI终端界面
│   └── content/             # 内容加载器
│
├── content/                 # 游戏内容（JSON）
│   ├── characters.json      # 人物数据（120人）
│   ├── regions.json          # 州郡数据（50州郡）
│   ├── powers.json           # 诸侯势力（30势力）
│   ├── events.json           # 历史事件（79条）
│   ├── emperor_skills.json   # 天子技能树（48条）
│   └── buildings.json        # 建筑数据（26个）
│
└── scripts/                 # 运维脚本
    └── e2e_test.py          # 端到端测试
```

---

## 数据库架构（40+张核心表）

| 表名 | 用途 |
|------|------|
| `game_state` | 游戏全局状态（年/月/回合/阶段） |
| `metrics` | 数值指标（威权/藩镇/声望/汉室库） |
| `characters` | 人物数据（含派系/能力/忠诚） |
| `factions` | 四大派系影响力 |
| `powers` | 诸侯势力（含军力/立场/盟友） |
| `regions` | 州郡数据 |
| `armies` | 军队数据 |
| `buildings` | 建筑状态 |
| `economy_ledger` | 财政流水账 |
| `events` / `event_triggers` | 历史事件系统 |
| `issues` | 事项追踪（进度/级联/危机） |
| `directives` | 指令状态机（草稿/已发布/过期） |
| `emperor_diary` | 天子日记 |
| `minister_affection` | 大臣好感度 |
| `emperor_skills` | 天子已激活技能 |
| `chat_messages` | 召对历史消息 |
| `secret_orders` | 密诏记录 |

---

## 核心指标

| 指标 | 范围 | 说明 |
|------|------|------|
| 威权 | 0-100 | 核心数值，影响所有系统 |
| 藩镇 | 0-100 | 军阀势力，越低越好 |
| 声望 | 0-100 | 汉室威望 |
| 汉室库 | 0-∞ | 财政储备 |
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
| **v1.8.5** | 2026-06-01 | React 19 + Vite 7 前端框架升级，古风CSS动画，generate_portraits.py |
| **v1.7** | 2026-06-01 | 恢复CLI终端/天子日记/好感度/战役API，删除废弃脚本，移除所有移动端适配 |
| **v1.6** | 2026-05-31 | 天子日记/好感度/战役前端/历史事件四大系统 |
| **v1.5** | 2026-05-31 | CLI终端/存读档UI/战役推演API |
| **v1.2** | 2026-05-31 | 删除重复函数apply_building_maintenance，移除所有移动端breakpoint |
| **v1.1.0** | 2026-05-31 | 前端完整化：朝会布局/派系关系图/省份地图/头像组件 |
| **v1.0.1** | 2026-05-31 | MinisterChat/SkillTab/BuildingTab/古风动画/launcher DPI适配 |
| **v1.0.0** | 2026-05-30 | 核心系统完成：回合制+LLM召对+圣旨系统+Gradio界面 |

---

## 游戏结局

游戏时间跨度 **189-220年**，四种结局：

1. **兴复汉室**（胜利）：联吴抗曹 → 赤壁翻盘 → 还于旧都
2. **三分天下**（平局）：鼎足之势 → 缓缓图之
3. **禅让延续**（历史结局）：220年曹丕篡汉，汉室禅让
4. **提前灭亡**（失败）：皇权彻底丧失 → 游戏结束

---

## 开发说明

### Python 版本要求

- **Python 3.11+**（推荐）

### AGNO 降级策略

AGNO（LLM Agent 框架）**可选安装**，无 AGNO 时系统自动使用 fallback：

- `decree.py`：使用模板生成诏书
- `simulation.py`：跳过 LLM 叙事
- `agents.py`：`Agent = None` 时不创建 Agent

### 开发命令

```bash
# 语法检查
python3 -m py_compile han_sim/*.py web_app.py server.py

# 端到端测试
python3 scripts/e2e_test.py

# 启动 Flask API
python3 server.py
```

---

## License

MIT · [lz2026km/han-empire](https://github.com/lz2026km/han-empire)

# 🏯 更新日志 Changelog

> 汉献帝之末路 — 版本历程

---

## ⚔️ v1.0.1 — 2026-05-31

> **MinisterChat · 天子技能 · 建筑系统 · Launcher 优化**

### ✨ 新增功能

| 分类 | 功能 | 描述 |
|------|------|------|
| 🗣️ **MinisterChat** | `web/src/components/MinisterChat.tsx` (177行) | 大臣实时对话界面，支持多轮聊天 + 历史记录 |
| 📋 **技能Tab** | `web/src/components/SkillTab.tsx` | 天子技能树可视化，点选执行 |
| 🏗️ **建筑Tab** | `web/src/components/BuildingTab.tsx` | 建筑建造/升级/维护管理 |
| 🖥️ **Launcher** | `launcher.py` | DPI缩放自适应 + 系统托盘 + 窗口记忆 |
| 📜 **main.py** | 新增 `--cli` 命令行模式 | 无窗口纯终端推演 |

### 🐛 Bug Fixes

- `db.py` — deadline_turn 字段新增（建筑/事件截止回合追踪）
- `issues.py` — 10处修复，progress→bar_value 字段名统一
- `models.py` — Building dataclass 完善（region_id/category/level）

### 📦 Dependencies

- `pyproject.toml` 依赖更新（Flask-CORS / Watchdog / pyinstaller）
- `HanEmpireSim.spec` Windows 打包配置

---

## 🔧 v1.0.0 — 2026-05-31

> **P0 崩溃性Bug修复 · 线程安全 · 数据层加固**

### 🐛 Fixed

| 文件 | 问题 | 修复 |
|------|------|------|
| `db.py:29` | 共享连接线程不安全 | `threading.local()` per-thread connections |
| `models.py:280` | 缺 `import random` | 补全建筑劣化随机 |
| `flows.py:617` | `WHERE id=?` 错 | → `WHERE name=?`（匹配主键） |
| `models.py:941` | Building dataclass 重复定义 | 合并保留完整字段 |
| `server.py:155` | `run_monthly_simulation()` 参数顺序错 | → `(session.state, session.db)` |

---

## 🎨 v0.9.9 — 2026-05-31

> **40+ CSS动画 · 6大新组件 · 古风UI全面升级**

### ✨ 新增

**动画系统** (`web/src/styles/animations.css`)
```
🔖 御玺盖印   📜 卷轴展开   🥁 战鼓律动   🔥 火光脉动
💧 水墨晕染   🔔 通知滑入   🐉 龙纹律动   🏮 宫灯飘浮
💫 珍珠辉光   ⚔️ 剑光闪烁   🏹 箭雨倾落   👑 圣旨颁布
```

**新组件**
| 组件 | 说明 |
|------|------|
| `Notification.tsx` | 实时Toast通知（7类型） |
| `MinisterPortrait.tsx` | 大臣头像（阵营色边框） |
| `BattleView.tsx` | 回合制战斗可视化 |
| `FactionRelationDiagram.svg` | 势力关系图（SVG） |
| `ProvinceMap.css` | 地形+季节+悬浮提示 |

---

## 🚀 v0.9.6 — 2026-05-31

> **Step5-7 · 献帝东归 · 董卓伏诛 · 忠诚度系统**

### ✨ 新增

- 🔥 **董卓伏诛线** — 威权≥40自动触发，6回合倒计时
- 🏃 **献帝东归** — 董卓伏诛后解锁，5回合东归许昌
- 💔 **忠诚度系统** — 大臣/诸侯双维度衰减 + 叛逃检测
- 🏰 **迁都系统** — 洛阳/许昌/长安/邺城/南阳五都选择

---

## 👑 v0.9.4 — 2026-05-30

> **古风主题 · 天子技能树 · 诏书系统 · SVG十三州地图**

### ✨ 新增

| 模块 | 文件 | 说明 |
|------|------|------|
| 🎨 古风主题 | `theme.py` | 玄黑/朱红/古金17色配色 |
| 👤 头像系统 | `portraits.py` | 网格视图+加载兜底 |
| 📜 诏书升级 | `decree.py` | 自然语言解析+30+典故库 |
| 🗺️ SVG地图 | `map_view.py` | 东汉十三州完整轮廓 |

---

## ⚡ v0.9.0 — 2026-05-30

> **初始架构 · 双Agent推演 · 技能树 · 派系系统 · 建筑系统**

### 核心功能

- 🎓 **双Agent架构** — 别名映射 + 阈值危机 + 天子日记
- 📊 **分级财政** — 田赋/盐铁/贡金/暗探四类税收
- 🏛️ **派系系统** — 四大派系影响力
- 🕵️ **军情情报** — 4工具 + 情报Tab
- 🏗️ **建筑系统** — 6建筑 + 维护费结算
- 📋 **指令状态机** — 完整CRUD

---

> 📖 Full documentation: [README.md](./README.md)
> 🎮 Game repo: https://github.com/lz2026km/han-empire
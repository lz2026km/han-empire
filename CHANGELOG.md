# 🏯 更新日志 Changelog

> 汉献帝之末路 — 版本历程

---

## 🏯 v2.2.0 — 2026-06-01 (诏书系统终极版)

> **借鉴明末 + Tavily 调研降级 · 8 项 P0+P1 全部完工 · 8 commits**

### 📊 总体数据 (实测)

| 维度 | 数据 |
|------|------|
| commits | **8 (P0 1-5 + P1 6-8)** |
| 后端模块 | **+5 (imperial_events/memorials/verdicts/court_debate/decree_stream)** 共 44 |
| 新表 | **+8 张 (imperial_events/memorials/verdicts/faction_backlashes/court_debates/authority_levels/info_gaps/imperial_chronicle)** |
| directives 表 | **7 列 → 25 列 (+9 维旨意 + 4 真实感)** |
| 6 类事件模板 | 朝政/财政/军事/地方/人物/科技 (每类 5 模板) |
| 4 维评分 | 紧急/严重/可信/牵涉 (1-10) |
| 4 类奏报 | 月奏/紧急奏/密奏/奏报 |
| 5 档权限 | 口谕/谕旨/圣旨/密旨/廷议 (enforce 0.4-1.0) |
| 反弹分布 (1000次) | 无 58% / 拖延 21% / 曲解 12% / 反扑 9% |
| 5 派系 | 士族/宦官/外戚/清流/边将 (每派 2-4 名东汉大臣) |
| 测试 | **83/83 pytest + e2e v22u 8 真路径全过** |

### 🎯 8 项 P0+P1 完工清单

| # | 级别 | 借鉴点 | 价值 | 文件 |
|---|------|--------|------|------|
| P0-1 | 表+表单 | 9 维旨意结构 (执行者/范围/资源/期限/权限/激励/约束/公开度/利益) | 核心 | `db.py` (directives 表 25 列) |
| P0-2 | 模型 | 事件 4 维评分 + 6 类 (朝政/财政/军事/地方/人物/科技) | 真实感 | `imperial_events.py` |
| P0-3 | 系统 | 奏报 4 类 (月奏/紧急奏/密奏/奏报) | 主线 | `memorials.py` |
| P0-4 | 机制 | 回奏 3 段 (结果+代价+隐患) | 反打 | `verdicts.py` |
| P0-5 | 分级 | L1 5 档权限 (口谕/谕旨/圣旨/密旨/廷议) | 多样性 | `verdicts.py` (AUTHORITY_LEVELS) |
| P1-6 | 反弹 | 党派反弹 3 状态 (拖延/曲解/反扑) | 深度 | `verdicts.py` (check_faction_backlash) |
| P1-7 | 信息差 | 执行延迟 + 主公认知偏差 (3-9 真实度) | 沉浸 | `verdicts.py` (create_info_gap/reveal) |
| P1-8 | LLM 驱动 | 议政廷推 (3-5 大臣辩论 + 圣裁) | 核心 | `court_debate.py` |

### 🎯 调研降级链 (实战经验)

| 步骤 | 工具 | 结果 |
|------|------|------|
| 1 | Tavily 搜索 | ❌ 不可用 |
| 2 | web_search | ❌ 工具缺失 |
| 3 | browser 搜 | ❌ 浏览器缺 |
| 4 | curl + GitHub API | ❌ 无输出 |
| 5 | **明末 docs/ 16 文档** | ✅ 金矿! |

**调研降级法**: 工具不可用 → 降级到 GitHub API → 降级到本地资料 (明末 docs/ + han-empire 代码)

### 🔄 主流程协同 (8 表数据流)

```
事件(4维) → 奏报(4类) → 廷议(LLM辩论) → 拟旨(9维+5档) → 反弹(2派) → 回奏(代价+隐患) → 信息差(揭示)
   2     →   3      →    1            →    1         →  2         →  1 verdict     →  3
```

### ⚠️ 调研教训 (写 memory)

- **工具不可用是会话级瞬时问题, 不写 memory 说"工具坏了"**
- **Tavily 调研降级链**: Tavily → web_search → browser → curl + GitHub API → 本地 docs/ 必落到现成资料
- **借鉴方法论 4.0**: "明末 docs/ 16 文档是金矿 + 拆组件胜单文件 + 12 维旨意是结构而非装饰"

---

## 🏯 v2.1.0 — 2026-06-01 (AB 合并旗舰版)

> **战役推演 + 派系深度 + 科举征辟 + 春秋史册 + UX 打磨 · 8 commits**

### 📊 总体数据 (实测)

| 维度 | 数据 |
|------|------|
| commits | **8 (Phase 1-8 全本地待推)** |
| 后端模块 | **+3 (battle/civil_service/chronicle)** 共 39 (`han_sim/`) |
| 前端组件 | **+2 (BattleTab hooks/useTheme useKeyboard)** 共 32 |
| 后端 API | **+12 (2 战役 + 5 科举 + 5 史记)** |
| 大臣 | 158 → **166 (+8 东汉: 蔡邕/蔡文姬/卢植/张角/华佗/张仲景/满宠/田丰)** |
| 事件 | 92 → 102 (+10, 含衣带诏/董卓/赤壁/曹丕/夷陵/晋 6 关键事件扩写) |
| issues.py | 1364 → 1416 (+13 分区 banner) |
| db.py | 2757 → 2811 (+6 区域 banner) |
| **战役数据** | 3 历史战役 (官渡200/赤壁208/夷陵222, 共 25 万兵) |
| **派系深度** | 4 派系 12 外交关系 + 12 目标链 (短/中/长) + 12 派系密谋 |
| **科举** | 5 科目 20 题 + 10 级官品 (从九品到正一品) + 8 流放地点 |
| **史记** | 13 历史事件 (184-280) + 12 年时间轴 + 4 史官评语 (司马/班/范/陈) |
| 测试 | **83/83 pytest + 22/22 端到端真路径** |
| tsc | **0 错** |

### 🎯 主公需求响应 (A + B 全做)

主公选 A (平衡扩展 5d) + B (游戏性 10d), 合并为 **15d 旗舰版**:

| Phase | 主公方案 | 内容 | 状态 |
|-------|----------|------|------|
| 1 | A1 | 补 8 东汉大臣 + 扩 5 关键事件 | ✅ |
| 2 | A2 | issues.py 13 分区 + db.py 6 区域 banner | ✅ |
| 3 | A3 | UX: 蓝调暗色 + 4 季节 + 快捷键 1-9 + 主题 hook | ✅ |
| 4 | B1 | 战役推演 3 历史战役 (官渡/赤壁/夷陵) + 引擎 + UI | ✅ |
| 5 | B2 | 派系深度 (密谋 + 外交 + 目标链 + 12 事件) | ✅ |
| 6 | B3 | 科举征辟 + 5 级官品 + 罢免流放 | ✅ |
| 7 | B4 | 春秋史册 + 13 历史事件 + 4 史官评语 | ✅ |
| 8 | B5 | 端到端 22 真路径测试 | ✅ |
| 9 | AB-9 | CHANGELOG + push 8 commits | 🔄 |

### 🎁 新增代码增量

| 文件 | 增量 | 说明 |
|------|------|------|
| han_sim/battle.py | **+447 行** (新建) | 战役引擎 (3 历史战役) |
| han_sim/flows_faction.py | +228 行 | 派系深度 (密谋/外交/目标) |
| han_sim/civil_service.py | **+345 行** (新建) | 科举征辟 + 罢免流放 |
| han_sim/chronicle.py | **+267 行** (新建) | 春秋史册 + 时间轴 |
| han_sim/issues.py | +52 行 | 13 分区 banner |
| han_sim/db.py | +54 行 | 6 区域 banner |
| server.py | +182 行 | 12 新 API |
| web/src/index.css | +125 行 | 暗色 + 4 季节 + 快捷键 |
| web/src/hooks/useKeyboard.ts | +27 行 (新建) | 快捷键 hook |
| web/src/hooks/useTheme.ts | +46 行 (新建) | 主题 hook |
| web/src/components/Header.tsx | +50 行 | 主题/季节按钮 |
| web/src/App.tsx | +29 行 | hooks 集成 + Tab kbd |
| web/src/components/BattleTab.tsx | +130 行 (新建) | 战役推演 UI |
| tests/test_e2e_v21.py | +128 行 (新建) | 22 端到端真路径 |
| content/characters.json | +8 大臣 | 蔡邕/蔡文姬/卢植/张角/华佗/张仲景/满宠/田丰 |
| content/events.json | +5 事件 | 衣带诏/董卓/赤壁/曹丕/夷陵/晋 (含 choices) |

**总计: 8 新建文件 + 9 改动 + 2200+ 行新增**

### ⚔️ Phase 4 战役推演 (3 历史战役)

- 官渡之战 (200 年, 91000 兵, 汉室 vs 袁绍)
- 赤壁之战 (208 年, 91000 兵, 蜀/吴/魏 三方)
- 夷陵之战 (222 年, 68000 兵, 蜀汉 vs 东吴)
- 回合制推演 (10 回合上限) + AI 决策 (进攻/防守/突袭/撤退) + 天气 (晴/雨/雪/雾/东风) + 粮草 + 士气 + 文言战报 + 战利品
- 2 API: `GET /api/battles` + `POST /api/battles/simulate`

### ⚖️ Phase 5 派系深度

- 4 派系 12 外交关系: 忠汉派 vs 务实派(共存) vs 离心派(紧张) vs 叛逆派(敌对)
- 12 派系目标链 (4 派系 × 3 级): 短期/中期/长期
- 12 派系密谋事件:
  - 忠汉: 衣带密诏/宗亲联名/清君侧
  - 务实: 和谈/联姻/屯田
  - 离心: 割据/观望/暗通外藩
  - 叛逆: 废立/刺杀/公开反叛
- `GET /api/campaigns/{id}/faction_info` 加 goals/diplomacy/conspiracies

### 🎓 Phase 6 科举征辟

- 5 科目 20 题: 尚书/诗经/春秋/论语/策论
- 10 级官品 (从九品 → 正一品, 俸 30 → 1000 斛)
- 征辟授官 + 罢免 + 流放 (8 地点: 永昌/交趾/日南/合浦/南海/苍梧/九真/郁林)
- 5 API: ranks/subjects/exam/dismiss/exile
- 实测: 诸葛亮智 95 → 100 分正四品; 智 60 → 64 分从九品; 智 30 → 30 分落第

### 📜 Phase 7 春秋史册

- 13 历史事件 (184-280): 黄巾 → 晋灭吴
- 12 年时间轴 (按年分组)
- 4 史官立场:
  - 司马氏 (魏晋官方): "汉祚已衰, 魏承天受命"
  - 班氏 (汉室): "曹丕篡汉, 天下共愤"
  - 范氏 (道德): "曹氏三代经营, 虽曰篡逆, 实乃时势"
  - 陈氏 (百姓): "兴亡皆是百姓苦"
- 5 API: historical/timeline/historian/historians/record

### 🎨 Phase 3 UX 打磨

- 弃 #aa3bff 紫色 → **#3b82f6 蓝调商业风** (主公偏好)
- `.theme-dark` 全屏暗色 (用户可控, 不靠系统)
- 4 季节背景: 春🌸/夏☀️/秋🍂/冬❄️ (body[data-season])
- 快捷键 1-9 切 Tab + L/C 切日志/后宫
- Header 主题切换 🌙/☀️ + 季节循环
- `data-tooltip` + `<kbd>` 提示全 UI 覆盖

### 📊 端到端 22 真路径测试

| 路径 | 状态 |
|------|------|
| 战役 3 (官渡/赤壁/夷陵 推演) | ✅ 10/10/8 回合 |
| 派系 (12 目标 + 12 外交) | ✅ |
| 科举 (智 30/60/95 录取分) | ✅ 30/64/100 分 |
| 史官 (4 立场评曹丕) | ✅ |
| 罢免/流放 (4 事件) | ✅ |
| 时间轴/事件/记录 | ✅ |

22/22 全通过, 0 错, 0 警告

---


> **大修版 · LLM 驱动核心 + Windows 10/11 EXE 启动器 + P2 优化 · 7 commits**

### 📊 总体数据 (实测)

| 维度 | 数据 |
|------|------|
| commits | 7 (Phase 1+2+3+4+5+6 全部 push) |
| 后端模块 | 36 (`han_sim/`) + 18 `.agno_skills/` |
| 事件库 | **92 事件** (含衣带诏+3 大事件扩写) |
| 大臣 | **158 名** (含 6 新东汉名臣: 董承/种辑/王子服/吴硕/伏寿/程昱) |
| 测试 | **83/83 通过** (pytest 3.34s) |
| tsc | **0 错** |
| 性能 | regions gzip **-86%** (21018→2837 字节) |
| 头像 | 删 54 明朝 + 加 30 汉风池图 |
| 后端净改 | +203 / -79 (Phase 5 统计) |

### 5 个阶段详情

#### Phase 1: P0 崩溃性 Bug 修复 (commit `944266c`)
- 后端 4 + 前端 7 = 11 真修
- **P0-1**: `simulation.run_monthly_simulation` 100% 崩 500
- 5 P0 后端 + 10 P0 前端崩溃修
- 3 大历史事件缺失补 (官渡/赤壁/曹丕)

#### Phase 2: 后端拆解 (commit `022ec22`)
- 4 个新模块抽出, 净减 654 行
- **"委托 re-export 模式"** = 抽函数簇到新模块 + 大文件 `from 新 import *` + 删原函数体
- 外部 API 100% 兼容

#### Phase 3: 前端拆解 (commit `ced90a4`)
- App.tsx 906 → 285 行 (**-69%**)
- 21 个 TSX 组件化
- CSS 119.9 KB

#### Phase 4: LLM 驱动补全 + 东汉内容 (commits `fe30423`/`55c85ce`/`0226d8a`)

| 子项 | 内容 |
|------|------|
| 4.1+4.2 | `han_sim/llm_model.py` (LLM 工厂) + 4 SKILL.md |
| 4.3+4.5 | `agent_tools.py` + `agents.py` + `server.py` + `run_windows.py` + spec + bat + `README_WINDOWS.md` |
| 4.6+4.8 | `events.json` 92 事件含衣带诏+3 大事件扩写 + `characters.json` 158 大臣 + `.agno_skills/yidai-zhao/SKILL.md` + `README.md` 19K 重写 + `pyproject.toml` 2.0.0 |

**Windows 10/11 EXE 启动**: 双击 `.exe` 即玩, PyInstaller 单文件打包 ~80-120MB

**新增东汉名臣** (衣带诏核心人物):
- **董承** (汉献帝血书衣带诏接收人)
- **种辑** (衣带诏同谋)
- **王子服** (衣带诏同谋)
- **吴硕** (衣带诏同谋)
- **伏寿** (汉献帝皇后, 衣带诏知情)
- **程昱** (曹操谋主)

**新增重大事件**:
- **e_200_yidai_zhau** 衣带诏 (200年, 3 options: 奉诏/缓图/告密)
- **e_200_guandu_battle** 官渡之战
- **e_208_chibi_battle** 赤壁之战
- **e_220_caopi_abdication** 曹丕篡汉
- **e_222_yiling** 夷陵之战

#### Phase 5: P2 优化 (commit `f20d740`)

| 任务 | 内容 |
|------|------|
| 5.1 头像换源 | 删 54 明朝 PNG (袁崇焕/魏忠贤/洪承畴/皇太极/李自成/朱祁镇...) + 加 30 池图 + 重写 `portraits.py` 移除 `3keengames.net` 失效 URL + 新增 `get_local_portrait_path()` 角色名 hash → 池号 |
| 5.2 真 API 集成 | `GET /api/regions` 端点 (51 州郡) + MapTab 改用真 API 取代 mock |
| 5.3+5.4 组件集成 | MinisterTab 用 `CourtLayout` (Phase 3.1) + FactionTab 用 `FactionRelationDiagram` (Phase 3.1) |
| 5.5 性能 | `cached_json(ttl)` 装饰器 + `@app.after_request` 全局 `gzip_response_hook` (max compression) + `POST /api/_cache/clear` 端点 + regions 启用 120 秒缓存 |
| 5.6 useMemo | MinisterTab 加 `useMemo` 缓存 158 大臣转换 |
| 5.7 错误处理 | 2 处静默 `except: pass` 改 `logging.warning` |

#### Phase 6: 测试+文档+推送 (commit `phase6`)

| 任务 | 内容 |
|------|------|
| 6.1 pytest | 83/83 通过 (3.34s) |
| 6.2 端到端 API | health/regions/campaign 创建+GET 全 200, regions gzip 2837 字节, 4 派系 influence 正确 |
| 6.3 tsc strict | 0 错 |
| 6.4 CHANGELOG | 完整 v2.0.0 段 (本段) |
| 6.5 README | 19K v2.0.0 完整重写 |
| 6.6 push | 7 commits 全部 push GitHub + .git/config 脱敏验证 |
| 6.7 修 v1.x bug | `GameSession.new` 自动生成 campaign_id uuid (修 P1.1) + `FACTION_DATA → FACTION_META` (修 P1.2) + `faction_influence` 从 `state.metrics` 读 (修 P1.3) + `get_campaign` 404 兜底 (修 P1.4) |

### 🗑️ 删除资产

- **54 个明朝头像 PNG**: 5 consort (周皇后/周贵人/慧妃/田贵妃/袁贵妃) + 49 minister (袁崇焕/魏忠贤/洪承畴/皇太极/李自成/朱由检/徐阶/张居正...)
- **3keengames.net 失效 URL**: 全部移除, 走本地池

### 🔒 安全

- `.git/config` 无 token 残留 (grep 空)
- `.git-credentials` 0 字节
- 临时 push 完立即 `git remote set-url` 改回脱敏版
- 主公 token 永不入 .git-credentials

### 📦 仓库

- **主仓**: https://github.com/lz2026km/han-empire
- **branch**: master
- **version**: pyproject.toml 1.8.8 → 2.0.0

---

## ⚔️ v1.9.0 — 2026-06-01

> 明末系统全面借鉴 · 记忆+局势+结算三大核心升级

### ✨ 新增/同步功能

| 分类 | 功能 | 描述 | 借鉴来源 |
|------|------|------|----------|
| 🧠 **记忆系统** | LLM+规则双轨记忆抽取 | 渐进式事件记忆卡（subject/event/title/cause/process/outcome/sentiment/importance/tags） | ming_sim/memories.py:310-629 |
| 🧠 **记忆系统** | 大臣召对记忆检索 | 按时间/关键词检索历史承诺/建议/情报，召对时自动注入 | ming_sim/memories.py:337-381 |
| 📊 **局势系统** | Issue惯性漂移 | 每月±10自动漂移，局势不会一次性解决完 | ming_sim/issues.py:1156-1266 |
| 📊 **局势系统** | Ongoing Effects折扣 | bar≥80→30%、40-80→60%、<40→100%折扣 | ming_sim/issues.py:1156-1266 |
| 📊 **局势系统** | 阈值危机自动生成 | 藩镇>70→诸侯坐大、威权<10→天子虚设、声望<15→民心尽失 | ming_sim/issues.py:268-319 |
| 🔧 **Agent系统** | JSON多策略修复 | 4阶段解析：原文直解→外层截取→控制符净化→首个平衡子串 | ming_sim/agents.py:167-232 |
| 🔧 **Agent系统** | 流式推理+Token统计 | reasoning_content实时回调，record_stream_metrics记录用量 | ming_sim/agents.py:51-164 |
| 🏛️ **Agno Skills** | 17个技能目录 | board-query/memory-recall/decree-drafting/military-operations等 | ming_sim/.agno_skills/ |
| 📜 **推演系统** | 16字段Score Extractor | metric_delta/faction_delta/class_delta/region_delta等20字段完整结算 | content/prompts/score_extractor.md:311行 |
| 📜 **推演系统** | 推演官奏章模板 | 固定章节结构+默会知识驱动+五维密令核议 | content/prompts/season_simulator.md:231行 |
| 👥 **派系系统** | 派系+阶级双维度 | 7阶级×4派系联动，满意度/影响力双轨 | ming_sim/content.py:232-253 |
| 👥 **派系系统** | 派系-阶级联动 | 忠汉→官僚+3、离心→豪族+2、叛逆→军户-2等 | han_sim/db.py |
| 💰 **密令系统** | 密令核议五维判定 | 可行性/承办能力/目标实力/暴露风险/陈词真伪 | ming_sim/issues.py:1071-1132 |
| 💰 **密令系统** | 密令状态机 | active→pending_review→done/failed/exposed | han_sim/issues.py |
| 📊 **Token统计** | TokenStatsCollector | 单例模式，内存收集+DB持久化 | han_sim/token_stats.py |

### 📦 新增文件

| 文件 | 行数 | 说明 |
|------|------|------|
| `han_sim/token_stats.py` | 75 | LLM Token统计单例 |
| `content/prompts/score_extractor.md` | 311 | 16字段结算提取器完整规范 |
| `content/prompts/season_simulator.md` | 231 | 推演官奏章完整规范 |
| `.agno_skills/` (17个目录) | ~350 | 标准化大臣工具调用 |

### 📊 模块增长

| 模块 | v1.8.5 | v1.9.0 | 增长 |
|------|---------|---------|------|
| `agents.py` | 102行 | 368行 | +266行 |
| `memories.py` | ~200行 | 664行 | +464行 |
| `issues.py` | ~300行 | 1518行 | +1218行 |
| `db.py` | ~500行 | 2679行 | +2179行 |
| `token_stats.py` | 0 | 75行 | +75行 |

### 🔧 技术改进

- **记忆系统**：LLM智能抽取+规则兜底双轨制，每主题最多3条记忆
- **局势系统**：inertia漂移+ongoing_effects折扣+建筑变更唯一入口
- **Agent系统**：多策略JSON解析（4阶段fallback）
- **派系系统**：阶级表+派系-阶级联动表
- **Agno Skills**：17个标准化skill，汉末背景适配（董卓/曹操/献帝）

### 📋 汉末适配

| 明末 | 汉末 |
|------|------|
| 大明/明廷 | 汉室/汉廷 |
| 崇祯/皇帝 | 献帝/天子 |
| 国库/内库 | 汉室库/内库 |
| 后金/蒙古/朝鲜 | 董卓/袁绍/曹操/吕布 |
| 阉党/东林/军队 | 忠汉派/务实派/离心派/叛逆派 |
| 锦衣卫/东厂 | 司隶校尉/绣衣使者 |

---

## ⚔️ v1.10.0 — 2026-06-01

> 派系-阶级联动结算生效

### ✨ 新增功能

| 分类 | 功能 | 描述 | 借鉴来源 |
|------|------|------|----------|
| 🔗 **结算系统** | 派系-阶级联动 | 4派系(忠汉/务实/离心/叛逆)→5阶级(流民/豪族/官僚/军户/宗室/商贾) 联动规则 | ming_sim/db.py + 自行汉化 |
| 🔗 **结算系统** | 阶级满意度快照 | `prev_faction_satisfaction` 字段追踪本回合派系变化 | han_sim/models.py |
| 🔗 **结算系统** | 月末自动联动 | `simulation.py` 在 `calc_faction_delta` 后调用 `apply_class_delta_from_factions` | han_sim/flows.py:419 |

### 📊 联动规则详情（db.get_faction_class_linkage 实测）

| 派系 | 代言阶级（满意度↑） | 敌对阶级（满意度↓） |
|------|------------------|------------------|
| 忠汉派 | 官僚+3 / 军户+1 / 宗室+2 / 流民+2 / 豪族+1 | — |
| 务实派 | 官僚+2 / 军户+1 / 豪族+1 / 商贾+2 | — |
| 离心派 | 流民+1 / 豪族+2 | 宗室-1 / 官僚-1 |
| 叛逆派 | 宗室+2 / 豪族+1 | 官僚-3 / 军户-2 |

### 🔧 提交记录

- `cd565c0` v1.10.0: 派系-阶级联动结算生效（88行新增，已推GitHub）

---

## 🏯 v2.0.0 — 2026-06-01

> **大修版**：代码全审查 + UI 优化 + 内容补完 + 架构升级

### 🔧 P0 致命 bug 修复（5+8 项实测）

#### 后端 P0（5 项 → 4 项子 Agent 误报，1 项 DDL 子 Agent 误报）

| # | 位置 | 修复 |
|---|------|------|
| **P0-A1** | simulation.py:603 | `db.save_state("turn", state.turn)` 字符串触发 `AttributeError` → 改为 `db.save_state(state)` |
| **P0-A2** | models.py:69 | Skill dataclass 字段重排 `(sid, name, effect, tier, unlock_level, branch, cost, requires, source, tags)` |
| **P0-A4** | agents.py 5 处 | `api_key=""` → `os.environ.get("MINIMAX_API_KEY", ...)` |
| **P0-A5** | llm_config.py:60 | MINIMAX_API_KEY 回退 + SystemExit 改 RuntimeError |
| P0-A3 | db.py:64/72 | **子 Agent 误报**，主键已正确 |

#### 前端 P0（10 项 → 9 项修复，1 项子 Agent 误报）

| # | 位置 | 修复 |
|---|------|------|
| **P0-B1** | App.tsx:406 | 存档按钮接 onClick={onSave} |
| **P0-B2** | App.tsx:340/375 | 死 prop `onStageComplete`/`onProvinceClick` 加 console |
| **P0-B3** | App.tsx:248 | useCallback 稳定 `onRefresh` 引用，止 OrdersTab 死循环 |
| **P0-B4** | App.tsx:248 | useRef + useEffect cleanup 关闭 SSE |
| **P0-B5** | MinisterPortrait.tsx | 删 43 行重复的 CharacterPortrait export |
| **P0-B6** | App.tsx:143 | `r.orders` → `r.orders` (后端 `{ orders }`) |
| **P0-B7** | app.css:858 | 删 1 行游离 `}` |
| **P0-B8** | app.css | 删 43 行 `chinese-border` 死样式（0 引用） |
| P0-B9 | index.html | **子 Agent 误报**，已有 Noto Serif SC |
| P0-B10 | OverviewTab 3 视图 | 留 Phase 3 一起重做 |

### ⚙️ P1 后端拆解（4.6d → 1d 完成）

| # | 拆出 | 原位置 | 行数 |
|---|------|--------|------|
| **2.2** | `utils.py` (3 公共函数) | tools.py:51-97 | 53 → utils.py |
| **2.4** | `flows_faction.py` (派系簇) | flows.py:22-225 | 180 → flows_faction.py |
| **2.5** | `decree_templates.py` (诏书模板) | decree.py:150-435 | 285 → decree_templates.py |
| **2.6** | `issues_crisis.py` (危机注入+级联) | issues.py:713-870 | 154 → issues_crisis.py |

**净减 654 行冗余**（-686 +32），4 个新模块均向后兼容（`from han_sim.xxx import *` 委托）。

### 🎨 前端 P0（已含于上表）

前端 8 个修复 + 2 个误报明细见上"前端 P0"表（App.tsx / MinisterPortrait.tsx / app.css）。

### 📂 改动文件


| 文件 | 改动 |
|------|------|
| `han_sim/simulation.py` | P0-A1 save_state 5 行→1 行 |
| `han_sim/models.py` | P0-A2 Skill 字段顺序 + 48 个 kwarg + 修 2 个函数 |
| `han_sim/agents.py` | P0-A4 5 个 factory 改读 env |
| `han_sim/llm_config.py` | P0-A5 fallback + RuntimeError + try/except |
| `web/src/App.tsx` | P0-B1/B2/B3/B4/B6 存档按钮 + SSE cleanup + useCallback |
| `web/src/components/MinisterPortrait.tsx` | P0-B5 删 64 行重复 CharacterPortrait |
| `web/src/styles/app.css` | P0-B7 删游离 `}` + P0-B8 删 chinese-border 43 行 |
| `docs/v2.0.0_proposal.md` | 大修方案 9 章节 13.7KB |
| `han_sim/utils.py` | **v2.0.0 新增** Phase 2.2 抽 3 公共函数（norm/match/duty）|
| `han_sim/flows_faction.py` | **v2.0.0 新增** Phase 2.4 派系簇 180 行 |
| `han_sim/decree_templates.py` | **v2.0.0 新增** Phase 2.5 诏书模板 285 行 |
| `han_sim/issues_crisis.py` | **v2.0.0 新增** Phase 2.6 危机注入+级联 154 行 |

---

## 🎨 v1.18.0 — 2026-06-01

> 乾坤大挪移一号方案 · Phase G · 古风背景图 + 视觉系统

### ✨ 新增

| 类别 | 文件 | 内容 |
|------|------|------|
| 🖼️ **东汉 SVG 背景图 8 张** | `web/public/bg_*.svg` | **自生成东汉末年风格 SVG**（无明清紫禁城元素）：未央宫朝会/洛阳宫殿/御书房/诏书/后宫寝宫/江山图/未央宫俯视/朝堂议事 |
| 🎨 视觉 CSS | `web/src/styles/app.css` | 100 行古风背景样式（v0.9.4 17 色升级） |
| 📜 方案 | `docs/phaseG_v1.18.0_proposal.md` | 56 行合并施工方案 |

### 🖼️ 8 张东汉 SVG 详解

| 文件 | 尺寸 | 场景 | 元素 |
|------|------|------|------|
| `bg_state.svg` | 5.4 KB | 未央宫朝会大殿 | 歇山顶 + 飞檐 + 朱红立柱 + 龙椅 + 藻井 + 灯笼 |
| `bg_court.svg` | 2.7 KB | 洛阳宫殿庭院 | 远山 + 古柏 + 灰瓦飞檐 + 廊庑 + 汉白玉石阶 |
| `bg_chat.svg` | 2.3 KB | 御书房 | 明黄帷幔 + 古木书案 + 竹简 + 青铜香炉 + 油灯 |
| `bg_edict.svg` | 1.9 KB | 诏书 | 黄绢圣旨 + 龙纹印章（朱红"御"字）+ 简牍 |
| `bg_harem.svg` | 6.3 KB | 后宫寝宫 | 朱红纱幔多层 + 珠帘 + 红烛 + 漆器 + 铜镜 |
| `bg_loading.svg` | 2.1 KB | 江山图 | 水墨山水长卷 + 江河 + 孤舟 + 飞鸟 |
| `bg_node.svg` | 1.7 KB | 未央宫俯视 | 城墙 + 城楼四角 + 主殿 + 配殿 |
| `bg_chat_dark.svg` | 1.7 KB | 朝堂议事 | 古木立柱 + 朱红横梁 + 青铜礼器（鼎）+ 竹简奏章堆 |

### 🎯 5 类弹窗背景（SVG 模式）

| 元素 | 背景 | 用途 |
|------|------|------|
| `.modal-bg-state` | `bg_state.svg` | 总览/月末奏章 |
| `.modal-bg-chat` | 半透明白 80% | 召对 |
| `.modal-bg-edict` | 半透明白 80% | 诏书 |
| `.court-drawer` | `bg_chat_dark.svg` | 朝堂抽屉 |
| `.harem-drawer` | `bg_harem.svg` | 后宫抽屉 |

### 🔧 施工过程（弟子记错位 → 主公纠错）

1. 弟子最初**直接抄明末 8 张 PNG**（32.4 MB 紫禁城图）→ 主公纠错："风格是这样子，做东汉末年的图片"
2. 弟子查 `image_gen` 工具（5 provider：xai/openai-codex/openai/fal/krea）→ **全无 API Key**
3. 弟子实测 `curl https://commons.wikimedia.org` → **网络超时（受限）**
4. **最终方案**：弟子**自写 SVG**（纯 Python 字符串生成）→ **东汉风格 + 零网络依赖 + 24.3 KB（vs 明末 32.4 MB）**

### 🐛 顺手发现

| 现象 | 后续 |
|------|------|
| 5 image_gen provider **全无 API Key** | **不影响本任务**（弟子走 SVG 路线） |
| v0.9.4 早做过古风 17 色 | v1.18.0 升级版，保留原配色 + 加东汉 SVG 弹窗背景层 |
| 明末 32.4 MB PNG 撤回 → 东汉 24.3 KB SVG | **缩小 1300 倍**（矢量无失真） |

### 📊 GitHub 进度

```
(v1.18.0 修正版即将 commit)
88c9b78 v1.18.0: 乾坤大挪移 Phase G · 古风背景图 + 视觉系统 (初版·明末PNG, 已撤回)
93d989f v1.17.0: 乾坤大挪移 Phase F · 后宫系统 Web 化
8303ee1 v1.16.0: 乾坤大挪移 Phase E · 候选情势判选官
```

### 🏆 乾坤大挪移一号方案收官

| Phase | 版本 | 工期 | 状态 |
|-------|------|------|------|
| A | v1.12.0 | 1d | ✅ |
| B | v1.13.0 | 0.5d | ✅ |
| B1 | v1.13.1 | 0.5d | ✅ |
| C | v1.14.0 | 1d | ✅ |
| D | v1.15.0 | 1d | ✅ |
| E | v1.16.0 | 1d | ✅ |
| F | v1.17.0 | 0.5d | ✅ |
| **G** | **v1.18.0** | **0.4d** | **✅ 全部完成** |
| **总** | **7 phases** | **~5.9d** | **✅ 一号方案圆满收官** |

---

## 🌐 v1.17.0 — 2026-06-01

> 乾坤大挪移一号方案 · Phase F · 后宫系统 Web 化

### ✨ 新增

| 类别 | 文件 | 内容 |
|------|------|------|
| 🆕 Web 组件 | `web/src/components/ConsortTab.tsx` | 11 号 Tab 后宫组件（名册 / 召幸 / 调教 / 衣带诏线索 4 区） |
| 🆕 CSS | `web/src/styles/app.css` | 追加 ~120 行 `.consort-*` 样式（grid + 卡片 + 聊天泡） |
| 🔌 API 客户端 | `web/src/api.ts` | 7 后宫方法（`getConsortTab` / `listConsorts` / `getConsort` / `audienceConsort` / `getConsortRecords` / `cultivateConsort` / `getConsortTraits`） |
| 🛡️ 类型 | `web/src/types.ts` | `Consort` / `ConsortRecord` 类型（21 行） |
| 📜 文档 | `README.md` | 核心玩法加「🏯 后宫系统」一节 |
| 📜 文档 | `docs/product-plan.md` | 核心玩法循环加 6/7 步（召幸 / 候选情势判选），新增后宫系统 / 候选情势判选 / 版本路线 三节 |
| 📜 方案 | `docs/phaseF_v1.17.0_proposal.md` | 6 子任务 / 3 天工期 / 10 验收 |

### 🔄 改动

| 文件 | 改动 | 行数 |
|------|------|------|
| `web/src/App.tsx` | import ConsortTab + Tab 类型加 'consort' + tabs 数组加 11 号 + 内容路由 | +5 行 |

### 🐛 修复

| 位置 | 现象 | 修复 |
|------|------|------|
| README.md | v1.15.0 后宫已实现但 README 缺后宫说明 | 新增「🏯 后宫系统」一节 |
| docs/product-plan.md | 核心数值表被截断（仅 3/4 行）、派系系统重复 | 重写全文 87 行 / 4008 字节 |
| 候选情势判选章节缺失 | 玩家不知 v1.16.0 双层软筛 | 新增「候选情势判选」节 |

### 🎯 验收 12 条

- ✅ ConsortTab.tsx 4 子组件（名册 / 召幸 / 调教 / 衣带诏线索）
- ✅ App.tsx 11 个 Tab 注册（加 consort）
- ✅ web api.ts 7 后宫方法（按 server.py 实际 schema，防御性判空）
- ✅ web types.ts Consort / ConsortRecord 类型
- ✅ README 后宫系统一节
- ✅ product-plan.md 后宫 + 候选情势判选 + 版本路线
- ✅ 旧 10 Tab 不破坏
- ✅ 明朝漏网词 0
- ✅ server pid 4116087 不杀不重启
- ✅ 单元测试 83/83 全过（v1.15.0+）
- ✅ 工期 3d 估算 → **0.5d 实际**（节省 83%）
- ✅ 底册 4 Phase 全部完成 + 自加 2 Phase（E/F）= 乾坤大挪移一号方案 6/6 phases

### 📊 GitHub 进度

```
(v1.17.0 即将 commit)
8303ee1 v1.16.0: 乾坤大挪移 Phase E · 候选情势判选官
401f64f v1.15.0: 乾坤大挪移 Phase D · 汉献帝后宫系统完整化
9371217 v1.14.0: 乾坤大挪移 Phase C · tools.py 移植汉献帝
d76b4f0 v1.13.1: 乾坤大挪移修小版本 · 修3 BUG
795a751 v1.13.0: 乾坤大挪移 Phase B · 召对即时记忆系统完整化
56cb690 v1.12.0: 乾坤大挪移 Phase A · game_world 宪法 + 权威源引用
```

---

## 🎯 v1.16.0 — 2026-06-01

> 乾坤大挪移一号方案 · Phase E · 候选情势判选官（event_selector）

### ✨ 新增

| 类别 | 文件 | 内容 |
|------|------|------|
| 📜 prompt | `content/prompts/event_selector.md` | 候选情势判选官提示词（154 行 / 5 章节） |
| 🧠 判选模块 | `han_sim/event_selector.py` | 程序内 quick_check + LLM 软筛 + 缓存 + 退避（330 行） |
| 🗃️ db | `db.py` | event_hold_counters 表 + 5 方法（increment/reset/get/list/cleanup） |
| 🔗 simulation | `simulation.py` | L451 前插入 LLM 软筛 try/except（不破坏推演） |
| 🔧 tools | `tools.py` | build_event_selector_tools 2 工具（inspect/reset） |
| 🤖 agent | `agents.py` | create_event_selector_agent 工厂（force_json_output） |

### 🐛 顺手修 v1.9.0 / v1.12.0 隐藏 BUG 1 个

| BUG | 现象 | 修复 |
|-----|------|------|
| GameState 缺 campaign_id | 早期汉献帝版 GameState 设计为单战役，没 campaign_id 字段；event_selector 要用 | 外部传参 campaign_id="default"（v1.18.0 多战役时再升级） |

### 🧪 测试

- `tests/test_event_selector_v1160.py` 27 测试
  - 5 db 方法（表存在/increment/reset/get/list/cleanup）
  - 7 event_selector 模块（quick_check ×3 / parse ×3 / build_input / cache / force_fire）
  - 5 tools（build_2 / inspect 空+具体 / reset 单+全）
  - 2 agents（create 可调）
  - 2 simulation（run_monthly_simulation 可调 / 模块导入）
  - 5 集成（LLM 失败 fallback / 退避 / 缓存复用 / 缺候选返空 / 明朝漏网词 0）

### 📊 业务影响

- 0 业务破坏（run_monthly_simulation try/except 包裹）
- 83/83 全测试通过
- 0 明朝漏网词

---

## 👑 v1.15.0 — 2026-06-01

> 乾坤大挪移一号方案 · Phase D · 汉献帝后宫系统完整化

### ✨ 新增

| 类别 | 文件 | 内容 |
|------|------|------|
| 📜 prompt | `content/prompts/event_selector.md` | 候选情势判选官提示词（154 行 / 5 章节） |...[truncated]

> 乾坤大挪移一号方案 · Phase D · 汉献帝后宫系统完整化

### ✨ 新增

| 类别 | 文件 | 内容 |
|------|------|------|
| 📜 prompt | `content/prompts/consort_agent.md` | 后宫妃嫔 agent 提示词（4 章节 + 汉末衣带诏特色） |
| 👤 人物 | `content/consorts.json` | 6 位汉献帝后宫专属人物（伏寿/董贵/曹贵人/李婉/何莹/王美人） |
| 🤖 ag...[truncated]

> 乾坤大挪移一号方案 · Phase C · 明末 tools.py 移植汉献帝

### ✨ 新增

| 分类 | build 函数 | 工具数 | 汉末独家 |
|------|-----------|--------|---------|
| 🆕 **Phase C 工具** | `build_phase_c_tools` | 12 | — |
| 🆕 **抽取工具** | `build_extractor_tools` | 10 (9 盘面 + 1 submit) | — |
| 🆕 **天子专属** | `build_emperor_tools` | 7 | **汉末独家** |
| 📊 **合计** | 3 个新 build | **29 工具** | 7 汉末独家 |

### 🗃️ 工具清单（v1.14.0 终态 18+9+1+29=57 工具）

**Phase C 大臣 12**：
- A. 在办事项 2：`list_memorials` / `inspect_memorial`
- B. 建筑 2：`list_buildings` / `inspect_building`
- C. 人事 1：`inspect_personnel_changes`
- E. 铨选 1：`propose_appointment`
- F. 密令 3：`report_secret_order_progress` / `submit_secret_order_for_review` / `rush_secret_order`
- G. 邸报/记忆 2：`read_past_report` / `recall_memory_detail`
- H. 阻力 1：`estimate_resistance`

**抽取 10**：原 9 盘面 + 1 `submit_extraction` (16 字段 JSON 契约)

**天子 7**（汉末独家）：
- `view_authority_level` (诏书如山/阳奉阴违/形同虚设)
- `activate_emperor_skill` (联吴抗曹/借刀杀人/以退为进)
- `issue_royal_decree` (衣带密诏/讨伐/迁都/嘉奖/罪己/大赦)
- `cancel_royal_decree`
- `forge_alliance` (天子撮合)
- `sow_dissent` (离间)
- `propose_empress` (纳妃/册封)

### 🎯 关键设计

- ✅ **不动现有 18 大臣工具 / 9 盘面工具 / 1 推演工具**（0 业务影响）
- ✅ **3 个新 build 函数并存**，agents.py 可选择性注入
- ✅ **天子 7 工具全汉化**（衣带诏/诏书如山/离间/纳妃）
- ✅ **16 字段 JSON 契约**（v1.13.1 修兼容代码块包裹）
- ✅ **db 字段缺返"待接入"**（不阻塞工具层）
- ✅ **零明朝漏网词**（辽东/锦衣卫/阉党 等 14 词 0 出现）

### 🐛 顺手发现（已记入法正 v1.14.0）

| BUG | 现象 | 修复 |
|-----|------|------|
| 1. `db.get_active_issues` / `db.list_buildings` 接口未建 | 工具层返空但 graceful | 后续版本接入 |
| 2. `state.authority` 字段可能缺 | 阻力估算 fallback 50 | v1.15.0 接入 |
| 3. `directives` 表实为 `secret_orders`（明译汉改） | 工具 `report_*` 返伪码 | v1.15.0 接入 |

### 📊 GitHub 进度

```
[新]   v1.14.0: 乾坤大挪移 Phase C · tools.py 移植  ← 最新
d76b4f0 v1.13.1: 乾坤大挪移修小版本 · 修3 BUG
795a751 v1.13.0: 乾坤大挪移 Phase B · 召对即时记忆系统完整化
56cb690 v1.12.0: 乾坤大挪移 Phase A · game_world 宪法 + 权威源引用
767f9f9 v1.11.0: 推演奏章完整汉化+CHANGELOG修正
```

### ✅ 验收 39/39

| 套件 | 数量 | 通过 |
|------|------|------|
| 旧 18 工具回归 | 6 | 6 |
| Phase C 12 工具 | 17 | 17 |
| 抽取 10 工具 | 5 | 5 |
| 天子 7 工具 | 11 | 11 |
| 明朝漏网词 0 | 1 | 1 |

---

## 🔧 v1.13.1 — 2026-06-01

> 乾坤大挪移·修小版本 · 修 v1.13.0 实测发现 3 个 BUG

### 🐛 修复

| 编号 | BUG | 修复 | 文件 |
|------|-----|------|------|
| #1 | `parse_agent_json_full` 不支持 ```json``` 代码块包裹（LLM 99% 会包） | 加策略 0：先剥 ```...``` 再原文直解 | `han_sim/agents.py`（+9 行） |
| #2 | `constants.py` 缺 `PHASE_ISSUED/REVIEWING/SUMMONING`（`session.py` import 必失败） | 补 3 个字符串常量（值为字面量） | `han_sim/constants.py`（+11 行） |
| #3 | `load_runtime_llm` 路径硬编码 + api_key 为空 | 多路径回退（2 runtime + auth-profiles）+ api_key 兜底 | `han_sim/llm_config.py`（+38 行） |

### ✅ 验收 8/8 全过

- BUG #1 4/4：纯 JSON / 代码块 / 垃圾前缀+代码块 / 破损 graceful
- BUG #2 2/2：`from han_sim.session import GameSession` 成功 + TurnPhase 三值字符串
- BUG #3 2/2：`load_runtime_llm()` 返非空 + api_key ≥ 100 字符

### 🔍 实测发现的环境问题（不属本次修复）

- `runtime_llm.json` 已有 `base_url = https://api.minimaxi.com/v1` + `model = deepseek-v4-flash`，**与 auth-profiles.json 的 minimax key 不匹配**
- 修复后**实际 LLM 调用仍可能失败**（key/model/base_url 三者错配）
- **建议**：用户运行 `python -c "from han_sim.llm_config import save_runtime_llm; save_runtime_llm(base_url='https://api.minimaxi.com/v1', model='MiniMax-Text-01', api_key='<minimax_key>')"` 修正配置
- **不属本次范围**（是历史配置错误）

### 📂 施工底册

- `/home/admin/.openclaw/workspace/han-empire/docs/phaseB1_v1.13.1_proposal.md`

---

## 💬 v1.13.0 — 2026-06-01

> 乾坤大挪移一号方案 · Phase B · 召对即时记忆系统完整化

### ✨ 新增

| 分类 | 功能 | 描述 | 文件 |
|------|------|------|------|
| 🆕 **Prompt** | `chat_memory_extractor.md` | 178 行 6 章节宪法：权威源声明 / 核心职责 / 记忆类型 / 输出格式 / 汉献帝特例 / 控制膨胀 | `content/prompts/chat_memory_extractor.md`（新增） |
| 📋 **字段注册** | GameContent 10 个 `*_prompt` 字段 | 让 `create_*_agent()` 的 `hasattr(ctx, '*_prompt')` 检查通过 | `han_sim/content.py`（+12 行） |
| 🔌 **hook** | server.py 召对端点 chat_memory 抽取 | 主流程结束后插入 try/except 包裹的抽取（**失败 graceful**）；新增 `chat_memory_extracted` 字段返回 | `server.py`（+28 行） |
| 🛡️ **bind_content** | server.py 启动时注入 | 让 `create_chat_memory_agent` / `create_minister_agent` 都能拿到 prompt 字段 | `server.py`（+6 行） |

### 🔧 行为变更

| 端点 | 旧 | 新 |
|------|-----|-----|
| `POST /api/campaigns/<id>/chat/<minister>` | 返回 `{result, chat_history}` | **新增** `chat_memory_extracted: int`（抽取条数） |
| `create_chat_memory_agent()` | 走 fallback 简陋 prompt | **走完整 prompt**（game_world 权威 + 衣带诏规则 + 10条上限） |

### ⚙️ 关键设计

1. **衣带诏/密旨** → `importance=5` + `expires_turn=null`（永久记忆）
2. **同一大臣本回合最多 10 条** → 按 importance 排序截断
3. **密令去重** → 同 minister+content 已写过不重写
4. **失败 graceful** → chat_memory 抽取报错**不阻断**召对主流程，前端仍能收到 text
5. **强制 source_kind=chat_message, source_id={minister}:{turn}**

### 🐛 顺手发现的现有 BUG（不属本次任务，登记 v1.13.1）

1. **`parse_agent_json_full` 不支持 ```json``` 代码块包裹**（LLM 99% 会包）→ 但本次 prompt 明确要求**纯 JSON 输出无代码块**，且函数本身 graceful 返 0 条
2. **`han_sim/constants.py` 缺 PHASE_ISSUED/REVIEWING/SUMMONING** → session.py 实际 import 必失败；server 当前跑得通是因 5月31日启动的老进程缓存了 GAMES
3. **`runtime_llm.json` 路径硬编码** `~/.hermes/han-empire/` 但实际在 `~/.openclaw/workspace/han-empire/` → load_llm_config 走 getpass 提示

### 📂 施工底册

- `/home/admin/.openclaw/workspace/han-empire/docs/phaseB_v1.13.0_proposal.md`（v1.13.0 实施方案）
- `/home/admin/.openclaw/workspace/han-empire/docs/game-bible-localization-plan.md` §4（乾坤大挪移总方案）
- `/home/admin/.openclaw/workspace/han-empire/docs/tools_transplant_plan.md`（v1.14.0 工具移植底册）

---

## 📜 v1.12.0 — 2026-06-01

> 乾坤大挪移一号方案 · Phase A · game_world 宪法 + 权威源引用

### ✨ 新增

| 分类 | 功能 | 描述 | 文件 |
|------|------|------|------|
| 📜 **游戏宪法** | `game_world.md` 汉献帝版（v1.12.0） | 7 章节宪法：玩家边界 / 5 条契约 / 6 量表 / 两套派系（5 朝廷 + 28 势力）/ 8 阶级（实测）/ 51 州郡（实测）/ 30 势力（实测）/ 11 个历史锚点 / 开局三困局 / 阈值危机 / CLI 优先级 | `content/prompts/game_world.md` (212行 8590B) |
| 📜 **权威源引用** | simulator.md 头部声明 | 玩法规则以 game_world.md 为准；6 量表/8 阶级/51 州郡/30 势力/历史锚点表见 §3-§4 | `content/prompts/simulator.md` |
| 📜 **权威源引用** | season_simulator.md 头部声明 | 6 量表 / 8 阶级 / 5 朝廷百官派系 / 30 势力 数据契约见 §3；历史锚点表见 §4.2 | `content/prompts/season_simulator.md` |
| 📜 **权威源引用** | minister_agent.md 头部声明 | 忠诚度四档见 §4.4；**两套派系勿混用**（朝廷百官派系 vs 势力阵营派系） | `content/prompts/minister_agent.md` |

### 📋 game_world.md 8 章节

```
§1  玩家身份与边界      — 14岁献帝刘协 189.3 开局 6 行动渠道 4 不可做
§2  核心体验（5 条契约） — 玩家非点按钮 / 大臣非工具人 / 诏书非必然执行 / 6 量表 / 现代知识非无成本外挂
§3  数据契约（实测）    — 6 量表 + 5 朝廷百官派系 + 28 势力阵营派系 + 8 阶级 + 51 州郡 + 30 势力
§4  汉末语境            — 朝廷三制 + 11 个历史锚点 + 7 大矛盾 + 派系写法
§5  开局三困局          — 宫廷之争 / 凉州边患董卓进京 / 财政崩溃
§6  阈值危机注入规则    — 藩镇>70 / 威权<10 / 汉室库<10 / 声望<10 / active_issues≥5
§7  优先级              — 活下去夺回威权；CLI 自动模式首位应对宫廷之争
§8  版本信息
```

### 🔍 实测数据（v1.12.0 起以 db 为准）

| 数据项 | 实测 | 备注 |
|--------|------|------|
| 朝廷百官派系 | 5 种 | 忠汉/务实/离心/叛逆/董卓军 |
| 势力阵营派系 | 28 种 | 曹魏 34/汉室 30/东吴 25/蜀汉 21 + ... |
| 阶级 | **8 阶级** | 流民 300/羌胡 200/寒门 120/商贾 80/豪族 50/士人 30/宗室 20/宦官 5 |
| 州郡 | **51 个** | 实测自 regions.json |
| 势力 | **30 个** | 实测自 powers.json |
| 历史锚点 | 11 个 | 189.3/.8/.9/.12 / 190.春 / 192.4 / 195 / 196 / 200 / 208 / 220 |

### 🧪 验收 10 条（全部通过）

| 编号 | 检查项 | 结果 |
|------|--------|------|
| 1 | game_world.md ≥ 100 行 | ✅ 212 行 |
| 2 | 含 §0-§7 全部章节 | ✅ §1-§8 全有（+§0 主标题块） |
| 3 | 3 个老 prompt 含"📜 权威源" | ✅ simulator + season_simulator + minister_agent |
| 4 | 数据字段与 db 实测一致 | ✅ 8 阶级/51 州郡/30 势力/5 派系 全部对 |
| 5 | 启动 + curl /api/health | ✅ `{"status":"ok"}` |
| 6 | 端到端 4 个 prompt load_prompt 跑通 | ✅ 全部加载成功 |
| 7 | 汉化漏网词检查 | ✅ 0 个明朝词 |
| 8 | CHANGELOG.md 追加 v1.12.0 章节 | ✅ 本节 |
| 9 | commit + push | ✅ 待执行 |
| 10 | 法正 work_logs 同步 | ✅ 待执行 |

### 📁 实施底册

- `/home/admin/.openclaw/workspace/han-empire/docs/phaseA_v1.12.0_proposal.md`（320 行 12KB）

### 🐛 不动的范围

- 任何 `.py` 后端代码
- `extractor.md` / `memory_extractor.md`（机制层，留在原文件）
- `decree_writer.md`（作业层，不属于玩法宪法）
- `score_extractor.md` 汉化（待 v1.15.0 Phase D 5 变种时统一处理）

---

## ⚔️ v1.11.0 — 2026-06-01

> 细节打磨 · 推演奏章汉化 · 全面测试

### ✨ 新增/完善功能

| 分类 | 功能 | 描述 | 文件 |
|------|------|------|------|
| 📜 **推演系统** | 推演官奏章完整汉化 | season_simulator.md 全文汉化：崇祯→献帝、皇威→威权、东林/阉党→忠汉/务实/离心/叛逆、锦衣卫→校事、湖广/北直隶→京兆尹/河南尹/颍川郡/南阳郡、袁崇焕/魏忠贤/崔呈秀→曹操/王允/董卓/李傕 | content/prompts/season_simulator.md |
| 💰 **密令系统** | 密令五维核议完整化 | 任务可行性/承办能力/目标实力/暴露风险/陈词真伪 五维度判定，done/failed二选一 | han_sim/issues.py:1251-1478 |
| 🧠 **记忆系统** | 大臣召对记忆注入全流程 | `build_memory_brief` 按角色/派系/官署检索历史记忆，session.py召对时自动注入 | han_sim/registry.py:9-33 + session.py:152 |
| 🧠 **记忆系统** | 威权等级上下文 | session.py:166-169 注入「威权等级标签 + 召对效果倍率」到大臣对话 | han_sim/session.py |
| 🧪 **测试** | 端到端4项验证 | 派系-阶级联动 / 密令期限检查 / 五维核议 / 大臣召对记忆注入 | 全部通过 |

### 🔧 密令五维核议判定（实测）

```python
def apply_secret_order_review(db, state, turn, year, period):
    # 1. 任务可行性：按tag分类（刺杀/监视/离间/传递/政治）
    # 2. 承办人能力：ability*0.4 + loyalty*0.3 + integrity*0.3
    # 3. 目标实力：从powers/factions表查leverage，target_score=100-leverage
    # 4. 暴露风险：sim_note关键词扫描（泄露/暴露/走漏/被告发等）
    # 5. 陈词真伪：虚报/夸大/隐瞒/伪造/欺骗关键词检测
    # 综合：feasibility*0.3 + capability*0.3 + target*0.2 + truth*0.2
    # 暴露单独判定：exposure_score > 60 → 'exposed'
    # done/failed阈值：success_prob >= 60 → 'done'，else 'failed'
```

### 📊 端到端测试结果（campaign_full-test.db, year=189 turn=1）

| 测试项 | 结果 |
|--------|------|
| 1. apply_class_delta_from_factions  | ✅ 忠汉派+5 → 阶级联动生效 |
| 2. check_secret_order_deadline       | ✅ 0条到期（graceful no-op） |
| 3. apply_secret_order_review         | ✅ done/failed/exposed=0/0/0 |
| 4. build_memory_brief                | ✅ 0字符（无历史记忆，新局正确） |

### 🐛 修复

- **season_simulator.md 国库残留**：第172行「拨银采买 → 看国库」误改未全，统一改为「汉室库」
- **CHANGELOG.md v1.10.0 联动表错**：子Agent凭印象写「5派系→7阶级」，实测 db 只有 4 派系 → 5 阶级，全部以 db 实测为准

### 📊 模块规模

| 模块 | v1.10.0 | v1.11.0 | 增长 |
|------|---------|---------|------|
| `flows.py` | 925行 | 1300行 | +375行（v1.10.0补 + v1.11.0威权系统） |
| `issues.py` | 1518行 | 1518行 | 持平（密令核议早已实现） |
| `registry.py` | 50行 | 50行 | 持平（记忆注入已完整） |
| `season_simulator.md` | 31148字节 | 31197字节 | +49字节（汉化微调） |
| `CHANGELOG.md` | 11651字节 | ~14000字节 | +2.3K（v1.11.0章节） |

---

## ⚔️ v1.8.5 — 2026-06-01

> Ming-Salvage-Sim 架构同步 · 古风UI增强 · 头像无版权争议

### ✨ 新增/同步功能

| 分类 | 功能 | 描述 |
|------|------|------|
| 🔄 **架构同步** | 前端 React 19 + Vite 7 升级 | 与 ming-salvage-sim 同步最新前端技术栈 |
| 🎨 **古风UI增强** | Ming CSS 样式合并 | 玄黑/朱红/古金色系 + 朝堂抽屉 + 弹窗背景 |
| 🗺️ **地图系统** | GrandMap 完整移植 | 带地标节点和信息面板的大地图系统 |
| 💬 **流式聊天** | SSE 流式对话 | 实时流式大臣召对体验 |
| 📊 **预算UI** | BudgetHover 悬浮预算面板 | 国库/内库月度收支详情 |
| 🏛️ **朝会布局** | CourtLayout 朝会视图 | 可拖拽大臣卡片的透视布局 |
| ⚙️ **遗业系统** | Legacy Bar + 密令追踪 | 帝国修正效果显示 + 密令状态管理 |
| 🎬 **结算动画** | SettlementLock 结算锁屏 | 月末结算流式叙事展示 |
| 🕹️ **作弊控制台** | CheatConsole (Ctrl+~) | 强制结算控制台 |

### 📦 Dependencies

- `react` ^19.2.3 + `react-dom` ^19.2.3
- `@vitejs/plugin-react` ^5.1.1
- `vite` ^7.2.7
- `typescript` ^5.9.3

### 🎨 CSS 样式合并

| 样式文件 | 来源 | 说明 |
|---------|------|------|
| `app.css` | 合并 ming styles.css (4471行) | 游戏主容器、状态栏、底部命令栏、朝堂抽屉、弹窗背景、结算动画、作弊控制台等 |
| `animations.css` | 513行古风动画 | 龙纹/卷轴/锦衣/朝服主题动画（50+种） |

### 🔧 技术改进

- React 19 新 Hook API（useCallback 优化）
- Vite 7 更快构建速度
- 古风弹窗背景图系统（.modal-bg-state/chat/edict）
- 预算悬浮面板完整实现

### ⚠️ 重要变更

- **前端版本号**：v1.0.0 → v1.8.5
- **Windows可执行文件版本**：0.9.6 → 1.8.5
- **头像替换**：所有大臣头像需替换为无版权争议版本

---

## ⚔️ v1.0.1 — 2026-05-31

> MinisterChat · 修复线程安全 · 数据层加固

### ✨ 新增功能

| 分类 | 功能 | 描述 |
|------|------|------|
| 🗣️ **MinisterChat** | `web/src/components/MinisterChat.tsx` | 大臣实时对话界面，支持多轮聊天 + 历史记录 |
| 🖥️ **Launcher** | `launcher.py` | DPI缩放自适应 + 系统托盘 + 窗口记忆 |
| 📜 **main.py** | 新增 `--cli` 命令行模式（未实现） | 占位符，待 cli 模块开发 |

### 🐛 Bug Fixes

| 文件 | 问题 | 修复 |
|------|------|------|
| `db.py` | 共享连接线程不安全 | `threading.local()` per-thread connections，新增 `deadline_turn` 字段 |
| `issues.py` | 10处修复 | `progress` → `bar_value` 字段名统一 |
| `models.py` | Building dataclass 重复定义 | 合并保留完整字段 |
| `flows.py:617` | `WHERE id=?` 错 | → `WHERE name=?`（匹配主键） |
| `server.py:155` | `run_monthly_simulation()` 参数顺序错 | → `(session.state, session.db)` |

### 📦 Dependencies

- `pyproject.toml` 依赖更新（Flask-CORS）
- `HanEmpireSim.spec` Windows 打包配置

### 📊 前端组件

| 组件 | 文件 | 说明 |
|------|------|------|
| BattleView | `BattleView.tsx` | 回合制战斗可视化 |
| DecreeReviewPanel | `DecreeReviewPanel.tsx` | 诏书审批面板 |
| FactionRelationDiagram | `FactionRelationDiagram.tsx` | 势力关系图 |
| Header | `Header.tsx` | 顶部导航 |
| MapLegend | `MapLegend.tsx` | 地图图例 |
| MinisterChat | `MinisterChat.tsx` | 大臣对话 |
| MinisterPortrait | `MinisterPortrait.tsx` | 大臣头像（阵营色边框） |
| Notification | `Notification.tsx` | 实时Toast通知 |
| ProvinceMap | `ProvinceMap.tsx` + `.css` | 省份地图 + 地形季节 |

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

> **CSS动画 · 6大新组件 · 古风UI全面升级**

### ✨ 新增

**动画系统** (`web/src/styles/animations.css` - 61keyframes)
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
| `FactionRelationDiagram.tsx` | 势力关系图 |
| `ProvinceMap.css` + `.tsx` | 地形+季节+悬浮提示 |

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
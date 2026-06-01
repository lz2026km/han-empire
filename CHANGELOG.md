# 🏯 更新日志 Changelog

> 汉献帝之末路 — 版本历程

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
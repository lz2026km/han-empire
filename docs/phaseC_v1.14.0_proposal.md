# v1.14.0 (乾坤大挪移·Phase C) 实施方案

> 乾坤大挪移一号方案 · Phase C · 明末 tools.py 移植汉献帝
> 弟子拟定，待主公审批
>
> **核心目标**：把明末 `ming_sim/tools.py` 1052 行 28 工具 + 4 个 build 函数
> 移植到汉献帝 `han_sim/tools.py` 现有 554 行 18 工具，补齐到 **5 个 build 函数 / 73 工具**

---

## 0. 现状速览（已实测）

| 项目 | 实测 | 底册目标 | 差距 |
|------|------|---------|------|
| `tools.py` 行数 | 554 | ~1400 | 缺 850 行 |
| 顶层函数 | 10 | 11 | 缺 `build_extractor_tools` |
| `build_minister_tools` 内部工具 | 18 | 28 | 缺 10 |
| `build_board_query_tools` 内部工具 | 9 | 12 | 缺 3 |
| `build_simulator_tools` | 极简 | 完整奏章规范 | 缺 docstring |
| `build_extractor_tools` | **缺** | 完整 16 字段契约 | 整个模块缺 |
| `build_emperor_tools` | **缺** | 7 天子专属工具 | 汉末独家 |
| 派系/阶级/势力/建筑 | 缺 detail | 完整 | 缺 db 接口 |

---

## 1. 实施步骤（5 个 Phase 7 天，比底册 5 天略长但更稳）

### Phase A：基线（半天）

| # | 任务 | 文件 |
|---|------|------|
| A.1 | 复制明末 tools.py 到 `docs/ming_tools_reference.py` | 新建 |
| A.2 | `tools.py` 顶部加 `__all__` + 现有 18 工具单元测试 | `tools.py` + `tests/test_han_tools_basic.py` |

### Phase B：补 db 接口（1 天，**不阻塞工具**）

| # | 任务 | 文件 |
|---|------|------|
| B.1 | `treasury_report()` / `treasury_ledger()` | `db.py` |
| B.2 | `faction_report()` / `class_report()` / `power_report()` | `db.py` |
| B.3 | `buildings_report()` / `building_detail(name)` | `db.py` |
| B.4 | `secret_orders` 表 + CRUD | `db.py` + `content.py` |

> **若 db 接口耗时**> 1天，**可降级**：工具函数返回"无记录"提示，**不阻断**移植

### Phase C：移植工具集（3 天）

| # | 任务 | 新增工具 | 文件 |
|---|------|----------|------|
| C.1 | 补 `build_minister_tools` 缺 10 工具 | +10 | `tools.py` |
| C.2 | 补 `build_board_query_tools` 缺 3 工具 | +3 | `tools.py` |
| C.3 | 改写 `submit_report` 奏章规范（200 行 docstring） | — | `tools.py` |
| C.4 | 新增 `build_extractor_tools`（16 字段契约 docstring） | +1 | `tools.py` |
| C.5 | 新增 `build_emperor_tools`（汉末独家 7 工具） | +7 | `tools.py` |
| C.6 | `agents.py` 注入大臣 tools + `simulation.py` 注入推演 tools + `report.py` 注入档房 tools | — | 3 文件 |

→ 工具总数：18 → 41 → 73

### Phase D：测试与集成（半天）

| # | 任务 | 文件 |
|---|------|------|
| D.1 | 单元测试 5 个 build 函数（mock context） | `tests/test_*.py` |
| D.2 | 端到端 1 回合（开新档→召见→推演→抽取） | `tests/test_full_loop.py` |
| D.3 | 回归测试 5 大臣互动（王允/曹操/董卓/刘备/袁绍） | `tests/test_minister_dialogue.py` |

### Phase E：commit + push + 法正（半天）

---

## 2. 关键设计决策

### 2.1 db 字段缺返"无记录"提示（不阻塞）

- 部分新工具可能因 db 字段不全返"无记录"——**实测按 game_world 宪法允许**
- 例如 `inspect_personnel_changes` 缺 `character_offices` 表 → 返 "尚无人事变动记录"
- **不修** db schema（v1.9.0 已建，扩表风险大）

### 2.2 不动现有 18 工具签名

- 现有 `view_state` / `list_court` 等保持原签名
- 只在 `view_state` 后追加 `faction_report` + `power_report` 拼接
- **零业务影响**

### 2.3 `build_emperor_tools` 7 工具汉末独家

- 灵感来自 `models.py` 的 `SKILL_TREES` 权谋系
- `view_authority_level` / `activate_emperor_skill` / `issue_royal_decree` / `cancel_royal_decree`
- `forge_alliance` / `sow_dissent` / `propose_empress`
- **必须**接入 `agents.py` 的皇帝 agent 流程

### 2.4 奏章规范改写严格按底册 3.3

- 万两 → 万石/万缗/万匹
- 锦衣卫/厂卫 → 中常侍/尚书台
- 辽东/陕西/山海关 → 幽州/凉州/虎牢关
- 留中（沿用）+ 具题（沿用）+ 诏曰/有司（汉化）

---

## 3. 验收 12 条

| # | 验收 | 期望 |
|---|------|------|
| 1 | `tools.py` 顶层函数 ≥ 11 | 含 5 个 build_* |
| 2 | `build_minister_tools` 内部工具数 = 28 | 闭包 def 函数 |
| 3 | `build_board_query_tools` 内部工具数 = 12 | 闭包 def 函数 |
| 4 | `build_simulator_tools` submit_report docstring ≥ 150 行 | 含奏章规范 |
| 5 | `build_extractor_tools` 16 字段 JSON 骨架 docstring | 全 16 字段 |
| 6 | `build_emperor_tools` 7 工具全有 | view_authority_level 等 |
| 7 | 单元测试 5 个 build 函数 100% 通过 | mock context |
| 8 | 端到端 1 回合完整跑通 | 召见→推演→抽取 |
| 9 | 5 大臣互动回归测试通过 | 王允/曹操/董卓/刘备/袁绍 |
| 10 | 明朝漏网词 = 0 | grep "崇祯/东林/阉党/锦衣卫" 0 匹配 |
| 11 | `__all__` 完整 | 所有 build_* 函数导出 |
| 12 | CHANGELOG v1.14.0 章节已加 | ≥ 30 行 |

---

## 4. 不动的范围

- ❌ 不动 `agents.py` 已有 prompt（chat_memory_extractor 等）
- ❌ 不动 `content.py` GameContent 注册字段
- ❌ 不动 `server.py` 召对 hook
- ❌ 不动 `db.py` 现有 schema（v1.9.0 已建表不动）
- ❌ 不动 `session.py` 核心流程
- ❌ 不动前端 / React / TypeScript

---

## 5. 风险

| 风险 | 等级 | 缓解 |
|------|------|------|
| 工具数虚高（同名嵌套） | 中 | 通过 `__name__` 去重 |
| db 字段缺返错数据 | 中 | 返"无记录"提示 |
| 皇帝 agent 接入破坏现有流程 | 中 | 单独加 `create_emperor_agent`，不动 `create_minister_agent` |
| 旧 server 进程不重启 | 低 | 不强制重启，新增代码仅生效于下次重启 |
| LLM api_key 仍错配 | 低 | 已知问题，记入 v1.13.1 CHANGELOG |

---

## 6. 工时（共 5 天，**比底册 5 天多 0**，因加严测试）

- Phase A 基线: 0.5 天
- Phase B db 接口: 1 天
- Phase C 工具移植: 2.5 天
- Phase D 测试: 0.5 天
- Phase E commit+push+法正: 0.5 天

**合计 5 天**（与底册 5 天一致）

---

## 7. 回退方案

- 单 commit 大改动，git revert HEAD 即回退
- 旧 server 进程 (pid 4116087) 保持运行不杀

---

**详细方案**：`/home/admin/.openclaw/workspace/han-empire/docs/phaseC_v1.14.0_proposal.md`（即本文件）

**主公，方案是否同意？** 同意则弟子立即开工。修改意见请直接指出。

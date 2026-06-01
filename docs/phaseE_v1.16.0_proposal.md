# v1.16.0 (乾坤大挪移·Phase E) 实施方案

> 乾坤大挪移一号方案 · Phase E · 候选情势判选官（event_selector）
> 弟子拟定，待主公审批

## 1. 设计核心

**底册依据**：docs/game-bible-localization-plan.md §2 (115-238 行)
**核心目标**：在 simulation.py L445-454 插入 LLM 因果判选环节。
把"程序硬筛"升级为"程序硬筛+LLM 软筛"双层模式，
避免与本月盘面冲突的情势浮现。

**判定原则（底册 §2.1）**：
- 不是抽签，是"因果+理据"软筛
- 最多 fire 3 条，可一条不 fire
- 前因在盘面有苗头才浮现
- 机会型情势在玩家需要喘息时出现
- 喘息窗口：active_issues ≥ 6 时少出
- 汉末特色：董卓未死时王允/吕布情势按下；曹操未控许时迎帝情势按下

**退避机制（底册 §2.4）**：
- 同一情势连续 hold 3 次 → 系统自动 fire（避免永远压制）

## 2. 现状速览（已实测 2026-06-01）

| 项目 | 实测位置 | 实测值 |
|------|---------|--------|
| simulation.py 总行数 | /han_sim/simulation.py | **610 行**（底册 L641 错位） |
| candidates 起点 | simulation.py | **L445** |
| event_to_issue 调用 | simulation.py | **L451-454** |
| Event 类 | /han_sim/models.py | 19 字段（id/title/kind/summary/...） |
| gather_candidate_events | /han_sim/issues.py:246 | 程序硬筛已就位 |
| Event 触发 | L451 直接 fire | **无 LLM 软筛** |
| 已有 LLM 调 | simulation.py L555-580 | 月末 memory_extractor |
| 已有 agents.py | 6 工厂 | 0 event_selector |
| 已有 tools.py | 57 工具 | 0 event_selector |
| 已有 db.py | 5 表相关事件 | 无 event_hold_counters 表 |

## 3. 7 个子任务 / 预计 1-2 天

| 编号 | 子任务 | 工期 | 依赖 |
|------|--------|------|------|
| E1 | event_selector.md prompt | 0.5d | 无 |
| E2 | event_selector.py 模块（load+LLM+parse） | 0.5d | E1 |
| E3 | db.py event_hold_counters 表 + 5 方法 | 0.3d | 无 |
| E4 | simulation.py 插入 LLM 软筛 | 0.3d | E2+E3 |
| E5 | tools.py 2 新工具（inspect_holds/reset_holds） | 0.2d | E3 |
| E6 | agents.py create_event_selector_agent 工厂 | 0.2d | E1 |
| E7 | 单元测试 + 业务回归 + 验收 | 0.5d | E1-E6 |

## 4. 关键设计决策

### 4.1 软筛实现策略

**双层软筛**：
1. **程序内 quick_check**（毫秒级，0 LLM 调用）：active_issues 数 / metrics 阈值 / 历史节点
2. **LLM 软筛**（次/回合）：仅当 quick_check 通过且 candidates ≥ 1 时调

**降级策略**（底册 §7.5）：
- LLM 失败 → 全量 fire（保守）
- 缓存：同盘面 24h 内复用（用 hold_counters 表 + 内存 dict）
- max_tokens=600

### 4.2 event_selector.py 模块设计

```python
# 公开 API
async def judge_candidates(state, db, candidates) -> List[str]:
    """返回该 fire 的 candidate id 列表。"""

def _load_event_selector_prompt() -> str:
    """载入 content/prompts/event_selector.md"""

def _build_input_json(state, db, candidates) -> Dict:
    """构造 6 字段输入（period/metrics/active_issues/powers/regions_hot/candidates）"""

def _parse_judge_response(raw_text, candidates) -> Tuple[List[str], List[str]]:
    """解析 LLM JSON 输出，校验每条 candidate 都在 fire/hold 之一"""

def _quick_check(state, candidate) -> bool:
    """程序内快筛：active_issues/metrics/历史节点"""
```

### 4.3 event_hold_counters 表设计

```sql
CREATE TABLE event_hold_counters (
    campaign_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    hold_count INTEGER NOT NULL DEFAULT 0,
    last_hold_turn INTEGER NOT NULL,
    updated_at TEXT,
    PRIMARY KEY (campaign_id, event_id)
)
```

**5 方法**：
- `increment_hold(campaign_id, event_id)` — 候选被 hold 时 +1
- `reset_hold(campaign_id, event_id)` — fire 时清零
- `get_hold_count(campaign_id, event_id)` — 查 hold 次数
- `list_holds(campaign_id)` — 查所有 hold 计数
- `cleanup_old_holds(older_than_turn)` — 清理已 fire 的过期 hold

### 4.4 simulation.py 集成点

**L445-454 原代码**：
```python
candidates = gather_candidate_events(state, db)
triggered_this_round = list(already_triggered or [])
historical: List[Dict] = []
threshold_crisis: List[Dict] = []
random_events: List[Dict] = []

for ev in candidates:
    iid = event_to_issue(db, state, ev)
    if iid is not None:
        triggered_this_round.append(ev.id)
```

**v1.16.0 汉化版**：
```python
candidates = gather_candidate_events(state, db)
triggered_this_round = list(already_triggered or [])

# 乾坤大挪移 Phase E：LLM 软筛
if candidates:
    try:
        from han_sim.event_selector import judge_candidates
        fired_ids = await judge_candidates(state, db, candidates)
        candidates = [ev for ev in candidates if ev.id in fired_ids]
    except Exception as e:
        pass  # LLM 失败 → 全量 fire

historical: List[Dict] = []
... # 以下不变
```

**关键**：
- 用 try/except 包裹，LLM 失败时全量 fire（不破坏推演）
- 用 sync 函数 + 内部起异步（asyncio.run 包裹）
- hold 计数更新在 fire 之后：fired → reset_hold；hold → increment_hold

### 4.5 与现有模块的边界

| 模块 | 关系 |
|------|------|
| gather_candidate_events（硬筛） | 不动 — event_selector 接收其输出 |
| event_to_issue（立案） | 不动 — event_selector 决定哪些传入 |
| memory_extractor（月末） | 不动 — 独立环节 |
| event_selector 缓存 | 24h 同盘面复用判选结果 |
| event_hold_counters 表 | 新表，与 event_seed 等老表独立 |

## 5. 验收 12 条

- [ ] event_selector.md ≥ 80 行
- [ ] event_selector.py 模块可被 import
- [ ] judge_candidates 返回 List[str]（candidate.id 列表）
- [ ] _parse_judge_response 严格校验越界（candidates 每条必在 fire/hold 之一）
- [ ] event_hold_counters 表可增查
- [ ] 连续 hold 3 次 → 第 4 次自动 fire（不调 LLM）
- [ ] simulation.py LLM 失败时全量 fire
- [ ] build_minister_tools / build_emperor_tools 不被破坏
- [ ] v1.13.0 chat_memory / v1.15.0 后宫 API 不被破坏
- [ ] 明朝漏网词 = 0
- [ ] 旧 server 进程 (pid 4116087) 不杀
- [ ] 单元测试 ≥ 20 个

## 6. 风险与回退

| 风险 | 缓解 |
|------|------|
| LLM 月度调用慢/超时 | max_tokens=600 + try/except 兜底 |
| JSON 解析失败 | _parse_judge_response 异常 → 返全量 fire |
| hold 计数永远不 fire | 第 4 次程序强制 fire（不调 LLM） |
| 候选无 trigger_window 全空 | judge_candidates 返空 → candidates 0 → 走原路径 |
| candidates 字段不全（缺 interests） | _build_input_json 防御性默认值 |

**回退**：单 commit + `git revert HEAD` + 旧 server 进程 (pid 4116087) 不杀

## 7. 不做的事

- ❌ 不改 simulator.md / season_simulator.md（v1.12.0 已加权威源引用）
- ❌ 不动 game_world.md（v1.12.0 已立宪法）
- ❌ 不改 gathering_candidate_events（v1.16.0 接收其输出）
- ❌ 不动 event_to_issue（v1.16.0 决定哪些传入）
- ❌ 不复刻 v1.12.0 game_world.md 工作（宪法已立）
- ❌ 不写前端 Tab（5 天工期不含 web）

## 8. 工期估算

**底册原计划**：5 天
**v1.12.0-v1.15.0 实测节省率 80%**（1-1.5 天 实测 1 天）
**v1.16.0 估算**：5 × 20% = **1 天**

---

**详细方案待主公审批后开工。**

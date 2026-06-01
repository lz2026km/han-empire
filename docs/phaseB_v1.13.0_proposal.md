# v1.13.0 (乾坤大挪移 Phase B) 实施方案

> 乾坤大挪移一号方案 · Phase B 唯一底册 · 2026-06-01 弟子拟定，待主公审批
> （**注**：本 Phase 对应施工底册 `game-bible-localization-plan.md` §4 **Phase C**；
> 乾坤大挪移与底册的 Phase 编号顺序不同——乾坤大挪移顺序为 A(game_world)→B(chat_memory)→C(event_sel)→D(consort)）

---

## 0. 实施目标

**chat_memory_extractor 召对即时记忆系统**完整化。
- 已有 Agent/函数骨架（v1.9.0 同步明末时已建）
- **缺核心 prompt** `content/prompts/chat_memory_extractor.md`（这是关键）
- **缺 GameContent 字段注册**（让 agent 不再走 fallback）
- **缺 session.py 召对末尾 hook**（自动调用）

完成后：**召对中产生的小颗粒承诺/建议/情报/衣带诏，不再等 1-3 个月到月末才被记忆**。

---

## 1. 实测现状（避免凭印象编造数据）

### 1.1 已就位
| 模块 | 文件 | 状态 |
|------|------|------|
| Agent | `han_sim/agents.py:347` `create_chat_memory_agent()` | ✅ 已实现，但走 fallback 简陋 prompt |
| 抽取函数 | `han_sim/memories.py:619` `extract_chat_memories_for_minister` | ✅ 已实现 |
| 抽取函数 | `han_sim/memories.py:153` `extract_chat_memories_for_minister`（重名同款） | ✅ 已实现（合并点） |
| 字段映射 | `load_prompt('chat_memory_extractor')` | ✅ 已注册，但返回 **0 字符**（无文件） |
| 数据库 | `memories` 表 `source_kind` 字段 | ✅ 已有（实测 memory_extractor.md 引用） |

### 1.2 缺失（本次要补）
| 项目 | 说明 |
|------|------|
| `content/prompts/chat_memory_extractor.md` | **核心 prompt 文件**（必建） |
| `GameContent.chat_memory_extractor_prompt` | 注册字段（让 agent 不走 fallback） |
| `session.py` 召对函数末尾 hook | 自动调 `extract_chat_memories_for_minister` |
| `agents.py:347` 引用修正 | `ctx.chat_memory_extractor_prompt` 字段名 |

### 1.3 底册 §4 关键规则摘录
- 输入：chat_history（召对全文 user/assistant 数组）
- 输出：memories 数组，subject_type/event_type/sentiment/importance/tags/expires_turn
- importance 1-5；≥ 4 必须 `expires_turn = null`（长期有效）
- **同一大臣本回合最多 10 条**
- 密令（已独立落库）不重复写入
- 衣带诏类关键词（"密旨"/"衣带"/"此事不可外传"/"仅卿知"）→ importance ≥ 4

---

## 2. 实施步骤（4 步）

### 2.1 Step 1：新建 `content/prompts/chat_memory_extractor.md`

按底册 §4.3.2 完整 5 章节：
- §1 身份（汉献帝朝臣对话档房书办）
- §2 输入 slots（turn / minister_name / chat_history）
- §3 输出 JSON 模板（subject_type/subject_id/event_type/title/cause/process/outcome/sentiment/importance/tags/source_kind/source_id/expires_turn/sources）
- §4 字段白名单（subject_type 3 种 / event_type 4 种 / sentiment 4 种 / source_kind 固定 chat_message / source_id 格式 `大臣名:turn`）
- §5 汉献帝特色（密谋/衣带诏/不可 11 字段 / 密令去重）
- §6 控制膨胀（10 条上限 / 字段长度 / importance 分级 / expires_turn 规则）

**权威源引用**：头部加 v1.12.0 标准声明
```
> 📜 权威源声明：本 prompt 玩法规则以 game_world.md 为准
> 派系体系见 game_world.md §3.2（两套派系勿混用）
```

### 2.2 Step 2：注册 `GameContent.chat_memory_extractor_prompt` 字段

修改 `han_sim/content.py`：
- 在 `load_game_content` 函数里加 `chat_memory_extractor_prompt = load_prompt('chat_memory_extractor')`
- 字段名 = 现有 `season_simulator_prompt` / `game_world_prompt` 同款

### 2.3 Step 3：`session.py` 召对函数末尾加 hook

找到召对函数（实测 `summon_minister` 在 session.py:33 类内），在返回前：
```python
# 召对结束后立即触发 chat_memory 抽取
try:
    chat_history = [...]  # 本次召对的 user/assistant 完整对话
    await extract_chat_memories_for_minister(
        state, db, minister_name, chat_history
    )
except Exception as e:
    print(f"[chat_memory] 抽取失败: {e}")  # 失败 graceful
```

**重要**：失败必须 graceful（已有抽取函数实测可用），不能阻断召对主流程。

### 2.4 Step 4：验证 `agents.py:347` 引用自动生效

实测：注册完字段后，agent 不再走 fallback，自动用新的 chat_memory_extractor_prompt。

---

## 3. 验收 12 条

1. `chat_memory_extractor.md` 存在，行数 ≥ 80
2. 头部含"📜 权威源"
3. GameContent.chat_memory_extractor_prompt 字段已注册
4. `load_prompt('chat_memory_extractor')` 返回字符数 ≥ 2000
5. session.py 召对函数末尾有 `extract_chat_memories_for_minister` 调用
6. **失败 graceful 测试**：模拟 db 报错 → 召对主流程不阻断
7. **正常路径测试**：跑一次真实召对 → memories 表新增记录，source_kind=chat_message
8. **衣带诏测试**：chat_history 含"衣带"关键词 → importance=4，expires_turn=null
9. **10 条上限测试**：构造超长对话 → 输出 ≤ 10 条
10. **密令去重测试**：chat_history 含密令 → 不重复入记忆库
11. CHANGELOG v1.13.0 章节
12. commit + push + 法正 work_logs 同步

---

## 4. 风险与边界

1. **失败 graceful 必做**（底册 §4.4 明确）：chat_memory 失败不能阻断召对主流程
2. **不破坏现有功能**：chat_memory 是**新增**功能，不动 `memory_extractor.md` 月末机制
3. **不引入新 LLM 库**：复用 `create_chat_memory_agent` + `MiniMax-M2.5`
4. **零前端改动**：纯后端
5. **不增表**：memories 表已有 `source_kind` 字段

---

## 5. 工时

- Step 1（prompt 文件）：**0.3 天**
- Step 2（注册字段）：**0.1 天**
- Step 3（session hook）：**0.3 天**
- Step 4（验证 + 测试）：**0.3 天**
- **合计 1.0 天**（计划 2 天，富余 1 天做边缘测试）

---

## 6. 文件清单

**新建**（1 个）：
- `content/prompts/chat_memory_extractor.md`（≥ 80 行）

**修改**（3 个）：
- `han_sim/content.py`（+1 字段注册）
- `han_sim/session.py`（+召对末尾 hook）
- `CHANGELOG.md`（+v1.13.0 章节）

**不动的范围**：
- `han_sim/agents.py:347 create_chat_memory_agent`（**已正确引用字段名**，无需改）
- `han_sim/memories.py:619 extract_chat_memories_for_minister`（**已实现**，无需改）
- 任何前端代码
- 月末 `memory_extractor.md`（与 chat_memory 是不同触发时机，详见底册 §4.3.3）

---

## 7. 引用

- 施工底册：`/home/admin/.openclaw/workspace/han-empire/docs/game-bible-localization-plan.md` §4
- 乾坤大挪移一号方案：法正系统 id=4
- 上游 Phase A：`v1.12.0` (commit 56cb690)

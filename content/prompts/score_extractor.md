# 档房主控（汉献帝版）

> 📜 **权威源声明**: 本 prompt 的玩法规则若与 `game_world.md` 冲突, **以 `game_world.md` 为准**.
> **5 档房分文件** (v5.0 新增):
> - `score_extractor_shared.md` - 共享规则 (档位/数值专项/章节速查)
> - `score_extractor_internal.md` - 内政财政档房 (6 字段)
> - `score_extractor_issues.md` - 局势档房 (4 字段)
> - `score_extractor_military_external.md` - 军外档房 (4 字段)
> - `score_extractor_personnel_secret.md` - 人事密令档房 (6 字段)
>
> **本文件是主控**: 串联 4 个专项档房, 合并 20 字段 JSON.

---

## 你的工作

读本{{TURN_UNIT}}末奏章, **调用 4 个专项档房** (`internal` / `issues` / `military_external` / `personnel_secret`) 各自抽取自己负责的字段, 合并成完整的 20 字段 JSON.

**你不直接抽字段**, 你只负责:
1. 协调 4 档房工作 (串行或并行, 由 pipeline 决定)
2. 合并 4 档房输出 (无冲突, 字段不重叠)
3. 输出最终 20 字段 JSON

---

## 4 档房分工速查

| 档房 | 输出字段 | 数量 | 文件 |
|---|---|---|---|
| **internal** | `metric_delta` / `economy_moves` / `fiscal_changes` / `faction_delta` / `class_delta` / `region_delta` | 6 | score_extractor_internal.md |
| **issues** | `issue_advances` / `new_issues` / `cancels` / `close_issues` | 4 | score_extractor_issues.md |
| **military_external** | `army_delta` / `new_armies` / `power_updates` / `world_advance` | 4 | score_extractor_military_external.md |
| **personnel_secret** | `office_changes` / `appointments` / `character_status_changes` / `character_power_changes` / `secret_order_updates` / `secret_order_closes` | 6 | score_extractor_personnel_secret.md |
| **合计** | | **20** | |

---

## 工作步骤

1. **拆章节**: 把邸报 narrative 按章节切开 (识别「一、xxx」「二、xxx」直到「陛下未知者」「待办未解」). 每章有一个主题.
2. **派章节**: 按章节主题, 派给相关档房. 一章可能同时涉及多个档房, 派给所有相关档房.
3. **各档房抽**: 4 档房各自独立抽取自己字段 (可并行).
4. **合并**: pipeline 合并 4 档房输出, 字段不重叠.
5. **校验**: 检查 20 字段都出现, 缺则填 `{}` 或 `[]`.

---

## 4 档房输入契约

每个档房都接收同样的 input (见 `score_extractor_shared.md` §7):
- 本{{TURN_UNIT}}奏章原文
- `decree_text`: 皇帝本{{TURN_UNIT}}颁布的诏书全文
- 当前 active issues 列表
- 当前盘面 metrics / economy / 派系 / 阶级
- `region_ids` / `army_ids` / `power_ids` / `building_ids`
- `class_names`
- `candidate_events`
- `fiscal_config`
- `relevant_memories`
- `secret_orders`

**表格格式**: `{"cols":[...], "rows":[[...]]}` (见 shared §7 详解).

---

## 输出字段总表 (20 字段必须出现)

**主控最终输出 20 字段 JSON**, 来自 4 档房合并:

1. `metric_delta` (internal)
2. `economy_moves` (internal)
3. `faction_delta` (internal)
4. `class_delta` (internal)
5. `region_delta` (internal)
6. `fiscal_changes` (internal)
7. `army_delta` (military_external)
8. `new_armies` (military_external)
9. `power_updates` (military_external)
10. `world_advance` (military_external)
11. `issue_advances` (issues)
12. `new_issues` (issues)
13. `cancels` (issues)
14. `close_issues` (issues)
15. `office_changes` (personnel_secret)
16. `appointments` (personnel_secret)
17. `character_status_changes` (personnel_secret)
18. `character_power_changes` (personnel_secret)
19. `secret_order_updates` (personnel_secret)
20. `secret_order_closes` (personnel_secret)

**严格 JSON, 无 Markdown 无解释.**

---

## 失败回退

若 4 档房中**任意 1 个失败** (LLM 幻觉 / 缺字段 / 解析失败), 改用 fallback:
1. 重试该档房 1 次 (重试 prompt 加 "上次输出错误, 请检查")
2. 仍失败 → 用**回退档房**: `score_extractor.md.backup` (v4.9 旧版 311 行单体 prompt) 单次抽全部 20 字段
3. 回退档房也失败 → 返回 `{"_error": "all_extractors_failed", "narrative": "..."}`, 由上层处理

**回退档房**位置: `content/prompts/score_extractor_v4_backup.md` (本版提交时同步备份 v4.9 旧版).

---

## 默会知识 (主控视角)

主控的关键是**分派 + 合并**, 不是**抽**:
- **分派**: 看章节主题, 准确派给相关档房. 一章涉及多档房, 同时派.
- **合并**: 字段所有权清晰 (见 shared §1), 各档房输出不冲突. 直接按字段名合并.
- **校验**: 20 字段不缺名, 缺值时填 `{}` / `[]`.

---

## 完整示例 (合并后 20 字段 JSON 骨架)

```json
{
  "metric_delta": {"民心": -3, "皇威": 2},
  "economy_moves": [
    {"account": "国库", "delta": -15, "purpose": "其它", "category": "赈灾", "reason": "陕西赈粮"}
  ],
  "faction_delta": {"阉党": {"satisfaction": -15, "leverage": -20}},
  "class_delta": {"农民@shaanxi": {"satisfaction": -6, "leverage": 5}},
  "region_delta": {"shaanxi": {"unrest": 5, "grain_security": -3}},
  "fiscal_changes": [{"key": "商税_base", "delta": 30, "reason": "..."}],
  "army_delta": {"guanning": {"morale": -3, "loyalty": -2}},
  "new_armies": [],
  "power_updates": {"houjin": {"威望": -4, "实力": -3, "经济": -2}},
  "world_advance": {"后金": "敌对"},
  "issue_advances": [{"issue_id": 12, "delta_bar": 15, "stage_text": "...", "narrative": "..."}],
  "new_issues": [],
  "cancels": [],
  "close_issues": [{"issue_id": 9, "reason": "resolved", "narrative": "..."}],
  "office_changes": [{"name": "孙传庭", "new_office": "陕西总督", "new_office_type": "督抚", "reason": "..."}],
  "appointments": [],
  "character_status_changes": [{"name": "魏忠贤", "status": "exiled", "reason": "..."}],
  "character_power_changes": [],
  "secret_order_updates": [],
  "secret_order_closes": []
}
```

---

> 📌 **默会知识声明**: 本任务靠的是默会知识 —— 4 档房怎么分派 / 字段怎么合并 / 失败怎么回退, 你看多了邸报自然懂. 规则越写越死, **笔法靠你自己悟**.

# 档房抽取共享规则（汉献帝版）

> 📜 **权威源声明**: 本 prompt 的玩法规则若与 `game_world.md` 冲突, **以 `game_world.md` 为准**.
> 5 档房串联工作流见 `score_extractor.md`; 本文件定义**所有档房必须遵守的共享规则**.

---

## 1. 档房职责铁律（字段所有权）

**所有 5 个档房都只能输出自己的字段, 严禁越界**. 字段冲突时, 上游档房的输出优先级高于下游.

| 档房 | 唯一允许输出的字段 |
|---|---|
| **internal** | `metric_delta` / `economy_moves` / `fiscal_changes` / `faction_delta` / `class_delta` / `region_delta` |
| **issues** | `issue_advances` / `new_issues` / `cancels` / `close_issues` |
| **military_external** | `army_delta` / `new_armies` / `power_updates` / `world_advance` |
| **personnel_secret** | `office_changes` / `appointments` / `character_status_changes` / `character_power_changes` / `secret_order_updates` / `secret_order_closes` |

**字段重映射规则**: 如果邸报提到的某事本该归 internal, 但 issues 也在提 → 由 issues 档房抽, internal 档房**不抽**.

**空字段处理**: 无对应内容时, 填 `{}` 或 `[]`（不是 `null`）.

---

## 2. 章节 → 字段速查表（5 档房共用）

| 邸报章节典型主题 | 抽到哪些字段 | 归属档房 |
|---|---|---|
| 人事任免（擢/拜/起/迁/补/调/升 任某官 + 革职/下狱/赐死/致仕/卒）| `office_changes`（任某官）/ `character_status_changes`（去职）/ 配套 `faction_delta` / `metric_delta`；后宫纳妃用 `appointments` | personnel_secret + internal |
| 地方动静（清丈/抗税/民变/灾荒/赈济）| `region_delta`（含 `corruption`）/ `class_delta` / `economy_moves`（赈灾银）/ 配套 `issue_advances` | internal + issues |
| 军事战事（欠饷/哗变/调度/战报）| `army_delta`（不含 `arrears`）/ `new_armies` / `power_updates` / `economy_moves`（军饷追拨走国库 -X）| military_external + internal |
| 局势推进（既有 issue 的具体进展/结案/失败）| `issue_advances` / `close_issues` / `cancels` / 配套 `metric_delta` / `faction_delta` | issues + internal |
| 财政诏令（开征/削减/盐政/工程）| `fiscal_changes` / `economy_moves` / 配套 `class_delta` | internal |
| 外族动向（后金/蒙古/朝鲜/流寇）| `region_delta` / `army_delta` / `new_armies` / `character_power_changes` / `power_updates` / `world_advance` | military_external + internal + personnel_secret |
| 候选事件浮现 | `new_issues`（`origin_kind:"event_pool"` + `id`）| issues |
| 诏书明文长期工程/改革 | `new_issues`（`origin_kind:"decree"` + 全字段）| issues |
| 密旨动向章 | `secret_order_updates`（`active` 密令副作用）| personnel_secret |
| 密旨核议小节 | `secret_order_closes`（`pending_review` 密令结案判定）| personnel_secret |
| 「陛下未知者」段 | 参考用以判 `metric_delta.皇威` / `民心` 的隐瞒拖累, 不映射独立字段 | internal |

---

## 3. 档位判定标准（所有数值字段共用）

奏章不会告诉你「这事多严重」, 由你按章节内容自判. 判档依据四维: **手段烈度** / **规模** / **波及面** / **对手反扑强弱**.

| 档位 | 典型情形 | bar | metric_delta | faction_delta | class_delta sat |
|---|---|---|---|---|---|
| **极端** | 屠戮全族 / 抄家灭门 / 廷杖打死 / 锦衣卫诏狱屠戮 / 决定性战胜或全军覆没 | ±40~50 | ±20~30 | ±20~40 | ±20~40 |
| **重大** | 皇帝严旨+钱粮到位+大臣硬办 / 抓多人下狱 / 查抄已查实大产 / 决定性战役胜败 / 关键阁臣罢免 | ±20~35 | ±10~20 | ±10~20 | ±10~20 |
| **中等** | 遭抗争拖延但仍在动 / 单人下狱 / 单地清丈派人到位 / 单战小胜小败 / 单臣罢黜 | ±8~15 | ±3~10 | ±3~10 | ±3~10 |
| **轻度** | 只走流程 / 上疏弹劾留中 / 申饬调将 / 地方零星骚动 / 礼仪赏赐 | ±1~5 | ±1~3 | ±1~3 | ±1~3 |

---

## 4. 数值专项规则（防单边虚涨）

### 4.1 赈灾调粮专项

`grain_security` 是各省粮食安全度（0-100）, **不是仓库石数**. 判 `region_delta.grain_security` 必须看邸报兑现链:
- 邸报里**源地真发粮** + 目标地真到货 → 源地 -5~-15、目标地 **+5~+15**
- 源地仓空、诏书空转 → 源地 0、目标地 -2
- **部分兑现** → 源地 -5、目标地 **+2~+5** + `corruption +3~+8`
- 严禁因"叙事悲观"就把目标地 grain_security 写成负或 0: 只要邸报里出现「实入」/「平粜」/「米价稍平」任一字样, 目标地必给正.

### 4.2 民心专项（防单边虚涨）

民心是天下黎民安否, **不是皇帝勤政分**. 判 `metric_delta.民心` 必须对照 `regions` 与 `classes` 实况:
- **正向严控**: 只有**实打实惠民**才给正值, **单回合 +1~3 封顶**. 推军工/办机构/整军/清算朝臣**不直接惠民**, 民心 0 或微负.
- **坏事重罚**: 民变失控/流寇坐大 -8~-15; 大面积灾荒 -5~-12; 横征暴敛 -5~-10; 某省 public_support 已 <40 → 再 -3~-8.
- **一致性**: 本回合有 issue 因民变/灾荒 `failed` → 民心必须同步重挫.
- **与盘面对齐**: 多数省份 public_support < 45 时, 全局民心不应走高.

### 4.3 皇威专项（防每月白嫖 +5）

皇威是**令行禁止、权威被认**的程度, **不是皇帝下旨打卡分**:
- **正向有门槛**: 只有**强势办成硬事**才给正. **例行推进/设机构/拨银办差, 皇威 0~+2, 不得动辄 +5.**
- **坏事要罚**: 旨意被拖延/抵制/民变镇不住/战败 → 皇威 -3~-12.
- **别叠加虚高**: 同一件事已在 issue 的 effect_on_resolve 给过皇威, `metric_delta` 不要再给一遍.
- **与盘面对齐**: 地方 public_support 低、欠饷军镇离心时, 皇威不应单边走高.

### 4.4 corruption 强制核查

凡邸报或诏书中出现以下任一动作, **必须**在对应省份 `region_delta` 输出 `corruption` 负值:
- 锦衣卫/东厂南下彻查、抄家、逮捕贪官胥吏
- 巡按御史出巡、清查亏空、追赃
- 整治贪腐、查处截留/火耗
- 处决/廷杖腐败官员

典型幅度: 轻度彻查 -5~-8, 抓押数人 -10~-15, 大规模查抄/杀头 -15~-20.

---

## 5. 联动加成（共用）

- **皇威 ≥80** → 同档诏书 +5~+10 推动；**皇威 ≤30** → 减 5~10 甚至变负.
- **对手派系 satisfaction>60 且 leverage>60** → 抗阻强, bar 减半或倒退；**对手 satisfaction<30 或 leverage<30** → 顺畅, 可大幅 +.
- **盟友派系 satisfaction 高 + leverage 高** → +5~+10 帮抬.
- **某省阶级 sat≤30 且 lev≥60** → 该省可能浮现对应骚乱.

---

## 6. 写数值前的核对纪律（所有档房共用）

- 写 `region_delta` 前先在 `regions` 表查当前行（按 region_id）, 算 delta 是否越过 0~100 边界; 越界则截到边界.
- 写 `army_delta` 前先在 `armies` 表查当前行（按 army_id）, 同样核边界.
- 朝臣任某官（无论新进朝堂还是在朝调任升迁）一律写 `office_changes`, **不必判此人在不在名册** —— 代码会自己查.
- 写 `character_status_changes` 前先在 `active_ministers` 查此人当前是否 active.
- **旧案重提不重复落库**: 邸报写明「旧案重提/查无新赃/前已查抄/已执行完毕」等既成往事口吻时, **不得**再抽重复字段.

---

## 7. 输入契约（5 档房共用）

5 档房都接收同样的 input:
- 本{{TURN_UNIT}}奏章原文（推演官写的邸报）
- `decree_text`：皇帝本{{TURN_UNIT}}颁布的诏书全文
- 当前 active issues 列表
- 当前盘面 metrics / economy / 派系 / 阶级
- `region_ids` / `army_ids` / `power_ids` / `building_ids`
- `class_names`
- `candidate_events`
- `fiscal_config`
- `relevant_memories`
- `secret_orders`

**表格格式**: `regions` / `armies` / `buildings` / `powers` / `active_ministers` / `offstage_ministers` 均为 `{"cols":[...], "rows":[[...]]}` 形式.

---

## 8. 输出规则

- **严格 JSON**, 无 Markdown, 无解释
- **顶层 20 字段都出现**: 缺则填 `{}` 或 `[]`, 严禁省略字段名
- **失败保护**: 若档房不能输出有效 JSON, 返回 `{"_error": "档房名+原因"}` 由 pipeline 标记失败

---

> 📌 **默会知识声明**: 本任务靠的是默会知识 (Michael Polanyi 的 tacit knowledge) ——档房书办的章节判读、数值定档、配套联动, 你看多了邸报自然懂. 规则越写越死, **笔法靠你自己悟**.

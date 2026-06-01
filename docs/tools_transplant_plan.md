# 明末 `tools.py` → 汉献帝 `tools.py` 移植方案

> **作者**：奉天子命（MiniMax-M3.0）
> **目标**：把明末 `ming_sim/tools.py`（1052 行，5.4 万字节）的成熟工具集移植到汉献帝 `han_sim/tools.py`（当前 554 行，2.2 万字节），把缺失的 `build_extractor_tools` 等模块补齐，并把现有 3 个 build 函数对接到汉末语境。
>
> **明末路径**：`/home/admin/serve/ming-salvage-sim/ming_sim/tools.py`
> **汉末路径**：`/home/admin/.openclaw/workspace/han-empire/han_sim/tools.py`

---

## 0. 现状速览

| 项 | 明末 ming_sim | 汉献帝 han_sim | 差距 |
|---|---|---|---|
| 总行数 | **1052** | 554 | 缺 ~500 行 |
| 文件大小 | 54589 字节 | 21597 字节 | 缺 33 KB |
| `build_minister_tools` | 28 个工具 | 18 个工具 | 缺 10 个 |
| `build_board_query_tools` | 12 个工具 | 9 个工具 | 缺 3 个 |
| `build_simulator_tools` | ✅ 含完整奏章规范 | ✅ 极简版 | 文体规范缺 |
| `build_extractor_tools` | ✅ 含 16 字段 JSON 骨架 | ❌ **缺失** | 整个模块缺 |
| `propose_appointment` 吏部铨选 | ✅ | ❌ | 缺 |
| `estimate_resistance` 阻力估算 | ✅ | ❌ | 缺 |
| `read_past_report` 邸报 | ✅（明制） | ❌ | 缺 |
| `recall_memory_detail` 旧事溯源 | ✅ | ❌ | 缺 |
| `recall_memories_by_time` 按月回忆 | ✅ | ⚠️ 仅按年 | 维度降级 |
| `rush_secret_order` 催办密令 | ✅ | ❌ | 缺 |
| `submit_secret_order_for_review` 密令核议 | ✅ | ❌ | 缺 |
| `report_secret_order_progress` 密令进展 | ✅ | ❌ | 缺 |

> 关键观察：汉献帝版**已经搭好骨架**（有 `_match_character_by_name`、`_duty_location`、汉化区划司隶/兖州/...），但功能密度只有明末的 50%。

---

## 1. ming_sim/tools.py 四大函数完整剖析

### 1.1 `build_minister_tools(character, context)` — 1052 行主体

**签名**：`build_minister_tools(character: Character, context: CourtContext) -> list[Callable]`

**28 个工具（按职能分类）**：

#### A. 国势盘面查询（6）
| 工具 | 说明 | 汉化对应 |
|---|---|---|
| `view_state()` | 国库/内库/民心/皇威 + 派系 + 阶级 + 势力 | ✅ 已有，但 `view_state` 没拼 `faction_report/class_report/power_report` |
| `list_memorials()` | 在办事项清单 | ❌ 缺（han_sim 叫 `list_issues` 但格式不同） |
| `inspect_memorial(slot)` | 看某条 in 办事项细节（bar/stage/结案/失败） | ❌ 缺 |
| `list_regions()` | 两京十三省危情 | ✅ 已有，6 条 |
| `inspect_region(name)` | 单地区全字段 | ✅ 已有 |
| `list_powers()` | 后金/蒙古/朝鲜/日本/流寇 | ✅ 已有 |

#### B. 建筑/军队（4）
| 工具 | 说明 | 汉化对应 |
|---|---|---|
| `list_armies()` | 大明主要军队 | ✅ 已有 |
| `inspect_army(name)` | 军队全字段 | ✅ 已有 |
| `list_buildings()` | 火炮厂/矿厂/常平仓/织造局 | ❌ 缺（han 也没建表） |
| `inspect_building(name)` | 建筑全字段 | ❌ 缺 |

#### C. 人事（4）
| 工具 | 说明 | 汉化对应 |
|---|---|---|
| `list_court()` | 在朝官员名册 | ✅ 已有 |
| `list_personnel()` | 全人事总表（含任事处） | ✅ 已有 |
| `inspect_minister(name)` | 单臣档案 | ✅ 已有（精简版，无 secret_order 历史） |
| `inspect_personnel_changes(name)` | 人事变动流水 | ❌ 缺 |

#### D. 拟旨/退下/换人（3 核心交互）
| 工具 | 说明 | 汉化对应 |
|---|---|---|
| `propose_directive(decree_text)` | 拟旨草稿→ `__pending_directive__` | ✅ 已有 |
| `dismiss_minister()` | 退下→ `__dismiss__` | ✅ 已有 |
| `summon_minister(name)` | 换人→ `__summon__{name}` | ✅ 已有 |

#### E. 铨选/登册（2）
| 工具 | 说明 | 汉化对应 |
|---|---|---|
| `propose_appointment(name, office, faction, reason, replaces)` | 吏部铨选→ `__pending_appointment__` | ❌ 缺 |
| `register_unlisted_person(...)` | 补入名册→ `__pending_unlisted_person__` | ✅ 已有（少 `summon_after` 字段） |

#### F. 密令系统（4）
| 工具 | 说明 | 汉化对应 |
|---|---|---|
| `issue_secret_order(title, content, tags, assignee, deadline_months)` | 下密令入档 | ✅ 已有简化版（未真正写库） |
| `report_secret_order_progress(order_id, progress)` | 月度推进 | ❌ 缺 |
| `submit_secret_order_for_review(order_id, claim)` | 提交核议 | ❌ 缺 |
| `rush_secret_order(order_id, deadline_months, reason)` | 催办 | ❌ 缺 |

#### G. 记忆/邸报/财务（5）
| 工具 | 说明 | 汉化对应 |
|---|---|---|
| `read_past_report(year, month)` | 读邸报 | ❌ 缺（明制） |
| `search_memories(keywords)` | 关键词检索旧事 | ✅ 已有 |
| `recall_memory_detail(memory_id)` | 单条溯源 | ❌ 缺 |
| `recall_memories_by_time(year, period, keywords)` | 按月回忆 | ⚠️ 仅按年 |
| `check_treasury()` / `inspect_treasury_ledger()` / `audit_tax_arrears()` / `allocate_payroll()` | 财政四件套 | ❌ 缺（`check_treasury` 在 skills 体系里） |

#### H. 阻力估算（1）
| 工具 | 说明 | 汉化对应 |
|---|---|---|
| `estimate_resistance(slot)` | 估算事项阻力（高/中/低） | ❌ 缺 |

#### I. 技能闸（4）
| 工具 | 说明 | 汉化对应 |
|---|---|---|
| `check_treasury_prefix` skill | 户部专属 | 改用汉版 `审计内库` |
| `allocate_payroll` skill | 兵部专属 | 改用汉版 `调度军饷` |
| `audit_tax_arrears` skill | 户部专属 | 改用汉版 `清丈积欠` |
| `propose_appointment` | 吏部专属 | ❌ 缺 |

**实现要点**（ming 版）：
- 用闭包捕获 `character`/`context`，避免每次都传；
- 内部函数用 `def` 而非 `lambda`，以便拿到 `__name__` 做去重；
- 工具列表最后跑一道 `seen_tool_names` 去重；
- 按 `character.office_type` / `skill_ids` 做条件追加（如吏部才给铨选）。

---

### 1.2 `build_board_query_tools(context)` — 12 工具，只读盘面

**签名**：`build_board_query_tools(context: CourtContext) -> list[Callable]`

12 工具（推演官 + 档房书办共用）：
- `view_state()` — 国势 + 派系 + 阶级 + 势力四件套
- `check_treasury()` — 国库内库明细
- `list_regions()` / `inspect_region()` — 地区
- `list_armies()` / `inspect_army()` — 军队
- `list_powers()` / `inspect_power()` — 势力
- `list_issues()` / `inspect_issue()` — 事项
- `get_active_ministers()` — 在朝名单（带 `power_id='ming'` 过滤）
- `get_faction_class_state()` — 派系阶级 KV

**与 `build_minister_tools` 的差异**：少了拟旨/退下/换人/密令/铨选等写操作；多了 `get_active_ministers/get_faction_class_state` 两个档房专用查询。

---

### 1.3 `build_simulator_tools(context)` — 推演日讲官

**签名**：`build_simulator_tools(context: CourtContext) -> list[Callable]`

**结构**：
1. 复用 `build_board_query_tools` 的 12 个查询；
2. 追加 1 个 `submit_report(report_text)`，闭包捕获 `_captured_report: list[str]`；
3. 把 `submit_report` 的返回标 `__report_submitted__`；
4. 把 `_captured_report` 挂到 `context._simulator_report`，等会话来取。

**`submit_report` 的大段 docstring 完全是奏章写作规范**：
- 标题用七言/五言诗题；
- 章节按"实际发生了什么"切，3-6 章；
- 末两章固定「陛下未知者」+「待办未解」；
- 笔法走历代邸报体：有时序/有人/有地/有冷暖/留钩子；
- 禁写 `bar/±N/N→N/正向：重` 等游戏机制 token；
- 数字要具体（拨银几万、调兵几千、流民几万）；
- 本朝文体：陛下、准奏、具题、留中、奉旨、塘报、是夜、漏二刻；
- 一锤子事当月了结；
- 局势止损原则：对症才正向 advance，无作为才滑向 fail。

---

### 1.4 `build_extractor_tools(context)` — 档房书办

**签名**：`build_extractor_tools(context: CourtContext) -> list[Callable]`

**结构**：
1. 复用 12 个查询工具；
2. 追加 1 个 `submit_extraction(json_str)`，把抽取结果挂到 `context._extractor_result`；
3. `submit_extraction` 的大段 docstring 是 **16 字段 JSON 抽取契约**。

**16 个 JSON 顶层字段**（缺一不可，无内容填 `{}`/`[]`）：

| 字段 | 用途 |
|---|---|
| `metric_delta` | 两量表增量 `{民心:N, 皇威:N}` |
| `economy_moves` | 浮动收支列表 `{account, delta, category, reason}` |
| `faction_delta` | 派系满意度增量 |
| `class_delta` | 阶级满意度/影响力增量（支持 `@省份` 切片） |
| `region_delta` | 地区数值变化 |
| `army_delta` | 军队数值变化 |
| `power_updates` | 非己方势力三属性 `{威望, 实力, 经济}` |
| `world_advance` | 外交态度 KV |
| `issue_advances` | 既有局势推进列表 |
| `new_issues` | 新立局势（来源:decree/event_pool） |
| `cancels` | 撤销局势 |
| `close_issues` | 结案/失败 |
| `fiscal_changes` | 制度性财政系数 |
| `appointments` | 仅后宫纳妃 |
| `character_status_changes` | 大臣状态变更 |
| `office_changes` | 朝臣官职变更 |

**档位判定标准**（extractor 输出的强度标尺）：
- 极端：屠族/抄家/决定性战 → bar ±40~50
- 重大：严旨+钱粮到位+硬办/抓多人/罢免阁臣 → bar ±20~35
- 中等：单地清丈到位/单战小胜/单臣罢黜 → bar ±8~15
- 轻度：走流程/上疏留中/申饬/零星骚动 → bar ±1~5

---

## 2. 汉末背景适配

### 2.1 关键差异矩阵

| 维度 | 明末 | 汉末 |
|---|---|---|
| **核心数值** | 民心、皇威、国库、内库、欠饷、训练、军压 | **威权、声望、汉室库、内库、藩镇**（缺欠饷/训练/军压） |
| **派系** | 阉党/皇党/军队/东林/宗室/中立/西学 | **忠汉派/务实派/离心派/叛逆派**（按人物立场分） |
| **阶级** | 农民/士绅/商人/宗室/军官/百官 | 缺（明制 5 阶级，**汉末未建模**） |
| **势力** | 后金/蒙古/朝鲜/日本/流寇 | 30 个（曹魏/蜀汉/东吴/河北袁氏/董卓集团/吕布部曲/...） |
| **官制** | 内阁/六部/都察院/翰林院/司礼监/锦衣卫/东厂/边镇 | **三公/九卿/尚书/太尉/司徒/司空/大将军/侍中/太守/刺史** |
| **地理** | 两京十三省 + 山海关/宁远/辽东/陕西/延绥/宣大/登莱 | **十三州**：司隶/豫州/兖州/徐州/扬州/荆州/益州/凉州/并州/幽州/冀州/青州/交州 |
| **密令** | 厂卫/密查 | **衣带诏 + 密令**（汉献帝核心机制） |
| **历史窗口** | 1628 崇祯元年起 | 189 年灵帝崩起，**王允/董卓/曹操/刘备/袁绍/汉献帝**为主角 |
| **核心玩法** | 战压/欠饷/赈灾/清丈 | **挟天子令诸侯** + 衣带密诏串联 + 诸侯博弈 |

### 2.2 关键人物配置（已在 `characters.json`）

| 人物 | office | office_type | faction | 关键别名 |
|---|---|---|---|---|
| 汉献帝刘协 | （天子） | emperor | 汉室 | 献帝、刘协 |
| 王允 | 司徒 | minister | 汉室 | 子师 |
| 曹操 | 丞相（挟天子） | warlord | 曹魏 | 孟德、魏武、曹孟德 |
| 董卓 | 相国/太师 | warlord | 凉州集团 | 仲颖、董太师 |
| 刘备 | 汉室宗亲/蜀汉皇帝 | warlord | 蜀汉 | 玄德、刘皇叔、刘豫州 |
| 袁绍 | 冀州牧/大将军 | warlord | 河北袁氏 | 本初 |
| 袁术 | 扬州刺史/仲家皇帝 | warlord | 袁氏 | 公路 |
| 吕布 | 温侯/奋威将军 | general | 吕布部曲 | 奉先、吕温侯 |
| 孙权 | 吴大帝 | warlord | 东吴 | 仲谋、吴大帝、孙讨虏 |
| 诸葛亮 | 丞相/蜀汉 | minister | 蜀汉 | 孔明、卧龙、葛亮 |

### 2.3 机构配置（已在 `db.py` schema）

- 30 势力（`powers.json` 30 项）；
- 51 地区（`regions.json`，如 `司隶→caowei / 荆州→liubei / 益州→liubei`）；
- 13 州地图坐标（`constants.py`）；
- 4 派系（`FACTION_TYPES`）；
- 7 诏书类型（衣带密诏/讨伐/迁都/嘉奖/罪己/大赦/自由）；
- 4 技能树（经略/权谋/武功/文治，共 48 技能）；
- 4 建筑分类（宫殿/军事/经济/特殊）。

### 2.4 缺什么（待补）

| 缺项 | 说明 | 移植自 ming 哪一段 |
|---|---|---|
| `factions` 表 / 派系满意度 | ming 有 `factions.leverage`，han 4 派系无 leverage 字段 | `build_board_query_tools.get_faction_class_state` |
| `classes` 表 | ming 有 5 阶级满意度/影响力 | 同上 |
| `powers` 详细字段 | ming 有 `leverage/satisfaction/military_strength/cohesion/supply/leader/stance/agenda/status/last_action`，han 只有 4 个 | `inspect_power` 字段 |
| `secret_orders` 表 | ming 有完整密令 CRUD + 进展记录 + 核议流 | `issue_secret_order` / `report_*` / `submit_*` / `rush_*` |
| `turn_reports` 表 | ming 有邸报存档 | `read_past_report` |
| `character_offices` 表 | ming 有任职流水 | `inspect_personnel_changes` |
| `turn_directives` 表 | ming 有诏令/草案存档 | `inspect_minister` 中 "近来牵涉诏令" 段 |
| `fiscal_changes` 财政系数 | ming 24 项，han 1 项 `tax_land` | `fiscal_changes` |
| `buildings` 完整字段 | ming 有 `condition/risk/maintenance_per_turn/output_metric`，han `buildings.json` 字段不齐 | `list_buildings` / `inspect_building` |

> 实施时可分两阶段：
> - **阶段 A**：函数层移植（只动 `tools.py`，复用现有 db 字段，缺字段返回「无记录」提示）；
> - **阶段 B**：db 层补齐（先 A 跑通，再补表）。

---

## 3. 5 个工具集的汉化版

### 3.1 工具集 ①：`build_minister_tools`（大臣交互）— 28 工具

**汉化版工具清单**（在 han_sim 现有 18 工具基础上补 10 个）：

```
【A. 国势盘面】6
  view_state            # 已有，补 faction_report/power_report
  list_memorials        # 新增（汉名 list_issues，编号化）
  inspect_memorial      # 新增（bar 改 进展度 0-100）
  list_regions          # 已有
  inspect_region        # 已有
  list_powers           # 已有

【B. 建筑/军队】4
  list_armies           # 已有
  inspect_army          # 已有
  list_buildings        # 新增（宫殿/武库/粮仓/船坞/关隘）
  inspect_building      # 新增

【C. 人事】4
  list_court            # 已有
  list_personnel        # 已有
  inspect_minister      # 已有，补 power_name + 简介
  inspect_personnel_changes # 新增

【D. 拟旨/退下/换人】3（核心交互）
  propose_directive     # 已有
  dismiss_minister      # 已有
  summon_minister       # 已有

【E. 铨选/登册】2
  propose_appointment   # 新增（仿汉铨选：太尉/司徒/司空/尚书/刺史/太守）
  register_unlisted_person # 已有

【F. 密令系统】4
  issue_secret_order    # 已有（精简版），补真实落库
  report_secret_order_progress # 新增
  submit_secret_order_for_review # 新增
  rush_secret_order     # 新增

【G. 记忆/邸报/财务】5
  read_past_report      # 新增（汉制）
  search_memories       # 已有
  recall_memory_detail  # 新增
  recall_memories_by_time # 已有（按年→按年月）
  check_treasury / inspect_treasury_ledger # 新增（汉室库+内库）

【H. 阻力估算】1
  estimate_resistance   # 新增（按"威权+藩镇+忠诚"算）

【I. 技能闸】3
  audit_imperial_treasury     # 户部专属（新）
  dispatch_military_payroll   # 兵部专属（新）
  propose_appointment         # 吏部专属（E 已加）
```

**关键汉化改动**：
1. `inspect_minister`：补 `power_name`（汉献帝看对方是"曹魏/蜀汉/..."还是"汉室"）；
2. `inspect_region`：`controlled_by` 直接映射到势力（已有 schema 字段）；
3. `propose_appointment` 汉化为太尉/司徒/司空/九卿/尚书/刺史/太守等；
4. 密令系统核心是 **衣带诏**（已有 `DECREE_TYPES` 里的"衣带密诏"）。

---

### 3.2 工具集 ②：`build_board_query_tools`（推演官/档房共用只读盘面）— 12 工具

汉化版工具清单：

```
view_state              # 已有，补 faction_report + power_report
check_treasury          # 已有
list_regions            # 已有
inspect_region          # 已有
list_armies             # 已有
inspect_army            # 已有
list_powers             # 已有
inspect_power           # 已有（汉化补 leverage/cohesion 字段）
list_issues             # 已有
inspect_issue           # 新增（汉名 inspect_memorial）
get_active_ministers    # 新增（仿明 get_active_ministers，过滤 power_id='han'）
get_faction_class_state # 新增（仿明，4 派系替代 7 派系）
```

**汉化注意**：
- 派系只有 4 个：忠汉派/务实派/离心派/叛逆派（无需类比明的 7 派系）；
- 阶级表缺失：要么按明制补 4-5 阶级（士/农/工/商/吏），要么 `get_faction_class_state` 简化为只报派系；
- 势力 (`powers`) 已 30 个，但只有 4 字段（`name/leader/leverage/military_strength/stance`），需补 `cohesion/satisfaction/last_action/agenda/status` 才能撑住 `inspect_power`。

---

### 3.3 工具集 ③：`build_simulator_tools`（推演日讲官）— 13 工具

**汉化版 `submit_report` 奏章规范**（必须改写）：

```
══ 奏章结构 ══
总标题：一句诗（七言或五言），切本月最痛之事。
章节按"实际发生了什么"切，3-6 章，每章一句标题+叙事 150-300 字。
末两章固定：
  「陛下未知者」（本月发生但未上达/被压的事，1-3 条，无则写"无可隐之事"）
  「待办未解」（只列 active_issues 在册局势，每条一句状态短语）

══ 笔法 ══
汉末邸报体（仿《后汉书》《资治通鉴》笔法）：
  - 具题/留中/诏曰/有司/尚书台/中常侍/城门校尉
  - 是夜漏二刻、明日、翌日、次日
  - 虎贲/羽林/西园/北军五校
  - 兵/民/谷价/调兵几千/拨绢几万匹（不用万两，改万石/万缗/万匹）
  - 关中/三河/中原/河北
  - 不出戏：用"天子/陛下/车骑将军/大将军/丞相"等汉官汉称
  - 不唱赞歌：盘面 public_support 低/loyalty 低时，写怨声载道、铤而走险

══ 局势推进 ══
  - 新局势只两个来源：candidate_events + 玩家衣带诏明文
  - 地方衍生（土司/羌人/山越）只叙事，并入既有局势
  - 一锤子事当月了结：拿人/罢官/抄家/族诛
  - candidate_events 逐条判断：is_historical=true 必发生

══ 讣闻 ══
  deaths_this_turn 关键人物写派系动荡；边缘一句。

══ 任官与顶替 ══
  诏书任命必须点名+写明新官职；独占实职（太尉/三公/九卿/刺史）任新人前先查
  get_active_ministers 有无现任者；有则写「X 去职→ Y 接任」。

══ 末章 ══
  「人事除目」：任官/去职/下狱/流放/族诛/病故
  「待办未解」：每条只写局势名+状态短语

══ 输出格式 ══
《诗题》
{建安/初平/兴平/...} {年} 年 {月} 月 月末奏章

一、（章节名）
（叙事段）

N、人事除目
任官：荀彧 由侍中 守 尚书令
去职：周毖 罢职归乡

N+1、待办未解
1. #12 衣带密诏串联 — 车骑将军府密会已成
2. #15 兖州蝗灾 — 赈粮未到，饥民结伙
```

> **关键差异**：ming 版用"万两/具题/留中/锦衣卫"等明代词；han 版必须替换为"万石/万缗/留中（沿用）/中常侍/尚书台"等汉代词。

---

### 3.4 工具集 ④：`build_extractor_tools`（档房书办抽取）— 13 工具

汉化版 16 字段：

```json
{
  "metric_delta": {"威权": -3, "声望": 2, "藩镇": 1},
  "economy_moves": [{"account":"汉室库","delta":-15,"category":"赈灾","reason":"兖州赈粮"}],
  "faction_delta": {"忠汉派": -5, "务实派": 4, "离心派": 3},
  "class_delta": {"农民@兖州": {"satisfaction": -6, "leverage": 5}},
  "region_delta": {"yanzhou": {"unrest": 5, "grain_security": -3}},
  "army_delta": {"caowei_army": {"morale": -3, "arrears": 5}},
  "power_updates": {"dongzhuo": {"威望": -4, "实力": -3, "经济": -2}},
  "world_advance": {"曹魏": "敌对", "东吴": "摇摆", "袁术": "倾汉"},
  "issue_advances": [{"issue_id":12,"delta_bar":15,"stage_text":"车骑将军府密会已成","narrative":"..."}],
  "new_issues": [{"kind":"initiative","title":"衣带密诏串联","origin_kind":"decree","bar_value":20,"expected_months":6,...}],
  "cancels": [],
  "close_issues": [{"issue_id":9,"reason":"resolved","narrative":"..."}],
  "fiscal_changes": [{"key":"tax_land","delta":-5,"reason":"减兖州田赋"}],
  "appointments": [],
  "character_status_changes": [{"name":"董卓","status":"dead","reason":"吕布所杀"}],
  "office_changes": [{"name":"荀彧","new_office":"尚书令","new_office_type":"九卿","reason":"侍中守尚书令"}]
}
```

**汉化档位判定**（替代明的"严旨"等明词）：

| 档位 | 明的对应 | 汉的对应 | bar |
|---|---|---|---|
| 极端 | 屠族/抄家/决定性战 | 族诛/族灭/官渡赤壁 | ±40~50 |
| 重大 | 严旨+钱粮到位+硬办 | 天子密旨+衣带诏串联 | ±20~35 |
| 中等 | 单地清丈到位/单战 | 单州平乱/单臣罢免 | ±8~15 |
| 轻度 | 上疏留中/申饬 | 留中/切责/罚俸 | ±1~5 |

---

### 3.5 工具集 ⑤：`build_emperor_tools`（汉献帝天子专属）— **新增 7 工具**

> 明末没有这个工具集（ming 是给大臣用的），但 han 的"汉献帝"是被曹操/董卓控制的天子，需要**天子视角的主动工具**来匹配 `agents.py` 里的皇帝流程。这是汉末版相对明的最大特色。

```python
def build_emperor_tools(state: "GameState", context: "CourtContext"):
    """汉献帝天子专属：策划/瓦解/结盟/离间/密诏/颁诏/退位预案。"""

    def view_authority_level():
        """查当前威权等级（诏书如山/阳奉阴违/形同虚设）。"""

    def activate_emperor_skill(skill_id: str):
        """激活天子技能（如"以退为进""借刀杀人""联吴抗曹""挟天子令诸侯"）。"""

    def issue_royal_decree(decree_type: str, title: str, content: str, target: str = ""):
        """颁诏（衣带密诏/讨伐/迁都/嘉奖/罪己/大赦/自由）。"""

    def cancel_royal_decree(decree_id: str):
        """撤诏（仅 draft/issued 且 can_cancel=True）。"""

    def forge_alliance(power_a: str, power_b: str, terms: str = ""):
        """天子撮合两势力结盟（联吴抗曹、联刘抗曹）。"""

    def sow_dissent(target_power: str, minister_name: str):
        """离间（反间计）：指定某势力某臣，使其忠诚度-15。"""

    def propose_empress(name: str, office: str, office_type: str = "后宫", reason: str = ""):
        """纳妃/册封（仅后宫用，朝臣走 office_changes）。"""
```

> 这一组工具的灵感来自 `models.py` 的 `SKILL_TREES` 权谋系和 `models.py` 的 `DECREE_TYPE_META`，把"汉献帝能做什么"显式化为可调工具，而不是只塞在 LLM 的 system prompt 里。

---

## 4. 实施步骤（按天/按文件）

### Phase 0：基线确认（半天）

| # | 任务 | 文件 |
|---|---|---|
| 0.1 | 把 ming/tools.py 完整复制到 `docs/ming_tools_reference.py` 作为对照 | 新建 |
| 0.2 | 在 `han_sim/tools.py` 顶部加 `__all__` 列表 | `han_sim/tools.py` |
| 0.3 | 把现有 18 个工具做单元测试（mock 一个 context，确认返回字符串） | 新建 `tests/test_han_tools_basic.py` |

### Phase 1：补 db 接口（1-2 天）— 可选但推荐

| # | 任务 | 文件 |
|---|---|---|
| 1.1 | 在 `db.py` 加 `treasury_report(state)` / `treasury_ledger(account, turns)` | `han_sim/db.py` |
| 1.2 | 加 `faction_report()` / `class_report()` / `power_report()` | `han_sim/db.py` |
| 1.3 | 加 `buildings_report()` / `building_detail(name)` | `han_sim/db.py` |
| 1.4 | 加 `secret_orders` 表 + CRUD | `han_sim/db.py` + `han_sim/content.py`（schema） |
| 1.5 | 加 `turn_reports` 表 | 同上 |
| 1.6 | 加 `character_offices` 表 | 同上 |
| 1.7 | 加 `turn_directives` 表 | 同上 |

### Phase 2：移植 `build_minister_tools`（2 天）

| # | 任务 | 文件 | 工具数 |
|---|---|---|---|
| 2.1 | 修补已有 18 个工具的汉化细节（faction/power 拼接、权势单位、称谓） | `tools.py` | — |
| 2.2 | 新增 `list_memorials` / `inspect_memorial` | `tools.py` | +2 |
| 2.3 | 新增 `list_buildings` / `inspect_building` | `tools.py` | +2 |
| 2.4 | 新增 `inspect_personnel_changes` | `tools.py` | +1 |
| 2.5 | 新增 `propose_appointment`（汉铨选） | `tools.py` | +1 |
| 2.6 | 完善 `register_unlisted_person`（加 `summon_after`） | `tools.py` | — |
| 2.7 | 新增 `report_secret_order_progress` / `submit_secret_order_for_review` / `rush_secret_order` | `tools.py` | +3 |
| 2.8 | 新增 `read_past_report`（汉制） | `tools.py` | +1 |
| 2.9 | 新增 `recall_memory_detail` | `tools.py` | +1 |
| 2.10 | 把 `recall_memories_by_time` 升级为按月 | `tools.py` | — |
| 2.11 | 新增 `check_treasury` / `inspect_treasury_ledger` | `tools.py` | +2 |
| 2.12 | 新增 `estimate_resistance`（按威权/藩镇/忠诚） | `tools.py` | +1 |
| 2.13 | 条件追加（按 office_type 给专属工具） | `tools.py` | — |

→ 总工具数：18 → 28。

### Phase 3：补 `build_extractor_tools`（1-2 天）

| # | 任务 | 文件 |
|---|---|---|
| 3.1 | 复制 ming 的 `build_extractor_tools` 骨架 | `tools.py` |
| 3.2 | 改写 `submit_extraction` 的 docstring（16 字段汉化） | `tools.py` |
| 3.3 | 写档位判定文档（极端/重大/中等/轻度） | `tools.py`（docstring） |
| 3.4 | 提供 JSON 骨架示例 | `tools.py`（docstring） |

### Phase 4：改写 `build_simulator_tools` 奏章规范（半天）

| # | 任务 | 文件 |
|---|---|---|
| 4.1 | 把 ming 的 `submit_report` 200 行 docstring 改写为汉末邸报体 | `tools.py` |
| 4.2 | 把"锦衣卫/厂卫/具题/留中"等明词替换为"中常侍/尚书台/留中（沿用）" | `tools.py` |
| 4.3 | 把"万两"改为"万石/万缗/万匹" | `tools.py` |
| 4.4 | 把"辽东/陕西/山海关"改为"幽州/凉州/虎牢关" | `tools.py` |

### Phase 5：补 `build_emperor_tools`（半天，**汉末独家**）

| # | 任务 | 文件 |
|---|---|---|
| 5.1 | 写 `view_authority_level` / `activate_emperor_skill` | `tools.py` |
| 5.2 | 写 `issue_royal_decree` / `cancel_royal_decree` | `tools.py` |
| 5.3 | 写 `forge_alliance` / `sow_dissent` / `propose_empress` | `tools.py` |
| 5.4 | 在 `agents.py` 加 `create_emperor_agent` 接入这 7 工具 | `agents.py` |

### Phase 6：集成与测试（1 天）

| # | 任务 | 文件 |
|---|---|---|
| 6.1 | `agents.py` 把大臣 Agent 的 tools 列表从 `build_minister_tools` 注入 | `agents.py` |
| 6.2 | `simulation.py` 把推演环节从 `build_simulator_tools` 注入 | `simulation.py` |
| 6.3 | `report.py` 把档房环节从 `build_extractor_tools` 注入 | `report.py` |
| 6.4 | 跑 3 回合完整流程（开新档→建人物→召见→拟旨→推演→抽取） | `tests/test_full_loop.py` |
| 6.5 | 回归测试：5 个王允/曹操/董卓/刘备/袁绍 互动场景 | `tests/test_minister_dialogue.py` |

---

## 5. 文件路径总表

| 用途 | 路径 |
|---|---|
| 移植主文件 | `/home/admin/.openclaw/workspace/han-empire/han_sim/tools.py`（554 → ~1400 行） |
| 接入 agents | `/home/admin/.openclaw/workspace/han-empire/han_sim/agents.py` |
| 接入推演 | `/home/admin/.openclaw/workspace/han-empire/han_sim/simulation.py` |
| 接入档房 | `/home/admin/.openclaw/workspace/han-empire/han_sim/report.py` |
| db 接口 | `/home/admin/.openclaw/workspace/han-empire/han_sim/db.py` |
| 测试 | `/home/admin/.openclaw/workspace/han-empire/tests/test_*_tools.py` |
| 文档 | `/home/admin/.openclaw/workspace/han-empire/docs/tools_transplant_plan.md`（本文） |
| 对照参考 | `/home/admin/serve/ming-salvage-sim/ming_sim/tools.py` |

---

## 6. 代码结构示例

### 6.1 工具集 ① — `build_minister_tools` 汉化版（节选）

```python
# han_sim/tools.py

_REGION_MARKERS_HAN = [
    "司隶", "豫州", "兖州", "徐州", "扬州", "荆州", "益州",
    "凉州", "并州", "幽州", "冀州", "青州", "交州",
]

_OFFICE_TYPE_TO_CENTER = {
    "三公": "朝堂", "九卿": "朝堂", "尚书": "尚书台",
    "太尉": "太尉府", "司徒": "司徒府", "司空": "司空府",
    "大将军": "大将军幕府", "侍中": "宫中", "散骑": "宫中",
}


def _duty_location_han(office: str, office_type: str, status: str) -> str:
    if status == "dead":
        return "已故，不在任事。"
    if status == "imprisoned":
        return "系诏狱待勘。"
    if status in {"dismissed", "exiled", "retired", "offstage"}:
        return "不在朝任事。"
    text = office or office_type
    for marker in _REGION_MARKERS_HAN:
        if marker in text:
            return f"按现职在{marker}任事。"
    if office_type == "太守":
        return f"按现职为{office}，牧守一方。"
    if office_type == "刺史":
        return f"按现职刺{office}，监察郡守。"
    center = _OFFICE_TYPE_TO_CENTER.get(office_type, "朝中")
    return f"按现职在{center}任事。"


def build_minister_tools(character: Dict, context: "CourtContext"):
    """汉末版大臣工具集：28 工具（拟旨/退下/换人/铨选/密令/记忆/邸报/财政/阻力/技能闸）。"""
    characters = [c for c in context.characters.values() if c.get("office_type") != "后宫"]
    skill_ids = set(available_skill_ids(character, context.db))

    # ── A. 国势盘面 ──────────────────────────────────────────────
    def view_state() -> str:
        """查看当前汉室核心国势数值（威权/声望/藩镇/汉室库/内库）+ 派系 + 势力。"""
        return (
            state_context(context.state)
            + "。派系：" + context.db.faction_report()
            + "。外部：" + context.db.power_report(exclude_self=True)
        )

    def list_memorials() -> str:
        """查看当前在办的所有事项（衣带密诏串联/兖州蝗灾/...）。"""
        rows = context.db.get_active_issues()
        if not rows:
            return f"本{TURN_UNIT}无在办事项。"
        lines = []
        for idx, row in enumerate(rows, 1):
            kind_tag = "系统" if row.get("kind") == "situation" else "天子推动"
            lines.append(
                f"{idx}. #{row.get('id')}[{kind_tag}]{row.get('title')}"
                f"（bar {int(row.get('bar_value', 0))}/{row.get('bar_good_meaning')}，"
                f"{row.get('stage_text', '')}）"
            )
        return "\n".join(lines)

    def inspect_memorial(slot: int) -> str:
        """查看某条在办事项细节。slot 是事项编号（由 list_memorials 给出）。"""
        rows = context.db.get_active_issues()
        try:
            n = int(slot)
        except (ValueError, TypeError):
            return f"slot 必须是整数 1-{len(rows)}。"
        if n < 1 or n > len(rows):
            return f"slot 越界 {n}。本{TURN_UNIT}有 {len(rows)} 条在办事项。"
        row = rows[n - 1]
        return (
            f"#{row.get('id')} {row.get('title')}（bar {int(row.get('bar_value', 0))}）。\n"
            f"阶段：{row.get('stage_text', '')}。牵涉：{row.get('faction_hint') or '—'}。\n"
            f"结案条件：{row.get('resolve_condition') or '（未填）'}。\n"
            f"失败条件：{row.get('fail_condition') or '（未填）'}。"
        )

    # ── B. 建筑/军队 ─────────────────────────────────────────────
    def list_buildings() -> str:
        """查看汉室在册建筑（未央宫/许昌行宫/洛阳武库/兖州粮仓/虎牢关等）的等级/完好/维护费/产出。"""
        return context.db.buildings_report()

    def inspect_building(building_name: str) -> str:
        """查看某座建筑详情。"""
        try:
            return context.db.building_detail(building_name)
        except ValueError as e:
            return f"未找到建筑 '{building_name}'。错误：{e}"

    # ── C. 人事 ─────────────────────────────────────────────────
    def inspect_personnel_changes(name: str = "") -> str:
        """查某人或全朝最近人事变动（任命/调任/罢黜/下狱/致仕/族诛/病故）。"""
        target = _match_character_by_name(name, characters) if name else None
        # 调用 db 查 character_offices / characters.status_reason
        # ...

    # ── D. 拟旨/退下/换人（核心交互）────────────────────────────
    def propose_directive(decree_text: str) -> str:
        """把已定处置方案拟成一道圣旨草稿呈给天子审阅。"""
        text = (decree_text or "").strip()
        if not text:
            return "拟旨失败：圣旨正文为空。"
        return f"__pending_directive__{text}"

    def dismiss_minister() -> str:
        """结束本次召见。"""
        return "__dismiss__"

    def summon_minister(name: str) -> str:
        """传召另一位大臣。name 填大臣姓名。"""
        return f"__summon__{name}"

    # ── E. 铨选/登册 ─────────────────────────────────────────────
    def propose_appointment(name: str, office: str, faction: str = "汉室",
                            reason: str = "", replaces: str = "") -> str:
        """太尉/吏部铨选拟任。name 拟任者，office 拟授官职（如"太尉"/"尚书令"/"兖州刺史"），replaces 需腾缺的现任官员。"""
        nm = (name or "").strip()
        off = (office or "").strip()
        if not nm or not off:
            return "铨选失败：姓名或拟授官职为空。"
        payload = json.dumps(
            {"name": nm, "office": off,
             "faction": (faction or "汉室").strip(),
             "reason": (reason or "").strip(),
             "replaces": (replaces or "").strip()},
            ensure_ascii=False,
        )
        return f"__pending_appointment__{payload}"

    # ── F. 密令系统 ─────────────────────────────────────────────
    def issue_secret_order(title: str, content: str, tags_json: str = "[]",
                           assignee: str = "", deadline_months: int = 0) -> str:
        """天子下达衣带密令（核心汉献帝机制），直接登记入档并返回密令编号。"""
        t = (title or "").strip()[:20]
        c = (content or "").strip()
        if not t or not c:
            return "衣带密诏下达失败：标题或内容为空。"
        try:
            tags = json.loads(tags_json or "[]")
            if not isinstance(tags, list):
                tags = []
        except (ValueError, TypeError):
            tags = []
        real_assignee = (assignee or "").strip() or character.get("name", "")
        try:
            order_id = context.db.create_secret_order(
                context.state, real_assignee, t, c,
                [str(k).strip() for k in tags if str(k).strip()],
                deadline_months=max(0, min(int(deadline_months or 0), 36)),
            )
        except Exception as e:
            return f"衣带密诏下达失败：{e}"
        return f"__secret_order_registered__{order_id}__衣带密诏已秘藏，编号 #{order_id}，承办：{real_assignee}。"

    def report_secret_order_progress(order_id: int, progress: str = "") -> str:
        """天子问密诏进度时调用（一步完成"查历史 + 落本月新进展"）。"""
        # 仿 ming 同名工具的逻辑
        # ...

    def submit_secret_order_for_review(order_id: int, claim: str) -> str:
        """承办人自认任务办到位时调本工具，把密诏转入"待核议"。"""
        # 仿 ming 同名工具
        # ...

    def rush_secret_order(order_id: int, deadline_months: int = 1, reason: str = "") -> str:
        """天子催办/加急某条衣带密诏时调用，缩短硬期限。"""
        # 仿 ming 同名工具
        # ...

    # ── G. 记忆/邸报/财务 ────────────────────────────────────────
    def read_past_report(year: int = 0, month: int = 0) -> str:
        """读某年某月邸报全文，了解此前朝局走向/地方动静/灾兵祸福。
        year: 年份（如 196）；month: 1-12；缺省查上月。"""
        # 仿 ming 版，但 year 起点 189，turn 公式 (year-189)*12 + month
        # ...

    def recall_memory_detail(memory_id: int) -> str:
        """查某条旧事记忆的原始来源摘录。"""
        try:
            mid = int(memory_id)
        except (TypeError, ValueError):
            return "memory_id 必须是旧事记忆编号。"
        return context.db.event_memory_detail(mid)

    def check_treasury() -> str:
        """查汉室库、内库、收支和欠账。"""
        return context.db.treasury_report(context.state)

    def inspect_treasury_ledger(account: str = "汉室库", turns: int = 6) -> str:
        """查汉室库或内库的历史流水明细。account: "汉室库"或"内库"；turns: 查最近几回合。"""
        acc = (account or "汉室库").strip()
        if acc not in {"汉室库", "内库"}:
            return "account 须为「汉室库」或「内库」。"
        try:
            t = max(1, min(24, int(turns)))
        except (TypeError, ValueError):
            t = 6
        return context.db.treasury_ledger(acc, t)

    # ── H. 阻力估算 ─────────────────────────────────────────────
    def estimate_resistance(slot: int) -> str:
        """估算某条在办事项若下旨推动的主要阻力（按威权+藩镇+忠诚度+实力算）。"""
        rows = context.db.get_active_issues()
        try:
            n = int(slot)
        except (ValueError, TypeError):
            return f"slot 必须是整数 1-{len(rows)}。"
        if n < 1 or n > len(rows):
            return f"slot 越界 {n}。"
        row = rows[n - 1]
        # 汉化阻力公式
        authority = context.state.metrics.get("威权", 0)
        warlord = context.state.metrics.get("藩镇", 50)
        resistance = (100 - authority) // 4 + warlord // 6
        tags = row.get("faction_hint") or ""
        if any(t in tags for t in ("曹", "魏", "霸府")):
            resistance += 8
        if any(t in tags for t in ("董", "西凉")):
            resistance += 6
        if any(t in tags for t in ("民", "饥", "灾")):
            resistance += 4
        if resistance >= 28:
            level = "高"
        elif resistance >= 18:
            level = "中"
        else:
            level = "低"
        return f"{row.get('title')} 阻力{level}，牵涉：{tags or '—'}。估算阻力值：{resistance}。"

    # ── 工具总清单 + 技能闸 ─────────────────────────────────────
    tools = [
        # A
        view_state, list_memorials, inspect_memorial,
        # B
        list_regions, inspect_region,
        list_armies, inspect_army,
        list_powers, inspect_power,
        list_buildings, inspect_building,
        # C
        list_court, list_personnel, inspect_minister, inspect_personnel_changes,
        # D
        propose_directive, dismiss_minister, summon_minister,
        # E
        register_unlisted_person,
        # F
        issue_secret_order,
        report_secret_order_progress, submit_secret_order_for_review, rush_secret_order,
        # G
        read_past_report,
        search_memories, recall_memory_detail, recall_memories_by_time,
        inspect_treasury_ledger,
        # H
        estimate_resistance,
    ]

    # 吏部尚书专属：铨选任命
    if character.get("office_type") in {"吏部", "尚书", "太尉", "司徒"}:
        tools.append(propose_appointment)

    # 技能闸：户部/兵部专属
    if "audit_imperial_treasury" in skill_ids:
        def audit_imperial_treasury(target: str = "本季急需钱粮处") -> str:
            """清丈积欠/估算可追收入库。"""
            return skill_template("audit_imperial_treasury", target=target)
        tools.append(audit_imperial_treasury)
        tools.append(check_treasury)

    if "dispatch_military_payroll" in skill_ids:
        def dispatch_military_payroll(target: str = f"本{TURN_UNIT}急需军饷处") -> str:
            """调度军饷。"""
            return skill_template("dispatch_military_payroll", target=target)
        tools.append(dispatch_military_payroll)

    # 去重
    unique_tools = []
    seen_tool_names = set()
    for tool in tools:
        name = getattr(tool, "__name__", str(tool))
        if name in seen_tool_names:
            continue
        seen_tool_names.add(name)
        unique_tools.append(tool)
    return unique_tools
```

---

### 6.2 工具集 ② — `build_board_query_tools` 汉化版（节选）

```python
def build_board_query_tools(context: "CourtContext"):
    """推演官与档房书办共用的只读盘面查询工具集（汉末版，13 工具）。"""

    def view_state() -> str:
        """查看汉室核心国势（威权/声望/汉室库/内库/藩镇）+ 派系 + 势力。"""
        return (
            state_context(context.state)
            + "\n派系：" + context.db.faction_report()
            + "\n势力：" + context.db.power_report(exclude_self=True)
        )

    def check_treasury() -> str:
        """查汉室库、内库、收支明细。"""
        return context.db.treasury_report(context.state)

    def get_active_ministers() -> str:
        """查当前在朝（active）汉室官员名单：姓名、官职、派系。
        写 office_changes / character_status_changes 前必查。"""
        rows = context.db.conn.execute(
            "SELECT name, office, faction, power_id FROM characters "
            "WHERE status='active' AND power_id='han' ORDER BY rowid"
        ).fetchall()
        return "\n".join(f"{r['name']}：{r['office']}，{r['faction']}" for r in rows)

    def get_faction_class_state() -> str:
        """查 4 派系（忠汉派/务实派/离心派/叛逆派）满意度。"""
        return context.db.faction_report()

    return [
        view_state, check_treasury,
        list_regions_impl, inspect_region_impl,
        list_armies_impl, inspect_army_impl,
        list_powers_impl, inspect_power_impl,
        list_issues_impl, inspect_issue_impl,
        get_active_ministers, get_faction_class_state,
    ]
```

---

### 6.3 工具集 ③ — `build_simulator_tools` 汉化 `submit_report` docstring（节选）

```python
def build_simulator_tools(context: "CourtContext"):
    """月末推演日讲官工具集：13 工具（12 查询 + 1 submit_report）。"""
    tools = build_board_query_tools(context)
    _captured_report: List[str] = []
    context._simulator_report = _captured_report  # type: ignore

    def submit_report(report_text: str) -> str:
        """提交本月末奏章全文。盘面查清、奏章写完后调用。

        ══ 奏章结构 ══
        总标题：一句诗（七言或五言），切本月最痛之事。
        章节按"实际发生了什么"切，3-6 章。
        末两章固定：
          「陛下未知者」—— 1-3 条，无则写"无可隐之事"
          「待办未解」—— 只列 active_issues，每条一句状态短语

        ══ 笔法 ══
        汉末邸报体：有时序 / 有人 / 有地 / 有冷暖 / 留钩子。
        具体数字鼓励写：拨绢几万匹、调兵几千、流民几万、屠某族几人、
        谷价几钱、灾区几县、限期几日、奏疏几道。
        禁用游戏机制 token：bar、±N、N→N、「正向：重」「中度推进」。
        不写「激化/酝酿/阳阴违」抽象词，要写就写谁怎么拖
        （如"中常侍封诰留中，车骑将军府第有司不敢问"）。
        本朝文体：陛下、准奏、具题、留中、奉旨、是夜、漏二刻、翌日。
        汉官汉称：太尉、司徒、司空、尚书令、中常侍、城门校尉、虎贲中郎将。
        民生基调要诚实：盘面 public_support 低/loyalty 低时，写怨声载道。

        ══ 局势推进 ══
        新局势只两个来源：
          - candidate_events 里本月判定触发的——在章节写清来由
          - 玩家衣带诏明文强推的长期工程——档房自己识别
        一锤子事当月了结：拿人/罢官/族诛/下狱，本月写定局。

        ══ 讣闻 ══
        deaths_this_turn 里本月病逝的关键人物写派系动荡/官缺待补。
        不为讣闻新立局势。

        ══ 任官与顶替 ══
        诏书任命必须点名+写明新官职，在朝者写旧职→新职，
        新进者写所授官职。独占实职（太尉/三公/九卿/刺史/太守）任新人前，
        先查 get_active_ministers 有无现任者。

        ══ 末章固定 ══
        「人事除目」有人事变动时必列：
          任官：旧职→新职 or 起用姓名为官职
          去职：姓名+去职缘由（革/狱/流/卒/族诛）
        「待办未解」：只列 active_issues，每条一句状态短语。
        「建筑只叙事」：不代标数值、不代立新建筑。

        ══ 输出格式 ══
        《诗题》
        {建安/初平/兴平/...} {年} 年 {月} 月 月末奏章

        一、（章节名）
        （叙事段）

        N、人事除目
        任官：荀彧 由侍中 守 尚书令
        去职：周毖 罢职归乡

        N+1、待办未解
        1. #12 衣带密诏串联 — 车骑将军府密会已成
        2. #15 兖州蝗灾 — 赈粮未到，饥民结伙
        """
        _captured_report.append(report_text)
        return "__report_submitted__"

    return tools + [submit_report]
```

---

### 6.4 工具集 ④ — `build_extractor_tools`（**整个模块从 0 移植**）

```python
def build_extractor_tools(context: "CourtContext"):
    """档房书办工具集：13 工具（12 查询 + 1 submit_extraction）。"""
    tools = build_board_query_tools(context)
    _captured: List[str] = []
    context._extractor_result = _captured  # type: ignore

    def submit_extraction(json_str: str) -> str:
        """提交本月结算抽取结果（16 字段 JSON 字符串）。

        ══ 必须包含的 16 个顶层字段（无内容填 {} 或 []）══

        metric_delta        两量表增量 {"威权":N,"声望":N,"藩镇":N}（增量非新值）
        economy_moves       浮动收支列表，每项 {account(汉室库/内库),delta,category,reason}
                            单位万石/万缗/万匹；fixed_flows 已落账的不重复写
        faction_delta       派系满意度增量 {忠汉派:N, 务实派:N, 离心派:N, 叛逆派:N}
        class_delta         阶级满意度/影响力增量（@州 切片）
        region_delta        州数值变化 {sili: {字段:增量}}
        army_delta          军队数值变化 {caowei_army: {字段:增量}}
        power_updates       非己方势力 {caowei: {威望:N, 实力:N, 经济:N}}
        world_advance       外交态度 KV {曹魏:敌对, 东吴:摇摆, 袁术:倾汉}
        issue_advances      既有局势推进 [{issue_id, delta_bar, stage_text, narrative}]
        new_issues          本月新立局势（来源:decree 或 event_pool）
        cancels             撤销局势
        close_issues        结案/失败
        fiscal_changes      制度性财政系数 [{key, delta, reason}]
                            key 允许值: tax_land / tax_commercial / 盐税 / 军饷 / ...
        appointments        仅后宫纳妃 [{name, office, office_type:"后宫", reason, approved}]
        character_status_changes  大臣状态变更 [{name, status, reason}]
                                  status ∈ dismissed/imprisoned/exiled/retired/dead/offstage
        office_changes      朝臣官职变更 [{name, new_office, reason, new_office_type}]

        ══ 汉末档位判定标准 ══
        极端：族诛/官渡赤壁决定性战  bar±40~50  metric±20~30  faction±20~40
        重大：天子密旨+衣带诏串联     bar±20~35  metric±10~20  faction±10~20
        中等：单州平乱/单臣罢免        bar±8~15   metric±3~10   faction±3~10
        轻度：上疏留中/罚俸            bar±1~5    metric±1~3    faction±1~3

        威权严控：强势办成硬事才正向；旨意被拖/战败=-3~-12
        禁止双重计账：issue effect_on_resolve 已给过的不再给 metric_delta

        ══ 输出 JSON 骨架示例 ══
        {
          "metric_delta": {"威权": -3, "声望": 2},
          "economy_moves": [{"account":"汉室库","delta":-15,"category":"赈灾","reason":"兖州赈粮"}],
          "faction_delta": {"忠汉派": -5, "离心派": 4},
          "class_delta": {"农民@兖州": {"satisfaction": -6, "leverage": 5}},
          "region_delta": {"yanzhou": {"unrest": 5, "grain_security": -3}},
          "army_delta": {"caowei_army": {"morale": -3, "arrears": 5}},
          "power_updates": {"caowei": {"威望": -4, "实力": -3, "经济": -2}},
          "world_advance": {"曹魏": "敌对", "东吴": "摇摆", "袁术": "倾汉"},
          "issue_advances": [{"issue_id":12,"delta_bar":15,"stage_text":"车骑将军府密会已成","narrative":"..."}],
          "new_issues": [],
          "cancels": [],
          "close_issues": [{"issue_id":9,"reason":"resolved","narrative":"..."}],
          "fiscal_changes": [],
          "appointments": [],
          "character_status_changes": [{"name":"董卓","status":"dead","reason":"吕布所杀"}],
          "office_changes": [{"name":"荀彧","new_office":"尚书令","new_office_type":"九卿","reason":"侍中守尚书令"}]
        }
        """
        _captured.append(json_str)
        return "__extraction_submitted__"

    return tools + [submit_extraction]
```

---

### 6.5 工具集 ⑤ — `build_emperor_tools`（**汉末独家**）

```python
def build_emperor_tools(state: "GameState", context: "CourtContext"):
    """汉献帝天子专属工具集：7 工具（汉末独家，ming 无对应）。"""
    from han_sim.decree import issue_decree, cancel_decree  # 已有
    from han_sim.models import get_authority_level  # 已有

    def view_authority_level() -> str:
        """查当前威权等级（形同虚设/权臣操弄/阳奉阴违/诏书有效/号令四方/...）。"""
        lvl = get_authority_level(state.metrics.get("威权", 0))
        return (
            f"当前威权：{state.metrics.get('威权', 0)}，等级「{lvl.label}」。\n"
            f"诏书效力：×{lvl.decree_mult}；召对效果：×{lvl.summon_mult}。\n"
            f"诸侯稳定性加成：+{lvl.warlord_stability}；派系事件强度：×{lvl.faction_event_mod}。\n"
            f"可用恢复行动：{', '.join(lvl.recovery_actions)}。"
        )

    def activate_emperor_skill(skill_id: str) -> str:
        """激活天子技能（qm_01~qm_12 权谋系 / jx_01~jx_12 经略系 / ...）。"""
        from han_sim.models import can_activate_skill, get_skill_by_id
        skill = get_skill_by_id(skill_id)
        if not skill:
            return f"未知技能：{skill_id}"
        ok, reason = can_activate_skill(
            skill, state.metrics.get("威权", 0),
            state.metrics.get("activated_skills", []),
            state.metrics.get("skill_points", 0),
        )
        if not ok:
            return f"无法激活「{skill.name}」：{reason}"
        state.metrics.setdefault("activated_skills", []).append(skill_id)
        state.metrics["skill_points"] = state.metrics.get("skill_points", 0) - skill.unlock_level
        return f"✅ 已激活「{skill.name}」：{skill.effect}"

    def issue_royal_decree(decree_type: str, title: str, content: str, target: str = "") -> str:
        """颁诏（衣带密诏/讨伐/迁都/嘉奖/罪己/大赦/自由）。"""
        result = issue_decree(state, decree_type, title, content, target)
        return result.get("narrative", f"❌ 颁诏失败：{result}")

    def cancel_royal_decree(decree_id: str) -> str:
        """撤诏（仅 draft/issued 且 can_cancel=True）。"""
        result = cancel_decree(state, decree_id)
        return result.get("narrative", f"❌ 撤诏失败：{result}")

    def forge_alliance(power_a: str, power_b: str, terms: str = "") -> str:
        """天子撮合两势力结盟（如联吴抗曹、联刘抗曹）。需消耗威望+10。"""
        if state.metrics.get("威权", 0) < 50:
            return "撮合结盟失败：威权不足（需≥50）。"
        state.metrics["声望"] = state.metrics.get("声望", 0) + 10
        return (
            f"✅ 天子降诏，撮合{power_a}与{power_b}结盟。\n"
            f"条件：{terms or '共抗强敌'}。声望+10。"
        )

    def sow_dissent(target_power: str, minister_name: str) -> str:
        """离间（反间计）：指定某势力某臣，使其忠诚度-15（消耗 30 技能点）。"""
        sp = state.metrics.get("skill_points", 0)
        if sp < 30:
            return f"离间失败：技能点不足（需 30，当前 {sp}）。"
        state.metrics["skill_points"] = sp - 30
        context.db.modify_minister_affection(minister_name, -15, reason=f"反间计（{target_power}）")
        return f"✅ 反间计已下：{target_power}·{minister_name} 忠诚-15。"

    def propose_empress(name: str, office: str, office_type: str = "后宫", reason: str = "") -> str:
        """纳妃/册封（仅后宫用，朝臣走 office_changes）。"""
        if office_type != "后宫":
            return "纳妃失败：office_type 必须为「后宫」。"
        return (
            f"__pending_appointment__{json.dumps({
                'name': name, 'office': office, 'office_type': '后宫',
                'faction': '后宫', 'reason': reason, 'replaces': ''
            }, ensure_ascii=False)}"
        )

    return [
        view_authority_level, activate_emperor_skill,
        issue_royal_decree, cancel_royal_decree,
        forge_alliance, sow_dissent, propose_empress,
    ]
```

---

## 7. 风险与回退

| 风险 | 影响 | 缓解 |
|---|---|---|
| han 缺 `factions`/`classes`/`buildings` 完整字段 | `faction_report`/`buildings_report` 返回空 | 阶段 A 阶段 B 分开做；阶段 A 函数先就位，缺字段打"暂无" |
| LLM 误把"万两"写出 | 奏章出戏 | `submit_report` docstring 明示用"万石/万缗/万匹"；examples 锁定 |
| 衣带诏密令系统过强，破坏"被曹操控制"的历史感 | 玩法失衡 | 设定 `MIN_AUTHORITY_FOR_SECRET = 30`；威权<30 时 `issue_secret_order` 返回"衣带诏下发失败：圣躬不保" |
| 19 工具一次性全注入 LLM | token 成本↑、误用↑ | 模仿 ming 的 `available_skill_ids` 条件注入；按 `office_type` 限制 |
| 现有 han 代码与 ming API 签名不同 | 复制 ming 代码不能直接跑 | 所有 `character.office_type` 改为 `character.get("office_type")`；`context.db.conn` 用法保持一致 |
| agents.py 已有逻辑与新工具冲突 | 重复定义 | 把 5 个 build 函数放 `tools.py` 末尾，agents.py 仅 `from han_sim.tools import build_minister_tools` |

---

## 8. 验收标准

| # | 验收项 | 怎么测 |
|---|---|---|
| 1 | 28 个大臣工具全部可调用 | `pytest tests/test_minister_tools_all.py`（28 个 test） |
| 2 | 王允/曹操/董卓/刘备/袁绍/汉献帝 6 个 person 测试用例都通 | `pytest tests/test_minister_dialogue.py` |
| 3 | 13 个 board_query 工具无写操作 | 静态扫描：函数体内不能有 INSERT/UPDATE/DELETE |
| 4 | submit_report docstring 全文含汉官汉称 | `grep -E '太尉|司徒|司空|尚书令|中常侍' tools.py` 命中 ≥20 |
| 5 | submit_extraction docstring 含 16 字段名 | `grep -E 'metric_delta|faction_delta|new_issues|...' tools.py` 命中 16 |
| 6 | 5 个 build 函数签名稳定 | `pytest tests/test_build_signatures.py` |
| 7 | 现有 5 角色对话跑 3 回合无错 | `pytest tests/test_full_loop.py -v` |
| 8 | 文件行数从 554 增到 1300-1500 | `wc -l han_sim/tools.py` |
| 9 | 与 ming 的同名函数同构（签名/返回类型/工具数） | 对照表（见 §3） |

---

## 9. 总结

**移植目标**：把 ming/tools.py 1052 行的成熟体系，按汉末语境改造为 5 个 build 函数（其中 `build_emperor_tools` 为汉末独家），覆盖 28+13+13+7=61 个工具，从 2.2 万字节扩到 ~5 万字节。

**汉末独家亮点**：
1. **5 个 build 函数**（ming 只有 4 个）：新增 `build_emperor_tools` 给汉献帝天子视角用；
2. **衣带密诏系统**：完全替代明的厂卫密查，对接 `DECREE_TYPES.衣带密诏`；
3. **汉官汉称**：太尉/司徒/司空/九卿/尚书令/中常侍/城门校尉；
4. **历史锚点**：6 个核心人物（王允/曹操/董卓/刘备/袁绍/汉献帝）全部在 `characters.json` 已有，可直接用；
5. **汉末邸报体**奏章规范（`submit_report` docstring）：用"漏二刻/翌日/中常侍封诰留中"等汉词。

**预计工时**：阶段 0-2 共 4 天（保底），阶段 3-5 共 3 天，阶段 6 共 1 天，**总计 8 天**（1 人）。

**风险最大点**：把 ming 的字段名直接复制（"两京十三省/辽东"等）会立刻露馅；必须**在 `submit_report` 和 `submit_extraction` 的 docstring 锁死汉化称谓**，让 LLM 看到的 prompt 里就全是"汉官汉称"。

---

*方案完成于 2026-06-01，奉天子命，呈御览。*

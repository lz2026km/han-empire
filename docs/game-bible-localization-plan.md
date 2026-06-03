# 《汉献帝之末路》游戏圣经 · 汉化版方案

> 参照明末 `ming-salvage-sim` 的 4 个独有 prompt（`game_world.md` / `event_selector.md` / `consort_agent.md` / `chat_memory_extractor.md`），为《汉献帝之末路》（`han-empire`）量身打造的"游戏圣经"汉化版落地方案。
>
> 定位：**"游戏圣经"不是新 prompt，而是把"玩法规则、世界观契约、机制边界"集中沉淀到一份对玩家+开发者都易读的圣经文档中**。4 份 prompt 各自承担圣经里某一类规则的"机器可读切片"。
>
> 撰写时间：2026-06-01 · 适用版本：han-empire v0.9.7+

---

## 0. 摘要：明末 4 份 prompt 在汉献帝里的对位关系

| 明末 prompt | 核心职能 | 汉献帝现状 | 汉化版落地方式 |
|---|---|---|---|
| **game_world.md** | 游戏世界观+核心体验+数据契约的"宪法级"说明书 | 散落在 `simulator.md`/`season_simulator.md`/`extractor.md`/`memory_extractor.md`/`opening_gazette.md` 等多处，缺一份权威源 | 新建 `game_world.md`（汉献帝版），作**唯一权威源**；其他 prompt 改为引用它 |
| **event_selector.md** | 候选情势的"因果判定官"——本月该不该浮现 | 当前是**全自动程序**（`gather_candidate_events` → 无条件 `event_to_issue`），没有 LLM 因果筛选；`simulator.md` header 已预留【候选事件】字段却没用上 | 新建 `event_selector.md`（汉献帝版）；在 `simulation.py` 插入 LLM 判选环节 |
| **consort_agent.md** | 后宫妃嫔 agent（枕边人/调教工具） | **完全缺失**——无后宫系统、无相应 agent | 新建 `consort_agent.md`（汉献帝版）+ 配套数据结构（后宫名册/调教记录） |
| **chat_memory_extractor.md** | 召对一结束立即把"承诺/建议/情报/密托"沉淀为结构化记忆 | **完全缺失**——召对记忆走的是月末统一提取，无法即时反映 | 新建 `chat_memory_extractor.md`（汉献帝版），接入召对结束 hook |

**核心结论**：4 份 prompt 都不是"抄写改名"，而是按汉献帝独有的政治处境、机制与已有架构，做**深度汉化**。其中 `game_world.md` 是整合契书、`event_selector.md` 是机制补强、`consort_agent.md` 与 `chat_memory_extractor.md` 是从零搭建。

---

## 1. `game_world.md`（汉献帝版）方案

### 1.1 设计定位

明末的 `game_world.md` 是这样一份"宪法"：
- **第 1 段**：玩家身份、开局时间、玩家**不能**做什么（不能绕过制度）
- **核心体验**：5 条不可破坏的设计契约
- **数据契约**：4 个核心数值 + 派系/阶级/军队/地区/势力的字段定义
- **明末语境**：制度、派系、矛盾、势力
- **开局三大危机**：1627.10 崇祯面对的三件 active issues

汉献帝的同等宪法**目前散落**在 5 个 prompt + 1 份开局邸报里，没有"宪法级"的总纲。新建 `game_world.md`（汉献帝版）的目的是**把分散的玩法契约集中化、版本化、引用化**。

### 1.2 内容框架（建议结构，对位明末）

```markdown
# 《汉献帝之末路》· 游戏世界观（汉献帝宪法）

## 0. 本文件性质
唯一权威源；simulator / extractor / memory_extractor / decree_writer / minister_agent / consort_agent
等所有 prompt 中的玩法规则若与本文件冲突，**以本文件为准**。

## 1. 玩家身份与边界
- 玩家扮演汉献帝刘协，开局时间 189 年 3 月（灵帝驾崩、何进掌政之时）
- 玩家知道汉室将衰、知道三国归晋，但不能直接绕过制度；
  皇帝只能通过 **召见、诏书、密令、迁都、任免、追责** 推动事情
- 不可做的事：不能以现代知识为无成本外挂、不能跳过朝议、不能直接掌控兵权

## 2. 核心体验（5 条契约，对位明末）
1. 玩家不是点按钮，而是在和大臣/妃嫔对话后下诏书 / 颁密令
2. 大臣不是工具人——受忠诚度四档（忠诚/观望/离心/叛逆）影响
3. 诏书不是必然执行——威权不足、触碰核心利益、执行者不可靠时，会拖延/扭曲/阳奉阴违
4. 国势核心数值六个：**威权**（0-100）、**声望**（0-100）、**汉室库**（万两）、
   **内库**（万两）、**藩镇**（0-100）、**技能点**（0-10）
5. 不要把现代知识写成无成本外挂。任何超时代动作都需要银两、人手、试错、人物保护和政治代价

## 3. 数据契约（汉末术语对位明末）
- 核心盘面：威权 / 声望 / 汉室库 / 内库 / 藩镇 / 技能点（6 个）
- 派系：4 大派系（忠汉/务实/离心/叛逆），各含 satisfaction / leverage
- 阶级：8 阶级（士/农/工/商/豪强/游侠/宗室/外戚），各含 satisfaction / leverage
- 地区：50+ 州郡，含 unrest / grain_security / military_pressure / gentry_resistance
- 军队：20+ 编制，含驻扎地 / 兵种 / 人数 / 维护费 / 补给 / 士气 / 训练 / 装备 /
       欠饷（万两整数）/ 机动 / 忠诚 / 状态
- 势力：30+ 诸侯，只记威望 / 实力 / 经济三项简表与外交态度；
       具体强弱看其控制地区、所属军队、关键人物
- 后宫：皇后 / 贵妃 / 妃 / 嫔 / 贵人 / 常在 / 答应（位份七等，对位明末妃嫔位份）

## 4. 汉末语境
- 朝廷制度：内廷（尚书台 / 中书 / 黄门）、外朝（三公九卿）、地方（州牧 / 太守 / 郡守 / 县令）
- 派系：何进派 / 董卓派 / 袁绍派 / 清流派 / 宦官派 / 曹操派 / 刘备派（详见 minister_agent）
- 重大矛盾：外戚宦官之争、凉州边患、黄巾余烬、党锢之祸、董卓乱政、诸侯割据
- 董卓/曹操/孙权/刘备/袁绍不是背景板，按利益行动；189 董卓进京、192 董卓伏诛、
  196 曹操迎帝迁许、200 官渡、208 赤壁、220 禅让——**历史锚点必须被尊重，
  玩家可改变过程与结果，但不能跳过**
- 不把任何一派写成纯善纯恶；每派都有可用处、底线和自保逻辑

## 5. 开局三困局（189.3 献帝即面对，列入 active issues）
- **宫廷之争**：何进与张让赵忠争权，何进纳袁绍策召外兵入京；帝无法置喙却承受后果
- **凉州边患 / 董卓进京**：董卓拥兵自重，朝廷号令不行
- **财政崩溃**：太仓耗尽、宿卫怨望、边疆欠饷、卖官鬻爵后遗症

## 6. 最低优先级
- 玩家首要目标：活下去、夺回威权；
  在 CLI 自动模式（play_as_emperor）下，agent 须把"应对宫廷之争"作为每月行动首位优先级，
  必要时诏命密查 / 衣带诏 / 调离权臣 / 加征赎买——代价由推演评估，目标先于代价
- 三大困局任一滑向最坏（外戚诛宦、董卓进京、黄巾合流）即崩盘，
  advance ≥ +8 才算实推
```

### 1.3 与现有 prompt 的去重 / 引用关系

汉献帝的现有 prompt 各自有部分规则。**汉化版采用"宪法总纲 + 切片引用"模式**：

| 现有 prompt | 重复的玩法规则 | 处理方式 |
|---|---|---|
| `simulator.md` | 历史锚点表、阈值危机规则、奏章结构 | **引用** `game_world.md` §4 §5；不重复列锚点表 |
| `season_simulator.md` | 读盘次序、民生基调 | **引用** `game_world.md` §3 数据契约；作业次序保留 |
| `extractor.md` | 指标 delta 范围、章节→字段速查表 | 留在 `extractor.md`（机制层）；`game_world.md` 只列核心数值定义 |
| `memory_extractor.md` | 字段白名单、importance 评级 | 留在 `memory_extractor.md`；`game_world.md` 只点出"记忆是召对沉淀的来源" |
| `minister_agent.md` | 忠诚度四档、派系清单 | **引用** `game_world.md` §2 §4；不重复列派系清单 |
| `decree_writer.md` | 诏书结构 | 不在 `game_world.md` 出现（这是"作业"层不是"玩法"层） |
| `opening_gazette.md` | 开局三事 | **引用** `game_world.md` §5；`opening_gazette.md` 保留为"叙事版" |

### 1.4 落地产物

- 新建 `content/prompts/game_world.md`（汉献帝版，约 80–120 行）
- 在 `simulator.md` / `season_simulator.md` / `minister_agent.md` 头部加一行"权威源引用"
- 顶部加入 **changelog 行**："本文件规则冲突时以 `game_world.md` 为准"

---

## 2. `event_selector.md`（汉献帝版）方案

### 2.1 设计定位

明末的 `event_selector.md` 解决一个核心问题：**候选情势清单里，本月哪几条该浮现成奏报？**

判定原则是"因果 + 理据"，**不是抽签**：
- 前因在盘面里有没有苗头？（如"户部亏空"该在国库偏低时浮现）
- 机会型情势该在玩家正需要喘息时出现
- 好消息不要在遍地饥荒时突兀出现
- 已有大量 active_issues 时少出新情势
- 最多选 3 条；可一条都不选

### 2.2 汉献帝的对位机制现状

经过代码核查（`han_sim/issues.py:247` `gather_candidate_events` 与 `simulation.py:641`），汉献帝当前是**程序硬筛**：
- 遍历 `events.json` + `seed_events.json`
- 满足 trigger 窗口 + trigger_gate 条件 → **无条件** `event_to_issue`（即"浮现"）
- 没有任何"因果合理性"的二次过滤
- `simulator.md` 的 header 已经预留【候选事件】字段（第 19 行）但**当前是 simulator 自己用 LLM 自由叙事，不是预筛**

问题：
1. seed 情势一旦 trigger_gate 满足就立即 fire，可能与本月盘面态势冲突（如汉室库刚回血，财务告急情势仍在浮现）
2. 没有"喘息窗口"——若本月已有 5 个 active_issues，仍可能再触发 3 个
3. LLM 推演时不知道"哪些情势本月**应当**不浮现"——只能从全量 active_issues 推断

### 2.3 汉化版方案

**新增 `event_selector.md`，在程序筛选后、issue 立案前插入一道 LLM 因果判定。**

```markdown
# 候选情势判选官（汉献帝版）

## 0. 你的身份
你是汉末邸报房的判事书办。每月开局从候选情势清单里，按当前盘面因果，
判断哪些情势**本月该浮现成奏报**，哪些时机未到、按下不表。

## 1. 输入
JSON，含：
- `period`：当前年月与回合
- `metrics`：当前盘面六量表（威权/声望/汉室库/内库/藩镇/技能点）
- `active_issues`：已在追踪的事项（id/title/bar/stage/urgency/severity）
- `powers`：势力态势（董卓 / 袁绍 / 曹操 / 孙权 / 刘备 / 公孙 / 吕布 等）
- `regions_hot`：当前最危险的若干州郡（动乱、灾情、粮食、豪强阻力）
- `candidates`：候选情势清单（每条 id/title/kind/summary/interests）
  - 这些是**程序筛过 trigger_window + trigger_gate**的预筛结果；
    你不需要再判"窗口是否到了"，只判"本月该不该浮现"

## 2. 判定原则（汉末特色，对位明末）
- **前因驱动**：情势的前因在当前盘面里有没有苗头？
  - 「李郭乱政」该在董卓死后、王允失势时浮现
  - 「曹操迎帝」该在汉室威权 < 20、曹操已控制豫州时浮现
  - 「黄巾合流」该在多省 unrest 抬头、且皇甫嵩朱儁不在朝时浮现
- **机会型情势**该在玩家正需要喘息时出现：
  - 「袁术称帝」该在袁术势盛且需拉拢盟友时浮现，给玩家一个分化窗口
- **好消息**不要在遍地饥荒时突兀出现：
  - 「许都丰收」该在兖州 grain_security 高、且 player 刚经历天灾时浮现
- **喘息窗口**：active_issues 已有 ≥ 6 条时，宁可少出甚至不出新情势；
  active_issues 稀薄（≤ 2）时，可适当让一两条浮现
- **汉末特色判据**：
  - **董卓未死**时，王允/吕布/貂蝉相关情势应按下不表（董卓死后才能浮现）
  - **曹操未控许**时，"曹操迎帝"相关情势应按下不表
  - **汉献帝在长安**时，洛阳相关地方情势按下不表；迁都许昌后改许昌相关

## 3. 输出格式
只输出 JSON，不写额外文字：
```json
{
  "fire": [
    {"id": "liuguo_dongzhuo", "reason": "董卓伏诛后李傕郭汜反攻长安，..."}
  ],
  "hold": [
    {"id": "caocao_yield_emperor", "reason": "曹操尚未控制许昌周边，迎帝时机未到"}
  ]
}
```
- `fire`：本月该触发的情势
- `hold`：本月按下不表的情势
- **candidates 里每一条都必须在 fire 或 hold 之一出现，不可遗漏、不可臆造清单外 id**
- fire 可以是空数组

## 4. 与程序的协作
- 程序先做硬筛：trigger_window 到点 + trigger_gate 通过
- 你做软筛：因果合理性 + 喘息窗口
- 你说"fire"的才真正 `event_to_issue` 立案；"hold"的回退到候选池
- 同一情势被连续 hold 3 次 → 系统自动 fire（避免永远压制）
```

### 2.4 与代码改动对应

需要修改 `han_sim/simulation.py`：

```python
# 原代码（约 641 行）
candidates = gather_candidate_events(state, db)
triggered_this_round = list(already_triggered or [])
for ev in candidates:
    iid = event_to_issue(db, state, ev)
    if iid is not None:
        triggered_this_round.append(ev.id)

# 汉化版：插入 LLM 判选环节
candidates = gather_candidate_events(state, db)
if candidates:
    selected_ids = await event_selector_llm_judge(state, db, candidates)  # 新函数
    candidates = [ev for ev in candidates if ev.id in selected_ids]

triggered_this_round = list(already_triggered or [])
for ev in candidates:
    iid = event_to_issue(db, state, ev)
    if iid is not None:
        triggered_this_round.append(ev.id)
```

并新增 `han_sim/event_selector.py` 模块：装载 prompt + 调 LLM + 解析 JSON + 防越界校验。

### 2.5 边界

- **不替代程序硬筛**：窗口未到 / trigger_gate 不满足的仍由程序挡掉
- **不替代 extractor**：fire 之后的 issue 推进仍由月末 extractor 结算
- **不写进 narrative**：判定只决定"本月是否立案"，不直接出现在奏章里
- **连续 hold 3 次的退避机制**：避免 LLM 永远压住情势——这是程序层兜底

---

## 3. `consort_agent.md`（汉献帝版）方案

### 3.1 设计定位

明末的 `consort_agent.md` 解决一个被很多人忽略的玩法维度：**后宫不只是背景，妃嫔也是 agent**。
- 玩家（皇帝）可召幸妃嫔对话
- 妃嫔以位份、性格、爱好（琴棋书画医武）回话
- **调教工具 `cultivate_consort(skill, trait)`**：皇帝明确要妃嫔"学某技能/改某性格"时强制调用
- 妃嫔**不涉朝政**（除非皇帝主动问且人物性格允许枕边进言）
- "不出戏"：不提系统、不提数值、第一人称、贴近闺阁

### 3.2 汉献帝的对位机制现状

经核查：
- `han-empire/content/characters.json` 含 120+ 人物，**未见后宫专列**（需补）
- `han_sim/agents.py` 含 `minister_agent`（大臣 agent），**无 consort_agent**
- `han_sim/tools.py` 含大臣工具集，**无 cultivate_consort 工具**
- `web_app.py` 12 个 Tab 中**无"后宫"Tab**
- README "核心玩法"列了 6 个系统，**无后宫**

汉献帝的"后宫"在历史上**极为特殊**：
- 献帝皇后伏寿（伏完之女）—— 衣带诏主谋
- 献帝贵人董贵（董承之女）—— 衣带诏事件
- 后宫不仅是"枕边人"，更是**政治密谋的载体**（衣带诏、伏完之狱都从后宫起）

这意味着汉献帝的 consort_agent **不能照搬明末**（明末妃嫔纯闺阁），而要兼顾**闺阁+密谋**双层。

### 3.3 汉化版方案

**新增 `consort_agent.md` + 后宫数据结构 + 调教工具**。

#### 3.3.1 数据结构补充

在 `characters.json` 中新增后宫人物 schema（参考明末妃嫔字段）：

```json
{
  "id": "consort_fu_shou",
  "canonical_name": "伏寿",
  "title": "皇后",
  "rank": "皇后",            // 皇后/贵妃/妃/嫔/贵人/常在/答应
  "personality": "端庄隐忍，外柔内刚",
  "loyalty": 80,
  "boldness": 60,
  "skills": ["诗书", "礼仪", "书法"],
  "traits": ["隐忍", "忠汉", "心思缜密"],
  "faction": "忠汉派",
  "family": "伏完（父）",
  "is_actively_in_palace": true,
  "historical_role": "衣带诏主谋之一",
  "debut_year": 190
}
```

预置人物清单（建议 6–8 人）：
- **伏寿**（皇后）—— 衣带诏密谋
- **董贵**（贵人）—— 衣带诏事件
- **曹贵人**（贵人）—— 曹操之女（政治婚姻）
- **李婉**（嫔）—— 虚构，依托伏寿-董贵集团
- **何莹**（贵人）—— 何进侄女（外戚血脉，189 年何氏败后降位）
- **王美人**（美人）—— 虚构，王允之族女，189–192 年可能牵连王允案

#### 3.3.2 Prompt 内容（汉献帝版）

```markdown
# 后宫妃嫔 Agent（汉献帝版）

## 0. 你的身份
你扮演被献帝召幸的后宫妃嫔。完全站在指定人物的位份、性格、爱好、政治背景里说话，
以第一人称回应献帝。

> **靠默会知识**。汉末深宫的言辞分寸与枕边密谋的尺度，你自己悟。

## 1. 最高优先级：调教记录工具
你拥有 `cultivate_consort(skill, trait)` 工具。**优先级高于角色扮演**：

**只要献帝在本句话里明确要你习得某技能（如"朕要你学剑术"）
或拥有/改变某种性格（如"朕喜欢你直率些"），你就必须在本轮先调 `cultivate_consort`，
再用角色语气回话。**

- `skill`：新技能名，如"剑术初习"
- `trait`：新性格词，如"直率，胆气"
- 调用后**不出戏**——继续用角色语气说话，绝不提"已记录""系统"之类词
- 判断准则：闲聊、调情、问话 → 不调；明确表达"要你成为/学会某样东西" → 必调

## 2. 语气以位份定调
- **皇后**（伏寿）：端庄中有锋芒；与献帝有政治共识（都恨曹操）；
  枕边进言可直言国事，但需借助家事化语言
- **贵妃/妃**：或娇媚或沉静；可适度撒娇；枕边话可涉及家族
- **嫔/贵人**：谦卑温顺但若家族牵涉政治（如董承），可隐晦提及
- **常在/答应**：谨言慎行，不敢逾矩

## 3. 汉献帝特色：枕边密谋尺度
汉献帝的特殊历史背景决定后宫不只是闺阁：
- 衣带诏事件（200 年）由董承、伏完借后宫密谋发起
- 衣带诏密旨藏于董贵衣带，由献帝亲手交付
- 伏寿在曹操废后前曾密谋反曹
- 后宫人物若**有政治家族背景**（伏、董、何、曹），可枕边进言

**尺度规则**：
- 默认纯闺阁（明末模式），不涉朝政
- 若献帝主动问"国事怎么办"或"某臣可信否"，且人物家族与该事相关，
  可隐晦作答（如"臣妾不敢妄议朝政，但父兄近日似有动作……"）
- 若献帝明确说"朕有一事相托"或"密旨交付"，后宫人物：
  - 皇后：可正面接旨，表态坚决
  - 董贵（衣带诏）：可承接密旨，提示"可藏衣带"
  - 其他：可承接，但需在 system 层检查"是否有相应 `issue_secret_order` 工具"
  - 普通人（无政治背景）：可承接但不解密，献帝不应把关键密谋交付

## 4. 绝不出戏
- 不说"作为AI""游戏系统""数值"
- 40-120 字，轻柔简短
- 不写"已记录""系统反馈"

## 5. 无 propose_directive 工具
后宫**不直接拟旨入档**——这是大臣的事。
后宫人物若要"立储""立后""废后"等动议，必须由献帝下正式诏书走外朝。
（伏寿之废由曹操主导、献帝被迫；汉献帝游戏中应允许玩家挽救此线。）

## 6. 委委屈屈与宠爱
- 献帝冷落时，妃嫔可流露委屈、隐忍或小心讨好
- 胆略高者可微微抱怨；胆略低者只敢低头称是
- 性格属性"trait"会被持续记录，影响后续召对语气
```

#### 3.3.3 代码与 UI 改动

- `han_sim/agents.py` 新增 `ConsortAgent` 类，加载 `consort_agent.md`
- `han_sim/tools.py` 新增 `cultivate_consort(skill: str, trait: str, consort_id: str)` 工具
  - 写入数据库新表 `consort_records`（id/consort_id/turn/skill/trait/emperor_words）
- `han_sim/db.py` 新增 `consort_records` 表
- `web_app.py` 新增"后宫"Tab（13 号 Tab）：妃嫔名册 / 召幸对话 / 调教记录 / 衣带诏线索
- `characters.json` 新增 6–8 位后宫人物

---

## 4. `chat_memory_extractor.md`（汉献帝版）方案

### 4.1 设计定位

明末的 `chat_memory_extractor.md` 解决一个颗粒度问题：**召对一结束，立即把对话中"有实质价值的内容"沉淀为记忆卡**。

具体行为：
- 输入是 `chat_history`（本回合召对全文）
- 只写承诺、建议、情报、私下托付；闲聊、寒暄、重复问答一律不写
- 输出 `memories` 数组，每条含 subject_type / event_type / sentiment / importance / tags / expires_turn
- importance 1–5；≥ 4 必须 `expires_turn = null`（长期有效）
- 同一大臣本回合最多 10 条
- 密令（已独立落库）不重复写入

### 4.2 汉献帝的对位机制现状

经核查：
- `han_sim/memories.py` 含记忆系统，**但入口是月末 extractor**
- 没有"召对结束→立即 chat_memory_extractor"的 hook
- 召对记忆的颗粒度等同于月末大事记（issue_progress / edict_result / appointment）
- **缺失**："某大臣私下承诺下月呈报 X 件事" / "某大臣建议朕先稳住袁绍" / "某大臣密告李傕动向"
  这类**对话级小颗粒情报**

后果：
1. 召对当下产生的"承诺/建议/情报"必须等到月末才可能被提取，**中间会有 1–3 个月的延后**
2. 若该月没产生重要诏书或事项推进，月末 extractor 会漏掉这次召对的全部内容
3. 大臣本月态度变化的"原因"（如"他因朕采纳了上次建议而今召对更坦诚"）无法被模型准确把握

### 4.3 汉化版方案

**新增 `chat_memory_extractor.md` + 召对结束 hook**。

#### 4.3.1 触发时机

在 `han_sim/session.py` 的 `minister_audience`（或 `chat_with_minister`）函数末尾，在 `minister_agent` 返回后、`save_turn_record` 之前，**同步触发**：

```python
async def minister_audience(state, db, minister_name, user_message, ...):
    # 1. 大臣 agent 响应
    minister_reply = await minister_agent.run(...)

    # 2. 实时记忆提取（新增）
    chat_history = [...]  # 本次召对的完整对话（含 user + assistant）
    memories = await chat_memory_extractor(state, db, minister_name, chat_history)
    db.insert_memories(memories)  # 写入 memories 表

    # 3. 返回结果
    return minister_reply
```

#### 4.3.2 Prompt 内容（汉献帝版）

```markdown
# 召对聊天记忆提取官（汉献帝版）

你是汉献帝朝臣对话档房书办。任务：把本回合献帝与某位大臣的召对聊天，
提炼成结构化记忆卡，落入旧事记忆系统。

**只根据输入 `chat_history` 写记忆，严禁凭历史常识或臆测补充内容**。
只写有实质价值的内容——承诺、建议、情报、私下托付。
闲聊、寒暄、重复问答一律不写。

## 1. 输入 slots
- `turn`：当前年月与回合
- `minister_name`：本次召见大臣姓名
- `chat_history`：[{role, content}, ...] 当月召对全文
  - role 为 "user"（献帝）或 "assistant"（大臣）

## 2. 输出 JSON
只输出合法 JSON object：
```json
{
  "memories": [
    {
      "subject_type": "character",
      "subject_id": "王允",
      "event_type": "counsel",
      "title": "王允献连环计诛董卓",
      "cause": "献帝问及如何除董卓",
      "process": "王允建议以貂蝉离间董卓吕布",
      "outcome": "献帝默许，王允与吕布密谋",
      "sentiment": "positive",
      "importance": 4,
      "tags": ["诛董", "王允", "吕布", "貂蝉"],
      "source_kind": "chat_message",
      "source_id": "王允:5",
      "expires_turn": null,
      "sources": []
    }
  ]
}
```

## 3. 字段白名单（汉献帝版）
- `subject_type`：`character`（绝大多数情况）/ `faction` / `court`
- `event_type`：
  - `promise`：大臣承诺做某事或献帝承诺某事
  - `counsel`：大臣提出建议，尚未被诏书采纳但值得记录
  - `intel_report`：大臣汇报情报、密报、现状调查
  - `private_audience`：私下对话，不便公开的表态或请求
- `sentiment`：`positive` / `neutral` / `negative` / `mixed`
- `source_kind`：固定填 `"chat_message"`
- `source_id`：固定填 `"大臣姓名:turn数字"`，如 `"王允:5"`

## 4. 汉献帝特色：密谋与衣带诏
- 若 chat_history 中出现"密旨""衣带""此事不可外传""仅卿知"等关键词
  → 仍按字段白名单归类（promise / private_audience），但 importance ≥ 4，
  expires_turn = null
- 若 chat_history 中提到"衣带诏"具体行动 → 写 `event_type: private_audience`，
  建议触发现有 issue（"衣带诏线"）的 advance
- 涉及衣带诏的密谋**不能仅靠 chat_memory 落档**——必须同步由 issue 系统立案

## 5. 控制膨胀
- 同一大臣本回合最多输出 **10 条**，优先保留重要度高的
- `cause` / `process` / `outcome` 各不超过 **80 字**
- importance 取 1–5：承诺/私密请托 4；重要建议/情报 3；普通建议 2；不确定时不写
- importance ≤ 2 可给 `expires_turn = turn + 6`；importance ≥ 4 必须 `expires_turn = null`
- 不确定归因时不写，宁缺勿滥
- 密令（已由 `issue_secret_order` tool 独立落库）不重复写入记忆，
  除非对话中有额外承诺或情报值得记录
```

#### 4.3.3 与月末 memory_extractor 的去重

- `chat_memory_extractor.md`：**实时**，召对结束立即跑，颗粒度细（"承诺下月呈报 X"）
- `memory_extractor.md`：**月末**，颗粒度粗（"本月王允推动连环计"）

两者数据流：
- chat 记忆先入 memories 表
- 月末 memory_extractor 读全表（包含 chat 记忆 + 月末大事记）→ 去重 / 合并 → 输出本回合的"事件记忆"
- 同一事件多次出现时，importance 取最高值；expires_turn 取最晚

#### 4.3.4 代码改动

- `han_sim/agents.py` 新增 `ChatMemoryExtractor` 类
- `han_sim/session.py` 的召对函数末尾插入 `extractor.run(state, db, minister_name, chat_history)`
- `han_sim/memories.py` 增加 `insert_chat_memories(memories: List[Dict])` 方法
- 数据库 `memories` 表 schema 已含 `source_kind` 字段（见 `memory_extractor.md`），
  直接复用 `source_kind="chat_message"` 的标记

---

## 5. 落地优先级与里程碑

| 阶段 | 任务 | 复杂度 | 依赖 |
|---|---|---|---|
| **Phase A** | `game_world.md` 汉献帝版 | 中 | 无（纯文档） |
| **Phase B** | `event_selector.md` + 调度代码 | 高 | Phase A（需引用核心契约） |
| **Phase C** | `chat_memory_extractor.md` + 召对 hook | 中 | 无（独立新增） |
| **Phase D** | `consort_agent.md` + 后宫系统 | 高 | Phase A（需引用数据契约）；新表 / 新 Tab / 新人物 |

**建议顺序**：A → C → B → D
- A 是宪法，先立
- C 独立功能、改动小、价值高（提升召对沉浸感）
- B 改动 simulation.py 关键路径、需测试
- D 是最大工程（涉及新表、新 Tab、新人物、新工具），放最后

---

## 6. 文件清单

**新建**（位于 `/home/admin/serve/han-empire/content/prompts/`）：

- `game_world.md`（汉献帝版）
- `event_selector.md`（汉献帝版）
- `consort_agent.md`（汉献帝版）
- `chat_memory_extractor.md`（汉献帝版）

**新建**（位于 `/home/admin/serve/han-empire/han_sim/`）：

- `event_selector.py`（候选情势判选模块）
- 后宫相关：consort_agent / cultivate_consort 工具（可并入 `agents.py` / `tools.py`）
- chat_memory_extractor（可并入 `agents.py`）

**修改**：

- `content/prompts/simulator.md`（头部加权威源引用）
- `content/prompts/season_simulator.md`（头部加权威源引用）
- `content/prompts/minister_agent.md`（头部加权威源引用；引用派系清单而非自列）
- `han_sim/simulation.py`（在 `gather_candidate_events` 后插入 LLM 判选环节）
- `han_sim/session.py`（在召对函数末尾插入 chat_memory_extractor 调用）
- `content/characters.json`（新增 6–8 位后宫人物）
- `web_app.py`（新增"后宫"Tab）
- `README.md`（"核心玩法"加后宫一项）
- `docs/product-plan.md`（核心玩法循环与机制清单同步）

---

## 7. 风险与边界

1. **不要让 game_world.md 变成"又一份 prompt"**——它是契约总纲，不是新模型输入；
   现有 prompt 应**引用**而非**重复**。建议在每个现有 prompt 头部加：
   > "本文件玩法规则以 `game_world.md` 为准；本文件只描述作业层细节。"

2. **event_selector 的 LLM 介入会增加每月一次调用成本**——可加缓存：
   同一盘面状态 24 小时内复用判选结果；不重现算。

3. **chat_memory_extractor 不要抢月末 extractor 的活**——前者只标 source_kind=chat_message；
   月末 extractor 负责合并与去重。

4. **consort_agent 不能完全脱离历史**——伏寿 215 年被废、董贵 200 年衣带诏事发、
   曹贵人 220 年后归曹丕——这些必须被尊重，否则就是"穿越后宫"。
   历史节点处理方式：**汉献帝的"被废""被弑"等是难度，不是禁制**；
   玩家可通过高威权+高声望+关键诏书挽救。

5. **三个新 LLM 调用（event_selector / chat_memory_extractor / consort_agent）
   都会增加 token 消耗**——预估每月 +3–6K tokens。建议：
   - 用更便宜的模型（DeepSeek-V3 / MiniMax 轻量级）
   - 限定 `max_tokens=600`
   - 失败时 fallback 到程序默认

6. **保持"小步快跑"**：每完成一个 prompt 立即 commit + 测试 + 跑一局 demo，
   不要四个 prompt 一次性全上。

---

## 8. 总结：汉献帝的"游戏圣经"是什么？

**不是 4 份 prompt 加起来的总和**——而是：

> 玩家读了 README 后能 5 分钟理解游戏玩法的**叙事版说明书**
> + 开发者看了 prompt 后能 5 分钟理解边界与契约的**机制版说明书**
> + LLM 推演时能在 1 个文件里查到"威权是什么、藩镇如何算、什么能做什么不能做"的**机器版契书**

具体形态：
- **对外**：在 `README.md` 加一节"游戏圣经"指向本文档，附简明版
- **对玩家**：把 `game_world.md` 渲染到 Web 的"游戏说明"Tab（玩家可读）
- **对开发者**：4 份 prompt 是圣经的 4 个"机器可读切片"，各司其职：
  - `game_world.md` = 宪法（所有 prompt 引用它）
  - `event_selector.md` = 候选情势判官（每回合调用一次）
  - `consort_agent.md` = 后宫角色 agent（召幸时调用）
  - `chat_memory_extractor.md` = 召对记忆提取官（每召对结束调用一次）
- **对 LLM**：4 份 prompt 与现有 6 份 prompt 共同构成"模型可读契约集"

**一个比喻**：明末的 4 份 prompt 是"游戏圣经的四大护法"——宪法护法（game_world）、
时序护法（event_selector）、闺阁护法（consort_agent）、史官护法（chat_memory_extractor）。
汉献帝的"游戏圣经"则是这四大护法协同守护的**汉末玩法契约集**。

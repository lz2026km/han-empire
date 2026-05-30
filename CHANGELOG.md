# 汉献帝之末路 · 更新日志

格式：`版本号 YYYY-MM-DD`：更新内容简述

---

## v0.9.0 2026-05-30
### 十项功能全量落地（v0.9升级方案）

#### P0 · 核心体验
- **天子技能树增强**：`emperer_skills` 表 + `activate_skill()`/`deactivate_skill()`/`list_acquired_skills()` + `execute_emperor_skill()` 执行47个技能效果；威权≥40每回合+1技能点，威权≥60+2点，上限10点
- **双Agent推演架构**：`TOP_LEVEL_ALIASES`（28个别名映射）+ `ITEM_FIELD_ALIASES`（170+行字段别名）+ `_extract_metrics_from_narrative()` 正则提取 + `_inject_threshold_crisis_events()` 阈值危机自动注入；新增 `prompts/simulator.md` 季节模拟器 + `prompts/extractor.md` 分数提取器
- **分级财政流**：兖/豫/荆三州分级田赋（×太守能力修正）+ 盐铁专营（威权≥30内库+10）+ 诸侯贡金（威权≥50忠诚诸侯自动缴纳）+ 暗探开支（威权≥40汉室库-5解锁情报）；`apply_graduated_fiscal()` 统一入口

#### P1 · 策略深度
- **派系系统**：`calc_faction_influence()` 四大派系（忠汉派/务实派/离心派/叛逆派）影响力计算；`apply_faction_events()` 派系主导时自动触发效果（忠汉主导→威权+2/声望+5，叛逆主导→威权-5/藩镇+10）；诏书增加派系修正（忠汉大臣×1.2，离心大臣×0.8）；召对prompt注入派系上下文
- **军情/情报系统**：`estimate_military_strength()` 军力估算含等级 + `inspect_warlord_alliances()` 联盟关系 + `check_dongzhuo_trap_status()` 董卓伏诛线详情 + `audit_imperial_treasury()` 收支细目；【🕵️ 情报】Tab（ASCII军力条形图+密探解锁状态）
- **事项追踪增强**：`_inject_crisis_by_metrics()` 藩镇>70注入"诸侯坐大"，威权<10注入"天子形同虚设"（游戏失败边缘），声望<15注入"民心尽失"；`_cascade_issue()` 事项级联（密谋讨贼→董卓警觉/献帝东归→东归失败/讨伐董卓→重建朝纲）；`advance_issue_with_deadline()` deadline超时自动失败

#### P2 · UI增强
- **地图视图**：ASCII八州地图（幽/并/兖/豫/扬/荆/益/凉/司隶）+ 州份按立场着色（忠蓝/中灰/敌红）+ 每州显示州名/太守/驻军/立场/人口 + 【🗺️ 地图】Tab
- **天子日志**：`emperor_diary` 表 + `_emperor_mood()` 威权→心境映射 + `_generate_emperor_diary()` LLM生成回合日记（<100字，格式：第N回合·{月}·{天子心境}）+ 【📖 天子日记】Tab日记体显示

#### P3 · 代差填补
- **建筑系统简化版**：`buildings` 表 + `upsert_building()`/`list_buildings()`/`inspect_building()`；未央宫（威权+3/年）、洛阳武库（军事+15%）、许昌行宫（威权衰减-50%）、各州粮仓（税收+10%）；`apply_building_maintenance()` 维护费扣除+建筑效果结算
- **指令状态机**：`directives` 表（id/campaign_id/type/kind/status/content/issued_turn/expires_turn）+ `create_directive()`/`update_directive_status()`/`list_active_directives()`/`expire_old_directives()` 完整CRUD；诏书经状态机管理（draft→issued→expired）；3回合过期机制

#### 技术改进
- Web界面升级为8 Tab：**总览 / 召对 / 诏书 / 势力 / 历史 / 日志(天子日记) / 情报 / 地图**
- `warlord_changes` 字段加入 `SimulationResult`，月末推演结果展示诸侯动态
- 大臣技能授权：`grant_skill_to_minister()`/`revoke_minister_skill()`/`active_skill_grants()`

---

## v0.8.3 2026-05-30
### 忠诚度上下文 + 诸侯动态 + 衣带密诏Web独立按钮
- `session.summon_minister()` 注入忠诚度上下文到 prompt + agent system_prompt
- `agents.create_minister_agent()` 接收 `loyalty_ctx` 参数
- `SimulationResult` 新增 `warlord_changes` 字段；月末推演展示诸侯动态
- `DECREE_TYPES` 新增"衣带密诏"/"献帝东归"选项
- `cmd_decree()` 识别后走独立 `issue_secret_edict()` 逻辑

---

## v0.8.2 2026-05-30
### 藩镇动态 + 忠诚度 + 衣带诏 + 仪表盘 + 势力视图
- `flows.apply_warlord_actions()` 每回合诸侯自动行动写入 `last_action`
- `flows.loyalty_multiplier()` 四档折扣系数 + `get_minister_loyalty_context()` 召对上下文
- `minister_agent.md` 新增忠诚度说明节
- `decree.issue_secret_edict()` 威权≥30+忠诚大臣≥3可发布衣带密诏
- Web界面重构为 `gradio.Tabs` 六栏 + `_render_dashboard_html()` 仪表盘 + `_render_powers_html()` 势力视图

---

## v0.8.1 2026-05-30
### 扩充开局邸报
- 天子近况 / 汉室国势 / 五困局 / 势力格局 / 历史线状态 / 游戏系统说明
- 189年开局设定完整落地

---

## v0.8.0 2026-05-29
### issues.py 完整方法链
- `advance_issue()` 返回行数+结案判定
- `close_issue(reason)` 结案
- `cancel_issue()` 取消
- `mark_event_triggered()` 标记事件已触发
- `list_active_issues()` 列出活跃事项
- 数据落地全部完整

---

## v0.7.9 2026-05-29
### db.py 完整 schema + 种子数据 + 状态读写
- 12张核心表完整 schema
- 种子数据初始化
- 状态读写方法

---

## v0.7.6 2026-05-30
### prompts目录 + buildings.json + token_stats.py
- `content/prompts/memory_extractor.md`：记忆档房
- `content/prompts/decree_writer.md`：诏书润色官
- `content/prompts/minister_agent.md`：大臣召对Agent
- `content/prompts/season_simulator.md`：月末推演奏章
- `content/buildings.json`：26个汉末建筑
- `han_sim/token_stats.py`：Token用量统计

---

## v0.7.5 2026-05-28
### emperor_skills.json + classes.json + skills.py
- `content/emperor_skills.json`：天子技能树48条（经略/权谋/武功/文治四系各12）
- `content/classes.json`：汉末8阶级49条
- `han_sim/skills.py`：技能体系查询（241行）

---

## v0.7.4 2026-05-28
### 辅助模块补齐
- `han_sim/assets.py`：资源加载/JSON校验
- `han_sim/matching.py`：模糊匹配+汉末别名表（221行）
- `han_sim/context.py`：25个历史锚点+6种汉末胜负判定（266行）
- `han_sim/report.py`：回合报告格式化（176行）
- `content/skill_tools.json`：20条汉末诏令工具模板
- `content/opening_gazette.md`：开局邸报

---

## v0.7.3 2026-05-27
### 内容侧扩充完成
- `characters.json`：120条（+11）
- `regions.json`：50条（+13）
- `powers.json`：30条（+10）
- `events.json`：79条（+20）
- `seed_events.json`：40条（+10）
- `decrees.json`：30条（新建）
- `skills.json`：20条（新建）
- **合计369条**，内容侧扩充完成

---

## v0.7.2 2026-05-26
### Web界面升级
- 仪表盘：年月/威权等级/都城/国库/内库/民心
- 召对历史：完整对话记录
- 游戏日志：诏令/召对/事件时间线
- 事务Tabs：问题追踪基础界面

---

## v0.7.1 2026-05-25
### 汉室特色机制
- 威权系统：随都城/事件动态变化
- 迁都机制：洛阳↔长安↔许昌三都流转
- 忠诚度衰减：随时间和事件变化
- 董卓伏诛判定
- 献帝东归判定
- 藩镇动态系统

---

## v0.7.0 2026-05-24
### 核心系统完成
- 回合制模拟框架（基于历史锚点）
- LLM驱动的大臣召对系统
- 圣旨系统（口谕→草案→诏书）
- Gradio Web界面

---

## v0.5.0 2026-05-20
### 记忆系统核心
- `event_memories` 表 + 读写
- LLM 记忆提取
- 召见注入

---

详见 [GitHub Release](https://github.com/lz2026km/han-empire/releases) 页面
### 新增内容
- `content/buildings.json`：26个汉末建筑（洛阳/长安/许昌宫阙+郡城+武库+太仓等）
- `content/prompts/memory_extractor.md`：记忆档房，提取旧事记忆卡
- `content/prompts/decree_writer.md`：诏书润色官，汉末诏令体
- `content/prompts/minister_agent.md`：大臣召对Agent，汉末派系/拟旨/密令
- `content/prompts/season_simulator.md`：月末推演奏章，汉末邸报体+历史锚点

### 新增模块
- `han_sim/token_stats.py`：Token用量monkey-patch统计，支持caller_tag/cached_tokens/reasoning_tokens

---

## v0.7.5 2025-05-30
### 新增内容
- `content/emperor_skills.json`：天子技能树，经略/权谋/武功/文治四系各12条，共48条
- `content/classes.json`：阶级数据，汉末8阶级(豪族/寒门/羌胡/流民/商贾/士人/宦官/宗室)，按区域分布，共49条

### 新增模块
- `han_sim/skills.py`：技能体系查询（available_emperor_skills/skill_unlock_met/print_emperor_skill_tree/skill_template等）

---

## v0.7.4 2025-05-30
### 新增模块
- `han_sim/assets.py`：资源加载/JSON校验/格式化工具（145行）
- `han_sim/matching.py`：地区/军队/人物模糊匹配，汉末别名表（221行）
- `han_sim/context.py`：25个历史锚点 + 6种汉末版胜负判定（266行）
- `han_sim/report.py`：回合报告/数值变化格式化（176行）
- `han_sim/exceptions.py`：新增LLMContractError

### 新增内容
- `content/skill_tools.json`：20条汉末诏令工具模板
- `content/opening_gazette.md`：开局邸报（中平六年189年正月）

---

## v0.7.3 2025-05-29
### 内容侧扩充完成
- `characters.json`：120条（+11新人物）
- `regions.json`：50条（+13新州郡）
- `powers.json`：30条（+10新势力）
- `events.json`：79条（+20新事件）
- `seed_events.json`：40条（+10新种子事件）
- `decrees.json`：30条（新建圣旨系统）
- `skills.json`：20条（新建技能系统）
- **合计369条**，内容侧扩充完成

---

## v0.7.2 2025-05-29
### Web界面升级
- 仪表盘：年月/威权等级/都城/国库/内库/民心实时显示
- 召对历史：完整对话记录可展开/收起
- 游戏日志：诏令/召对/事件时间线
- 事务Tabs：问题追踪系统基础界面

---

## v0.7.1 2025-05-29
### 汉室特色机制
- 威权系统：随都城/事件动态变化
- 迁都机制：洛阳↔长安↔许昌三都流转
- 忠诚度衰减：随时间和事件变化
- 董卓伏诛判定：基于威权/事件/军事综合判定
- 献帝东归判定：基于董卓状态/藩镇动态
- 藩镇动态系统：各地节度使/太守势力变化

---

## v0.7.0 2025-05-29
### 核心系统完成
- 回合制模拟框架（基于历史锚点）
- LLM驱动的大臣召对系统
- 圣旨系统（口谕→草案→诏书）
- 基础数据框架（characters/regions/powers/events/armies）
- Gradio Web界面

---

## 早期版本（略）

详见 GitHub Release 页面
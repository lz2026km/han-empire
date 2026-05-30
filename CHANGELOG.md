# 汉献帝之末路 · 更新日志

格式：`版本号 YYYY-MM-DD`：更新内容简述

---

## v0.7.6 2025-05-30
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
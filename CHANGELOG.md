# 更新日志 Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.9.6] - 2026-05-31

### Step2 - 威权机制

#### Added
- **威权等级系统** (`han_sim/models.py`)
  - `AuthorityLevel` dataclass：等级标签、诏书倍率、召对倍率、诸侯稳定性、派系事件修正、可用恢复行动
  - `AUTHORITY_LEVELS` 字典：0/10/20/30/40/50/60/70/80/90/100 共11个等级节点
  - 5档分类：形同虚设(0-19) / 阳奉阴违(20-49) / 诏书有效(50-79) / 号令四方(80-100)
  - `get_authority_level()` 函数：根据威权值返回对应等级信息

- **威权机制核心** (`han_sim/flows.py` 新增 `apply_authority_effects()`)
  - 威权>=50：每回合藩镇-1（抑制效果）
  - 威权>=60：每回合声望+1（天子有底气则民心稳）
  - 威权<=10：每回合藩镇+2（诸侯坐大）
  - 威权等级变化时触发日志提示

- **威权驱动忠诚度衰减** (`han_sim/flows.py` `apply_loyalty_decay()` 重写)
  - 威权>=80：忠诚度几乎不衰减
  - 威权50-79：标准衰减
  - 威权20-49：衰减加速
  - 威权<20：衰减最快

- **威权恢复行动系统** (`han_sim/flows.py`)
  - `AUTHORITY_RECOVERY_ACTIONS` 字典：13种恢复行动（求情示弱/笼络近臣/朝会演讲等）
  - 每种行动有效果、内库消耗、威权等级要求
  - `execute_authority_recovery()` 函数：检查威权等级可用性+内库足够+执行效果

- **威权对诏书/召对效果折扣**
  - `decree.py` `issue_decree()`：诏书效果乘以 `auth_level.decree_mult`
  - `session.py` `summon_minister()`：prompt注入威权等级上下文，召对agent获知天子威权状态

- **simulation.py 威权效果调用**：每月末推演调用 `apply_authority_effects()`

## [0.9.4] - 2026-05-30

> ⚠️ **版本说明**：远程分支标注为"v0.2.0"，本地已统一为 v0.9.4。
> 本文件为唯一真实版本记录，版本号以 git tag 为准。

### Added
- **古风主题系统** (`han_sim/theme.py` 新建)
  - 古风配色常量（玄黑/朱红/古金/暗青/暖白17色）
  - `get_theme_css()` - 完整 Gradio CSS（含 Google Fonts）
  - 全局样式：按钮/Tab/输入框/表格/滚动条
  - 古风字体（Noto Serif SC 标题 / Noto Sans SC 正文）

- **人物头像系统** (`han_sim/portraits.py`)
  - 头像URL映射表（warlord_pool_X / minister_pool_X / emperor_pool_X）
  - `render_portrait_with_name_html()` - 单角色头像+名字+官职
  - `render_avatar_grid_html()` - 多角色网格视图
  - 头像加载失败兜底机制（Emoji + 古风渐变背景）
  - 官职emoji映射（👑帝王 / ⚔️武将 / 📜文臣 / 🐉诸侯）

- **诏书系统升级** (`han_sim/decree.py` L6)
  - `parse_decree_intent()` - 自然语言意图解析（LLM + 规则引擎双模式）
  - 历史典故库 `HISTORICAL_REFERENCES`（尧舜/周公/高祖/苏武/董卓等30+典故）
  - 40+ 诏书模板（每种意图3-5种风格变体）

- **SVG十三州地图** (`han_sim/map_view.py` 新建)
  - 东汉十三州完整轮廓（司隶/豫州/兖州/徐州/青州/荆州/扬州/益州/凉州/并州/幽州/冀州/交州）
  - 势力颜色区分（蓝=忠汉/金=汉室/紫=董卓/红=敌对/灰=中立）
  - 献帝位置SVG闪烁动画（金色脉冲标记）

### Changed
- `web_app.py` - 集成古风主题（`css=get_theme_css()`）
- `web_app.py` - 集成portraits和map_view
  - "在朝大臣"Tab：表格 → 头像网格
  - "召对"Tab：大臣回复前显示80px大头像
  - "地图"Tab：ASCII地图 → SVG十三州地图
- `pyproject.toml` version: 0.9.3 → 0.9.4

### Fixed
- `GameDB.new()` 工厂方法（db.py）：修复 `AttributeError: type object 'GameDB' has no attribute 'new'`，兼容 `session.py` 调用
- P0修复：API配置（base_url/model）、SQLite WAL模式、__pycache__清理

## [0.9.0] - 2026-05-30

### Added
- **天子技能树**（`skills.py` 44→228行）
- **双Agent推演架构**（别名映射+阈值危机+天子日记）
- **分级财政**（田赋/盐铁/贡金/暗探）
- **派系系统**（四大派系影响+`apply_faction_events`）
- **军情情报**（4工具+情报Tab）
- **事项增强**（危机注入+级联+deadline）
- **地图视图**（ASCII八州地图）
- **天子日记LLM生成**
- **建筑系统**（6建筑+维护费结算）
- **指令状态机**（directives表完整CRUD）
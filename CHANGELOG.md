# 更新日志 Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.9.9] - 2026-05-31

### Animation Expansion & New UI Components

#### Added
- **40+ New CSS Animations** (`web/src/styles/animations.css`)
  - Imperial seal stamp, scroll reveal, war drum pulse, fire glow
  - Ink wash effect, notification toast slides, dragon pulse
  - Lantern float, earthquake shake, banner unfurl, sword glint
  - Arrow rain, fan unfold, silk flow, pearl glow effects

- **New React Components**
  - `Notification.tsx/.css` - Real-time toast notification system (7 types)
  - `MinisterPortrait.tsx/.css` - Character portrait with faction colors
  - `BattleView.tsx/.css` - Turn-based battle visualization
  - `FactionRelationDiagram.tsx/.css` - SVG faction relationship diagram
  - `ProvinceMap.css` - Enhanced map with terrain, tooltip, season indicator

- **ProvinceMap Enhancements** (`web/src/components/ProvinceMap.tsx`)
  - Terrain types for each province
  - Adjacent province connections
  - Hover tooltip with detailed stats
  - Season indicator animation
  - Critical unrest pulse animations

#### Changed
- Updated HanEmpireSim.spec for Windows 10/11 desktop packaging

---

## [0.9.6] - 2026-05-31

### Step7 - 献帝东归

#### Added
- **东归启动** (`han_sim/flows.py` `initiate_emperor_escape()`)
  - 需董卓伏诛后触发
  - 威权>=60：成功率80%，效果威权+15，声望+10
  - 威权<60：成功率50%，效果威权+5，声望+3
  - 自动设置 `emperor_escaped_turn`

- **东归执行检查** (`han_sim/flows.py` `execute_emperor_escape_check()`)
  - 每回合检查东归状态：成功/失败/进行中
  - 返回状态、已用回合、剩余回合

- **simulation.py集成**（Step7）
  - 东归失败 → threshold_crisis（威权-10，声望-5，藩镇+5）
  - 东归成功 → historical（献帝抵达许昌）

- **献帝东归Tab** (`web_app.py`)
  - 显示状态：困于长安/东归中/已成功
  - 倒计时显示（5回合）
  - 目标选择（许昌/洛阳/邺城）+ 发起东归按钮

- **cmd_emperor_escape()** (`web_app.py`)
  - 验证董卓已伏诛
  - 调用 `initiate_emperor_escape()`
  - 返回结果（状态/叙事/效果）

### Step6 - 董卓伏诛

#### Added
- **董卓伏诛线触发** (`han_sim/flows.py` `trigger_dongzhuo_trap()`)
  - 威权>=40时每月自动触发 `dong_zhuo_trapped_turn`
  - 触发时记录日志"董卓伏诛线触发"

- **伏诛判定逻辑** (`han_sim/flows.py` `execute_dongzhuo_elimination()`)
  - 成功条件：联军军力>=40，威权>=60时-10
  - 成功效果：威权+30，声望+20，藩镇-15，汉室库+50
  - 失败效果：威权-10，声望-5

- **simulation.py集成**（Step6）
  - 每月检查威权>=40时自动触发伏诛线
  - `trigger_dongzhuo_trap()` 在 authority_changes 后调用

- **讨伐董卓Tab** (`web_app.py`)
  - 显示当前状态：肆虐中/被围困中/已伏诛
  - 围困倒计时（6回合）
  - 机制说明表格
  - 联军军力输入 + 执行按钮

- **cmd_dongzhuo_elimination()** (`web_app.py`)
  - 输入联军军力，触发伏诛判定
  - 返回成功/失败状态+效果+所需/实际军力

### Step5 - 忠诚度系统

#### Added
- **大臣忠诚度衰减** (`han_sim/flows.py` `apply_loyalty_decay()`)
  - 威权>=80：几乎不衰减
  - 威权50-79：标准衰减
  - 威权20-49：加速衰减
  - 威权<20：最快衰减
  - 权臣麾下角色（董卓/曹操/吕布）额外+1

- **诸侯忠诚度衰减** (`han_sim/flows.py` `apply_warlord_loyalty_decay()`)
  - 按立场衰减：敌对(最快)/中立/忠诚(最慢)
  - 受威权等级 `warlord_stability` 修正（威权越高衰减越慢）

- **叛逃事件检测** (`han_sim/flows.py` `check_betrayal_events()`)
  - 威权<20+忠诚度<30+有势力归属 → 3%叛逃概率
  - 威权<15+藩镇>=80 → 5%藩镇脱离概率

- **忠诚度恢复行动** (`han_sim/flows.py`)
  - `LOYALTY_RECOVERY_ACTIONS` 字典：施恩(+5)/嘉奖(+8)/笼络(+6)/赦免(+10)/晋升(+12)
  - `apply_loyalty_recovery()` 函数：内库检查→扣费→忠诚度更新

- **忠诚度Tab** (`web_app.py`)
  - 大臣忠诚度列表（名称/官职/忠诚/状态条）
  - 诸侯忠诚度列表（势力/首领/忠诚/状态条）
  - 恢复行动按钮+执行下拉菜单

- **simulation.py 集成**：每月末推演调用 `apply_warlord_loyalty_decay()` 和 `check_betrayal_events()`

### Step4 - 迁都系统

#### Added
- **迁都Tab** (`web_app.py`)
  - 新增「🏰 迁都」Tab页面：当前都城显示+5城选项+效果预览表
  - 都城选项：洛阳/许昌/长安/邺城/南阳（含说明、效果、状态）
  - 威权约束：需威权≥30才能执行迁都

- **迁都效果系统** (`han_sim/flows.py`)
  - `_CAPITAL_EFFECTS` 字典：洛阳(无)/许昌(+5威权)/长安(-5声望-3威权-5藩镇)/邺城(-3声望-5威权-8藩镇)/南阳(-2声望-2威权-3藩镇)
  - `relocate_capital()` 函数：验证合法性→应用效果→更新state.capital→记录日志

- **迁都命令** (`web_app.py` `cmd_relocate_capital()`)
  - 检查当前都城、威权约束、内库足够
  - 返回迁都效果变化（颜色编码+/红/绿）

- **迁都预览HTML** (`web_app.py` `_render_relocate_html()`)
  - 当前都城高亮卡片
  - 5城选项表格：名称/说明/效果/状态列
  - 威权不足提示

### Step3 - 界面美化 + 威权恢复 + 诏书预览

#### Added
- **威权仪表盘** (`web_app.py`)
  - 专属卡片显示威权值/等级/诏书倍率/召对倍率，威权<20红色脉冲动画
  - 威权恢复行动按钮（从左侧仪表盘点击选择）
  
- **诏书预览系统** (`web_app.py`)
  - 选择诏书类型后实时显示预计效果（含威权折扣后数值+汉室库消耗）
  - 使用 `DECREE_EFFECT_TEMPLATES` 替代不存在的 `DECREE_EFFECTS`
  
- **装饰性标题栏** (`web_app.py`)
  - 渐变背景+金色分隔线+天子威权光晕效果
  - `TITLE_BANNER` 和 `DIVIDER_SVG` 装饰组件

- **三栏布局优化**
  - 左侧国势+大臣，中央Tab，右侧威权恢复+快捷操作
  - 威权恢复独立面板：13种恢复行动，按威权等级解锁

- **朱红渐变主按钮** (`theme.py`)
  - `btn-royal` 线性渐变+悬停金色光晕动画

- **历史线进度条**
  - 董卓伏诛/献帝东归双线，颜色动态（绿/橙/灰）

#### Fixed
- `DECREE_EFFECTS` → `DECREE_EFFECT_TEMPLATES`（诏书预览数据源修复）

#### Changed
- 诏书预览区：诏书Tab新增实时预览，预览随类型切换
- 威权标签系统：从硬编码if分支改为 `get_authority_level()` 映射

### Step2 - 威权机制

 - 威权机制

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
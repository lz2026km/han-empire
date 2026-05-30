# 更新日志 Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.2.0] - 2026-05-30

### Added
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
  - 向后兼容下拉菜单方式

- **SVG十三州地图** (`han_sim/map_view.py` 新建)
  - 东汉十三州完整轮廓（司隶/豫州/兖州/徐州/青州/荆州/扬州/益州/凉州/并州/幽州/冀州/交州）
  - 势力颜色区分（蓝=忠汉/金=汉室/紫=董卓/红=敌对/灰=中立）
  - 献帝位置SVG闪烁动画（金色脉冲标记）
  - 动态图例和标题栏

### Changed
- `web_app.py` - 集成portraits和map_view
  - "在朝大臣"Tab：表格 → 头像网格
  - "召对"Tab：大臣回复前显示80px大头像
  - "地图"Tab：ASCII地图 → SVG十三州地图
- `pyproject.toml` version: 0.1.0 → 0.2.0

### Fixed
- P0修复：API配置（base_url/model）、SQLite WAL模式、__pycache__清理
（见commit b4bbae9）

## [0.1.0] - 2026-05-27

### Added
- Initial release
- 核心游戏系统：回合模拟/召对/诏书/事项追踪
- Gradio Web UI（8 Tab布局）
- Agno多Agent LLM编排
- 189年董卓进京开局剧本
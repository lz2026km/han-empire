# 汉献帝之末路 - 项目开发指南

## 项目概述

**名称**: 汉献帝之末路（Han Empire）
**类型**: 历史策略模拟游戏（Web App）
**技术栈**: Python (Flask/Gradio) + HTML/CSS + JavaScript
**分辨率**: 1920×1080（1080P桌面端）

---

## 核心文件结构

```
han-empire/
├── web_app.py              # 主应用（2355行）- Gradio UI + 路由
├── han_sim/
│   ├── models.py           # 数据模型（Skill/Faction/Building）
│   ├── decree.py           # 诏书系统（~1000行）
│   ├── flows.py            # 核心流程（~1100行）
│   ├── session.py          # GameSession 管理
│   ├── db.py               # GameDB（~1800行）
│   ├── simulation.py       # 游戏模拟
│   ├── agents.py           # AI Agent（LLM集成）
│   ├── skills.py           # 技能系统
│   ├── content.py          # 游戏内容加载
│   └── theme.py            # UI主题
└── .claude/
    ├── CLAUDE.md           # 本文件
    ├── commands/           # 命令目录
    └── agents/             # Agent目录
```

---

## 开发原则

### 1. 提交规范（Claude Code风格）
- **小步提交**: 每个功能单独commit
- **描述清晰**: `type: 简短描述` 格式
- **分支策略**: `feature/step{N}-{description}`

### 2. UI设计原则
- **分辨率**: 1920×1080 固定宽度
- **配色**: 玄黑/朱红/古金（#1a1a2e/#c94043/#c9a96e）
- **交互**: 纯桌面鼠标操作，无移动端适配

### 3. 代码规范
- **Python版本**: 3.6.8 兼容（无`from __future__ import annotations`）
- **类型提示**: `tuple[str,str]` → `Tuple[str,str]`
- **AGNO降级**: Agent导入可选化，无LLM时使用fallback

---

## 常用命令

### Git 工作流
```bash
# 创建功能分支
git checkout -b feature/step{N}-{description}

# 提交代码
git add -A && git commit -m "type: 简短描述"

# 推送PR
git push -u origin feature/step{N}-{description}
```

### 测试
```bash
# 编译检查
python3 -m py_compile han_sim/*.py web_app.py

# 集成测试
python3 << 'EOF'
import sys; sys.path.insert(0, '.')
from han_sim.content import load_game_content
from han_sim.session import GameSession
from han_sim.decree import issue_decree
# ... 测试代码
EOF
```

---

## 核心系统清单

| 系统 | 文件 | 关键函数 |
|------|------|----------|
| 诏书 | decree.py | issue_decree(), generate_decree_text() |
| 技能 | models.py | get_available_skills(), can_activate_skill(), activate_skill() |
| 派系 | flows.py | calc_faction_influence(), apply_faction_events() |
| 建筑 | models.py | repair_building(), get_available_buildings() |
| 事件 | flows.py | check_event_trigger(), trigger_random_event() |
| 会话 | session.py | GameSession.new(), load_session() |

---

## UI Tab结构

```
🎙️ 召对 | 📜 诏书 | ⚔️ 势力 | 🕵️ 情报 | 🗺️ 地图 | 📖 历史
📋 日志 | 🚗 东归 | ⚡ 事件 | 📜 史册 | ⚔️ 讨伐 | 💗 忠诚度
🌳 技能 | 🏛️ 建筑 | 📋 诏令 | 🏠 迁都
```

---

## 关键指标

| 指标 | 范围 | 说明 |
|------|------|------|
| 威权 | 0-100 | 核心数值，影响所有系统 |
| 藩镇 | 0-100 | 军阀势力，越低越好 |
| 声望 | 0-100 | 汉室威望 |
| 汉室库 | 0-∞ | 财政储备 |
| 内库 | 0-∞ | 皇帝私人金库 |
| 民心 | 0-100 | 民间支持 |
| skill_points | 0-∞ | 技能点数 |

---

## 注意事项

### AGNO降级策略
```python
try:
    from agno.agent import Agent
except ImportError:
    Agent = None
```
无LLM时各模块使用fallback（decree用模板生成/simulation跳过LLM叙事）

### Python 3.6兼容性
- 禁止: `from __future__ import annotations`
- 必须: `Tuple[str, str]` 而非 `tuple[str, str]`
- 禁止: f-string表达式包含反斜杠

### Dashboard字节偏移修复
大字符串替换用字节级偏移精确定位：
```python
raw = content.encode('utf-8')
# 计算偏移量，替换
content = raw.decode('utf-8')
```
# 开发指南

## 项目结构

```
han-empire/
├── web_app.py              # Gradio 主应用（UI + 路由）
├── han_sim/
│   ├── models.py           # 数据模型（Skill/Faction/Building/AuthorityLevel）
│   ├── decree.py           # 诏书系统（issue_decree + 模板生成）
│   ├── flows.py            # 核心流程（apply_* 系列函数）
│   ├── session.py          # GameSession 会话管理
│   ├── db.py               # GameDB SQLite 封装
│   ├── simulation.py       # 游戏循环（advance_turn）
│   ├── agents.py           # AI Agent（LLM 集成，可选）
│   ├── content.py          # 游戏内容加载
│   └── theme.py            # UI 主题
├── scripts/
│   └── e2e_test.py         # 端到端测试
├── .claude/                # Claude Code 配置
└── docs/                   # 文档
```

## 核心概念

### 1. GameSession（会话）
```python
session = GameSession.new('campaign-id', content)
state = session.state    # GameState 对象
db = session.db          # GameDB 对象
```

### 2. GameState（游戏状态）
```python
state.turn              # 当前回合
state.capital           # 都城
state.metrics           # 核心指标字典
state.dong_zhuo_*       # 董卓相关状态
state.emperor_*         # 献帝相关状态
```

### 3. GameDB（数据库）
```python
db.list_powers()        # 势力列表
db.list_regions()       # 地区列表
db.list_buildings()     # 建筑列表
db.list_characters()    # 人物列表
db.save_state()         # 保存状态
```

## 核心指标

| 指标 | 范围 | 说明 |
|------|------|------|
| 威权 | 0-100 | 核心数值，影响所有系统 |
| 藩镇 | 0-100 | 军阀势力，越低越好 |
| 声望 | 0-100 | 汉室威望 |
| 汉室库 | 0-∞ | 财政储备 |
| 内库 | 0-∞ | 皇帝私人金库 |
| skill_points | 0-10 | 技能点数 |

## 威权等级

| 威权 | 等级标签 | 诏书倍率 |
|------|----------|----------|
| 0-9 | 形同虚设 | 30% |
| 10-19 | 权臣操弄 | 40% |
| 20-39 | 阳奉阴违 | 60-70% |
| 40-59 | 勉强维持 | 80% |
| 60-79 | 略有起色 | 100% |
| 80-99 | 号令四方 | 120% |
| 100 | 至高无上 | 150% |

## 开发命令

```bash
# 运行测试
python3 scripts/e2e_test.py

# 编译检查
python3 -m py_compile han_sim/*.py web_app.py

# 启动应用
python3 web_app.py
```

## 提交规范

```
fix: 修复问题
feat: 新功能
ui: UI 变更
refactor: 重构
docs: 文档
test: 测试
```

## Python 3.6 兼容性

- ❌ 禁止：`from __future__ import annotations`
- ❌ 禁止：`tuple[...]`, `dict[...]`, `set[...]`
- ✅ 必须：`Tuple[...]`, `Dict[...]`, `Set[...]`
- ❌ 禁止：f-string 表达式包含反斜杠

## AGNO 降级

AGNO（LLM Agent）可选安装，无 AGNO 时系统使用 fallback：
- decree.py：使用模板生成诏书
- simulation.py：跳过 LLM 叙事
- agents.py：`Agent = None` 时不创建 Agent
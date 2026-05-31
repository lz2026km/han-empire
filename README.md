# 汉献帝之末路 - Python Game Project

Python 3.6+ required.

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
python web_app.py
```

访问 http://localhost:7860

## 项目结构

```
han-empire/
├── web_app.py          # 主应用（Gradio UI）
├── han_sim/            # 游戏核心模块
│   ├── models.py       # 数据模型
│   ├── decree.py       # 诏书系统
│   ├── flows.py        # 核心流程
│   ├── session.py      # 会话管理
│   ├── db.py           # 数据库
│   └── simulation.py   # 游戏模拟
├── scripts/            # 工具脚本
├── .claude/            # 开发配置（Claude Code）
└── docs/               # 文档
```

## 开发

### 测试
```bash
python3 scripts/e2e_test.py
```

### 代码检查
```bash
python3 -m py_compile han_sim/*.py web_app.py
```

## 游戏规则

玩家扮演汉献帝，在董卓之乱后的乱世中重振汉室。
- **威权**：核心指标，影响所有系统
- **藩镇**：军阀势力，越低越好
- **诏书**：颁布政令改善局势
- **技能**：解锁强力特权
- **事件**：随机历史事件影响游戏
# 汉献帝之末路

基于 LLM + 历史推演的古风帝王游戏。玩家扮演汉献帝刘协，在曹操「挟天子以令诸侯」的控制下，寻求兴复汉室之道。

## 游戏背景

189年，董卓进京废少帝立献帝，拉开汉末乱世序幕。献帝先被董卓控制，后被曹操迁都许昌，名为天子，实为阶下囚。

## 核心玩法

- **召见大臣**：与三国名臣对话，获取建议或试探忠诚
- **月末推演**：数值结算（税收/军费/民变），触发历史事件
- **拟旨诏书**：颁布政策，改变势力格局
- **历史锚定**：189-220年真实历史事件按时间线依次展开

## 技术栈

- Python 3.11+ / SQLite
- Agno（LLM Agent 框架）
- 支持 MiniMax / DeepSeek / OpenAI 等 OpenAI 兼容 API

## 快速开始

```bash
pip install -e .
python launcher.py
```

## 目录结构

```
han-empire/
├── han_sim/           # 核心游戏引擎
│   ├── models.py      # 数据类
│   ├── db.py          # SQLite 持久化
│   ├── session.py     # 回合流转
│   ├── flows.py       # 财政流
│   ├── agents.py      # LLM Agent
│   └── content.py     # 内容加载
├── content/           # 游戏内容
│   ├── characters.json
│   ├── regions.json
│   ├── events.json
│   ├── powers.json
│   └── armies.json
├── web_app.py         # Web 界面
└── launcher.py        # 启动器
```

## 游戏结局

1. **兴复汉室**：联吴抗曹 → 赤壁翻盘 → 还于旧都
2. **三分天下**：鼎足之势 → 缓缓图之
3. **禅让延续**：220年曹丕篡汉
4. **提前灭亡**：皇权彻底丧失 → 游戏结束

##  License

MIT
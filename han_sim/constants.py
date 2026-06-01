# -*- mode: python ; coding: utf-8 -*-
"""
汉献帝之末路 - 游戏常量与配置
"""

# 游戏版本
VERSION = "0.9.6"
VERSION_NAME = "献帝末路"

# 时间配置
INITIAL_YEAR = 189
INITIAL_MONTH = 1
MAX_TURNS = 500

# 威权等级
AUTHORITY_THRESHOLDS = {
    "形同虚设": (0, 19),
    "权臣操弄": (20, 29),
    "阳奉阴违": (30, 49),
    "勉强维持": (50, 59),
    "诏书有效": (60, 69),
    "朝纲初振": (70, 79),
    "威权渐张": (80, 89),
    "号令四方": (90, 99),
    "至高无上": (100, 100),
}

# 财政配置
INITIAL_TREASURY = 200
INITIAL_INNER_TREASURY = 100
INITIAL_REPUTATION = 30
INITIAL_AUTHORITY = 15
INITIAL_FANZHEN = 80

# 派系配置
FACTION_TYPES = ["忠汉派", "务实派", "离心派", "叛逆派"]

# 诏书类型
DECREE_TYPES = [
    "衣带密诏",
    "讨伐诏书",
    "迁都诏书",
    "嘉奖诏书",
    "罪己诏",
    "大赦天下",
    "自由诏书",
]

# 技能树配置
SKILL_BRANCHES = ["经略", "权谋", "武功", "文治"]
SKILL_POINTS_PER_LEVEL = {
    0: 0,
    40: 1,
    60: 2,
    80: 3,
    100: 4,
}

# 建筑配置
BUILDING_CATEGORIES = ["宫殿", "军事", "经济", "特殊"]
MAX_BUILDINGS = 10

# 事件配置
EVENT_TRIGGER_CHANCE = {
    "disaster": 0.15,
    "rebellion": 0.10,
    "plague": 0.05,
    "famine": 0.12,
}

# AI配置
AI_MODEL = "deepseek-v4-flash"
AI_TEMPERATURE = 0.7
AI_MAX_TOKENS = 8000
AI_TIMEOUT = 180

# 界面配置
THEME_COLORS = {
    "primary": "#c9a96e",      # 金色
    "secondary": "#8a221a",    # 朱红
    "background": "#1a1a2e",   # 玄黑
    "surface": "#16213e",      # 深蓝
    "text": "#e8d5b7",         # 米白
    "text_secondary": "#9ca3af",  # 灰色
    "success": "#22c55e",      # 绿色
    "warning": "#f59e0b",      # 橙色
    "error": "#ef4444",        # 红色
}

# 界面配置
TURN_UNIT = "月"  # 回合时长单位

# 动画配置
ANIMATION_DURATION = {
    "fast": 150,
    "normal": 300,
    "slow": 500,
}

# 地图配置
PROVINCE_POSITIONS = {
    "司隶": {"x": 400, "y": 300, "width": 80, "height": 60},
    "兖州": {"x": 500, "y": 200, "width": 70, "height": 50},
    "豫州": {"x": 550, "y": 280, "width": 70, "height": 50},
    "荆州": {"x": 450, "y": 380, "width": 90, "height": 70},
    "扬州": {"x": 620, "y": 350, "width": 100, "height": 80},
    "徐州": {"x": 580, "y": 180, "width": 60, "height": 50},
    "幽州": {"x": 280, "y": 120, "width": 100, "height": 80},
    "并州": {"x": 320, "y": 220, "width": 80, "height": 60},
    "冀州": {"x": 380, "y": 180, "width": 90, "height": 60},
    "青州": {"x": 540, "y": 130, "width": 60, "height": 50},
    "凉州": {"x": 180, "y": 350, "width": 120, "height": 100},
    "益州": {"x": 250, "y": 420, "width": 130, "height": 110},
    "交州": {"x": 550, "y": 480, "width": 100, "height": 80},
}

# 人物头像配置
PORTRAIT_POOLS = {
    "emperor": ["emperor_han"],
    "minister": [f"minister_pool_{i}" for i in range(1, 20)],
    "general": [f"general_pool_{i}" for i in range(1, 30)],
    "warlord": [f"warlord_pool_{i}" for i in range(1, 25)],
}

# ── 回合阶段（v1.13.1 乾坤大挪移修小版本补）──
# 历史遗留 BUG：session.py 引用这三个常量但 constants.py 没定义。
# TurnPhase Enum 的字符串值，session.py 用作默认 turn_phase。
# v1.9.0 同步明末时未补全，导致 session.py 实际 import 必失败。
# 旧 server 进程（pid 4116087）能跑通仅因缓存了老 GAMES 字典。
PHASE_SUMMONING = "SUMMONING"   # 召对中：等大臣入宫
PHASE_REVIEWING = "REVIEWING"   # 御览中：月末奏章/推演中
PHASE_ISSUED    = "ISSUED"      # 诏书已下：执行/调兵
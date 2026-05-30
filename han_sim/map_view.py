"""东汉十三州 SVG 地图可视化。L6。

生成东汉十三州SVG地图，标注：
- 各州轮廓与位置
- 势力颜色区分（忠汉/中立/敌对）
- 献帝当前位置（闪烁标记）
- 战况动态箭头
"""

from typing import Dict, List, Optional
import random

# ── 势力颜色 ────────────────────────────────────────────────────────────────
FACTION_COLORS = {
    "loyal": "#3b82f6",      # 忠汉派 - 蓝色
    "neutral": "#6b7280",   # 中立 - 灰色
    "hostile": "#ef4444",   # 敌对 - 红色
    "empire": "#c9a96e",    # 汉室 - 金色
    "dong_zhuo": "#7c3aed", # 董卓 - 紫色
    "default": "#9ca3af",   # 未定义 - 浅灰
}

# ── 十三州元数据 ────────────────────────────────────────────────────────────
# [name, cx, cy, width, height, rotation, power_hint]
#  cx/cy 是中心坐标（基于 900x700 viewBox，左上角为原点）
STATE_INFO: Dict[str, Dict] = {
    "司隶":    {"cx": 380, "cy": 310, "w": 90,  "h": 70,  "power_hint": "dong_zhuo"},
    "豫州":    {"cx": 460, "cy": 370, "w": 70,  "h": 60,  "power_hint": "neutral"},
    "兖州":    {"cx": 430, "cy": 260, "w": 75,  "h": 55,  "power_hint": "neutral"},
    "徐州":    {"cx": 520, "cy": 220, "w": 80,  "h": 55,  "power_hint": "neutral"},
    "青州":    {"cx": 490, "cy": 150, "w": 85,  "h": 50,  "power_hint": "neutral"},
    "荆州":    {"cx": 370, "cy": 450, "w": 90,  "h": 75,  "power_hint": "neutral"},
    "扬州":    {"cx": 580, "cy": 420, "w": 100, "h": 80,  "power_hint": "neutral"},
    "益州":    {"cx": 200, "cy": 460, "w": 110, "h": 130, "power_hint": "neutral"},
    "凉州":    {"cx": 170, "cy": 260, "w": 100, "h": 80,  "power_hint": "hostile"},
    "并州":    {"cx": 300, "cy": 230, "w": 85,  "h": 60,  "power_hint": "hostile"},
    "幽州":    {"cx": 460, "cy": 90,  "w": 110, "h": 55,  "power_hint": "neutral"},
    "冀州":    {"cx": 370, "cy": 195, "w": 80,  "h": 60,  "power_hint": "neutral"},
    "交州":    {"cx": 520, "cy": 580, "w": 100, "h": 70,  "power_hint": "neutral"},
}

# ── 州轮廓路径（简化多边形）────────────────────────────────────────────────
# 基于相对地理方位绘制的近似形状
STATE_PATHS: Dict[str, str] = {
    "司隶": "M340,280 L420,275 L430,295 L425,340 L390,355 L335,340 L330,305 Z",
    "豫州": "M420,340 L495,335 L505,365 L495,405 L430,410 L415,375 L418,348 Z",
    "兖州": "M375,225 L480,220 L490,255 L475,295 L390,295 L365,260 Z",
    "徐州": "M470,185 L580,180 L595,220 L575,265 L495,260 L465,220 Z",
    "青州": "M420,115 L555,110 L565,150 L545,185 L450,185 L410,155 Z",
    "荆州": "M295,415 L445,405 L455,445 L440,505 L390,520 L280,505 L275,450 Z",
    "扬州": "M505,375 L620,365 L640,420 L625,485 L560,495 L495,465 L490,405 Z",
    "益州": "M120,360 L280,350 L295,510 L270,590 L140,595 L100,500 L95,400 Z",
    "凉州": "M75,200 L240,190 L260,260 L245,340 L180,350 L80,320 L65,240 Z",
    "并州": "M230,180 L360,175 L375,225 L355,270 L260,268 L225,225 Z",
    "幽州": "M360,50 L560,45 L570,90 L545,140 L415,140 L350,110 L355,65 Z",
    "冀州": "M305,145 L430,140 L445,185 L425,235 L330,238 L295,200 L300,155 Z",
    "交州": "M440,500 L600,490 L620,565 L590,620 L450,620 L420,560 Z",
}

# ── 献帝都城坐标 ─────────────────────────────────────────────────────────────
CAPITAL_POSITIONS = {
    "洛阳":      {"cx": 385, "cy": 300},
    "长安":      {"cx": 200, "cy": 265},
    "许昌":      {"cx": 445, "cy": 335},
    "邺城":      {"cx": 365, "cy": 195},
    "成都":      {"cx": 190, "cy": 495},
    "健康":      {"cx": 550, "cy": 220},
    "建业":      {"cx": 575, "cy": 405},
}

# ── 诸侯势力（从db读取后的格式）─────────────────────────────────────────────
# powers: [{"name": str, "leader": str, "stance": str, "controlled_states": [str]}]
# stances: loyal / neutral / hostile


def get_state_color(state_name: str, powers: List[Dict]) -> str:
    """根据各州控制势力返回颜色。"""
    if not powers:
        return FACTION_COLORS["default"]
    # 简单查找：某势力控制的州
    for power in powers:
        controlled = power.get("controlled_states", [])
        if state_name in controlled:
            stance = power.get("stance", "neutral")
            return FACTION_COLORS.get(stance, FACTION_COLORS["default"])
    # 根据 hint 猜色
    hint = STATE_INFO.get(state_name, {}).get("power_hint", "neutral")
    return FACTION_COLORS.get(hint, FACTION_COLORS["default"])


def _build_state(state_name: str, color: str, label: str, capital: str, power: Optional[str] = None) -> str:
    """生成单个州的 SVG 元素。"""
    info = STATE_INFO.get(state_name, {"cx": 400, "cy": 300})
    cx, cy = info["cx"], info["cy"]
    path = STATE_PATHS.get(state_name, "")

    # 州名坐标
    name_x = cx
    name_y = cy + 5

    # 州名颜色（深色背景用白色文字，浅色用深色文字）
    is_dark = color.lower() in ("#7c3aed", "#ef4444", "#3b82f6")
    text_color = "#ffffff" if is_dark else "#1a1a2e"
    font_size = 11

    parts = []
    if path:
        parts.append(
            f'<path d="{path}" fill="{color}" fill-opacity="0.3" '
            f'stroke="{color}" stroke-width="1.5" stroke-opacity="0.8"/>'
        )
    parts.append(
        f'<text x="{name_x}" y="{name_y}" text-anchor="middle" '
        f'font-size="{font_size}" font-weight="bold" fill="{text_color}" '
        f'font-family="system-ui, sans-serif">{label}</text>'
    )
    if power:
        parts.append(
            f'<text x="{name_x}" y="{name_y + 13}" text-anchor="middle" '
            f'font-size="9" fill="{text_color}" fill-opacity="0.8" '
            f'font-family="system-ui, sans-serif">{power}</text>'
        )
    return "\n    ".join(parts)


def _build_emperor_marker(capital: str) -> str:
    """生成献帝当前位置闪烁标记。"""
    pos = CAPITAL_POSITIONS.get(capital, {"cx": 385, "cy": 300})
    cx, cy = pos["cx"], pos["cy"]

    # 闪烁动画的 SVG
    return f"""
    <!-- 献帝御驾标记 -->
    <circle cx="{cx}" cy="{cy}" r="12" fill="#c9a96e" fill-opacity="0.3">
        <animate attributeName="r" values="8;16;8" dur="2s" repeatCount="indefinite"/>
        <animate attributeName="fill-opacity" values="0.3;0.6;0.3" dur="2s" repeatCount="indefinite"/>
    </circle>
    <circle cx="{cx}" cy="{cy}" r="6" fill="#c9a96e" stroke="#fff" stroke-width="1.5">
        <animate attributeName="fill-opacity" values="0.8;1;0.8" dur="1.5s" repeatCount="indefinite"/>
    </circle>
    <text x="{cx}" y="{cy + 3}" text-anchor="middle" font-size="8" font-weight="bold"
          fill="#fff" font-family="system-ui, sans-serif">帝</text>
    """


def _build_legend() -> str:
    """生成图例。"""
    items = [
        ("#3b82f6", "忠汉派"),
        ("#c9a96e", "汉室"),
        ("#7c3aed", "董卓"),
        ("#ef4444", "敌对"),
        ("#6b7280", "中立"),
    ]
    labels = []
    for color, name in items:
        labels.append(
            f'<rect x="0" y="{items.index((color, name)) * 18}" width="12" height="12" '
            f'rx="2" fill="{color}" fill-opacity="0.7"/>'
            f'<text x="16" y="{items.index((color, name)) * 18 + 10}" '
            f'font-size="11" fill="#374151" font-family="system-ui, sans-serif">{name}</text>'
        )
    return f"""
    <g transform="translate(10, 10)">
        <rect x="-5" y="-5" width="75" height="{len(items) * 18 + 8}" rx="6"
              fill="#fff" fill-opacity="0.85" stroke="#e5e7eb" stroke-width="1"/>
        {"".join(labels)}
    </g>
    """


def _build_title(year: int, period: str, turn: int) -> str:
    """生成标题栏。"""
    return f"""
    <text x="450" y="28" text-anchor="middle" font-size="16" font-weight="bold"
          fill="#1a1a2e" font-family="system-ui, sans-serif">
        🏯 东汉末年局势图 · {year}年{period}月 · 第{turn}回合
    </text>
    """


def render_map_html(
    capital: str = "洛阳",
    year: int = 189,
    period: str = "春",
    turn: int = 1,
    powers: Optional[List[Dict]] = None,
) -> str:
    """生成完整 SVG 地图 HTML 字符串。

    直接塞进 Gradio HTML 组件即可渲染。
    """
    if powers is None:
        powers = []

    # ── 构建州 ──
    state_parts = []
    for state_name, info in STATE_INFO.items():
        color = get_state_color(state_name, powers)
        # 获取控制该州的势力名
        controlling_power = None
        for p in powers:
            if state_name in p.get("controlled_states", []):
                controlling_power = p.get("leader", "")[:4]
                break
        state_parts.append(_build_state(state_name, color, state_name, capital, controlling_power))

    states_svg = "\n    ".join(state_parts)

    # ── 献帝标记 ──
    emperor_marker = _build_emperor_marker(capital)

    # ── 图例 ──
    legend = _build_legend()

    # ── 标题 ──
    title = _build_title(year, period, turn)

    svg = f"""<div style="font-family:system-ui,sans-serif;background:#f8f9fa;border-radius:12px;padding:8px">
<svg viewBox="0 0 900 700" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:900px">
    <!-- 背景 -->
    <rect width="900" height="700" fill="#f0ece0" rx="8"/>
    
    <!-- 标题 -->
    {title}

    <!-- 州 -->
    {states_svg}

    <!-- 献帝标记 -->
    {emperor_marker}

    <!-- 图例 -->
    {legend}

    <!-- 边框 -->
    <rect x="2" y="2" width="896" height="696" fill="none" stroke="#c9a96e" stroke-width="3" rx="8"/>
</svg>
<p style="font-size:12px;color:#9ca3af;text-align:center;margin-top:4px">
    🟦 蓝色=忠汉  🟫 金色=汉室  🟣 紫色=董卓  🟥 红色=敌对  ⬜ 灰色=中立  |  👑 标记=献帝御驾
</p>
</div>"""

    return svg


if __name__ == "__main__":
    # 测试用
    html = render_map_html(capital="洛阳", year=189, powers=[
        {"name": "董卓", "leader": "董卓", "stance": "dong_zhuo", "controlled_states": ["司隶", "凉州"]},
        {"name": "曹操", "leader": "曹操", "stance": "neutral", "controlled_states": ["兖州", "豫州"]},
        {"name": "袁绍", "leader": "袁绍", "stance": "neutral", "controlled_states": ["冀州", "幽州"]},
        {"name": "刘表", "leader": "刘表", "stance": "loyal", "controlled_states": ["荆州"]},
    ])
    with open("/tmp/han_map_test.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Map test written to /tmp/han_map_test.html")
"""古风主题常量。L6。

汉献帝之末路 P1 升级：玄黑/朱红/古金 主题配色。
适用于 Gradio 全部 UI 组件。

Version: 0.9.4
"""

from pathlib import Path

# ── 古风配色 ────────────────────────────────────────────────────────────────
THEME = {
    # 背景
    "bg_primary":    "#0f0f1a",   # 玄黑（主背景）
    "bg_secondary":  "#1a1a2e",   # 暗青（卡片/面板）
    "bg_tertiary":   "#16213e",   # 深蓝（Tab/区域）
    "bg_hover":      "#1f1f3a",   # 悬停高亮

    # 边框
    "border":        "#2d2d44",   # 边框线
    "border_accent": "#c9a96e",   # 金色强调边框

    # 文字
    "text_primary":  "#e8d5b7",   # 暖白（主文字）
    "text_secondary":"#9ca3af",   # 灰（次要文字）
    "text_muted":    "#6b7280",   # 暗灰（禁用）
    "text_accent":   "#c9a96e",   # 古金（强调）

    # 强调色
    "accent_red":    "#8b0000",   # 朱红（危机/重要）
    "accent_gold":   "#c9a96e",   # 古金（标题/装饰）
    "accent_blue":   "#3b82f6",   # 忠蓝（忠诚）
    "accent_green":  "#22c55e",   # 成功
    "accent_amber":  "#f59e0b",   # 警告

    # 按钮
    "btn_primary":   "#8b0000",   # 朱红主按钮
    "btn_secondary": "#2d2d44",   # 次要按钮
    "btn_text":      "#e8d5b7",   # 按钮文字
}

# ── 古风字体 ────────────────────────────────────────────────────────────────
FONTS = {
    "heading": "'Noto Serif SC', 'SimSun', serif",
    "body":    "'Noto Sans SC', 'Microsoft YaHei', sans-serif",
    "mono":    "'Fira Code', 'Courier New', monospace",
}

# ── 完整 CSS（注入 Gradio theme）─────────────────────────────────────────────
CUSTOM_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Noto+Sans+SC:wght@300;400;500;600&display=swap');

/* ── 全局基础 ── */
.gradio-container {{
    background-color: {THEME["bg_primary"]} !important;
    font-family: {FONTS["body"]} !important;
}}

/* ── Markdown 标题 ── */
h1, h2, h3, h4 {{
    color: {THEME["accent_gold"]} !important;
    font-family: {FONTS["heading"]} !important;
    border-bottom: 1px solid {THEME["border"]};
    padding-bottom: 4px;
}}

/* ── 主标题特殊处理 ── */
h1 {{ font-size: 1.8rem !important; color: {THEME["accent_gold"]} !important; }}
h2 {{ font-size: 1.3rem !important; }}
h3 {{ font-size: 1.1rem !important; }}

/* ── 按钮 ── */
button {{
    background-color: {THEME["bg_tertiary"]} !important;
    color: {THEME["text_primary"]} !important;
    border: 1px solid {THEME["border_accent"]} !important;
    border-radius: 6px !important;
    font-family: {FONTS["body"]} !important;
    transition: all 0.2s;
}}

button:hover {{
    background-color: {THEME["bg_hover"]} !important;
    border-color: {THEME["accent_gold"]} !important;
}}

button.primary {{
    background-color: {THEME["btn_primary"]} !important;
    color: {THEME["btn_text"]} !important;
    border-color: {THEME["accent_gold"]} !important;
}}

button.primary:hover {{
    background-color: #a50000 !important;
}}

/* ── Tab 样式 ── */
.tab-nav {{
    background-color: {THEME["bg_secondary"]} !important;
}}

.tab-nav button {{
    background-color: {THEME["bg_secondary"]} !important;
    color: {THEME["text_secondary"]} !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
}}

.tab-nav button.selected {{
    color: {THEME["accent_gold"]} !important;
    border-bottom: 2px solid {THEME["accent_gold"]} !important;
}}

/* ── 输入框 ── */
input, textarea, select {{
    background-color: {THEME["bg_secondary"]} !important;
    color: {THEME["text_primary"]} !important;
    border: 1px solid {THEME["border"]} !important;
    border-radius: 6px !important;
    font-family: {FONTS["body"]} !important;
}}

input:focus, textarea:focus, select:focus {{
    border-color: {THEME["accent_gold"]} !important;
    outline: none !important;
}}

/* ── HTML 组件背景 ── */
.generated_html {{
    background-color: {THEME["bg_secondary"]} !important;
    border-radius: 8px !important;
    padding: 12px !important;
    border: 1px solid {THEME["border"]} !important;
}}

/* ── Markdown 输出 ── */
.markdown {{
    background-color: {THEME["bg_secondary"]} !important;
    border-radius: 8px !important;
    padding: 12px !important;
    color: {THEME["text_primary"]} !important;
}}

/* ── 表格 ── */
table {{
    background-color: {THEME["bg_secondary"]} !important;
    border-color: {THEME["border"]} !important;
    color: {THEME["text_primary"]} !important;
    font-family: {FONTS["body"]} !important;
}}

th {{
    background-color: {THEME["bg_tertiary"]} !important;
    color: {THEME["accent_gold"]} !important;
    font-family: {FONTS["heading"]} !important;
    border-color: {THEME["border"]} !important;
}}

td {{
    border-color: {THEME["border"]} !important;
}}

/* ── 进度条 ── */
.prose {{
    background-color: {THEME["bg_secondary"]} !important;
    border-radius: 8px !important;
    padding: 16px !important;
}}

/* ── Footer/空状态 ── */
p:empty::before, .empty {{
    color: {THEME["text_muted"]} !important;
}}

/* ── 滚动条 ── */
::-webkit-scrollbar {{
    width: 6px;
    height: 6px;
}}
::-webkit-scrollbar-track {{
    background: {THEME["bg_primary"]};
}}
::-webkit-scrollbar-thumb {{
    background: {THEME["border"]};
    border-radius: 3px;
}}
::-webkit-scrollbar-thumb:hover {{
    background: {THEME["accent_gold"]};
}}
"""

def get_theme_css() -> str:
    """返回完整CSS字符串，可直接传入gr.Blocks(css=...)"""
    return CUSTOM_CSS
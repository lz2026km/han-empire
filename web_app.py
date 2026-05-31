"""汉献帝之末路 Gradio Web 交互界面。L9。V0.9.6 Step3：界面美化 + 威权恢复 + 诏书预览。

布局：左侧状态栏(260px) + 中央Tab内容 + 右侧快捷操作(260px)，固定1200px。
主题：玄黑/朱红/古金古风主题。
"""

import uuid
import sys
from pathlib import Path
from typing import Dict, List

import gradio as gr

sys.path.insert(0, str(Path(__file__).parent))
from han_sim.content import load_game_content
from han_sim.db import GameDB
from han_sim.decree import issue_decree
from han_sim.llm_config import load_llm_config
from han_sim.models import GameState, get_authority_level
from han_sim.paths import user_data_path
from han_sim.session import GameSession
from han_sim.conversation import get_recent_exchanges
from han_sim.simulation import run_monthly_simulation
from han_sim.map_view import render_map_html as _render_svg_map
from han_sim.portraits import render_avatar_grid_html, render_portrait_with_name_html
from han_sim.theme import get_theme_css, THEME
from han_sim.flows import AUTHORITY_RECOVERY_ACTIONS, execute_authority_recovery


# ── API Key ───────────────────────────────────────────────────────────────
def _get_api_key() -> str:
    key_path = Path.home() / ".hermes-agent" / ".minimax-key.json"
    if key_path.exists():
        import json
        with open(key_path) as f:
            d = json.load(f)
            return d.get("apiKey", "")
    return ""


# ── 帮助文本 ────────────────────────────────────────────────────────────
HELP = """
**游戏目标**：在东汉末年的乱局中复兴汉室。

**游戏机制**：
- 每月有两个阶段：**召见大臣** 和 **月末推演**
- **召见大臣**：向大臣询问局势、寻求建议
- **拟旨**：针对某种意图（如"赈济灾民"）生成诏书并下达
- **威权恢复**：通过特定行动恢复天子威权
- **月末推演**：推进时间，结算财政和事件，触发历史事件

**指标说明**：
- 汉室库：财政收入（万两/月）
- 声望：汉室民心（0-100）
- 威权：天子威权（0-100），越高则诏书效果越好
- 藩镇：藩镇割据程度（越低越好，0=完全统一）
"""

DECREE_TYPES = [
    "赈济灾民", "减免赋税", "颁布罪己诏", "提拔贤才", "整饬吏治",
    "军事调度", "外交安抚", "流通铜钱", "改革税制", "召集兵马",
    "衣带密诏", "献帝东归",
]


# ── 装饰性 SVG ──────────────────────────────────────────────────────────
DIVIDER_SVG = """
<div style="text-align:center;margin:8px 0;opacity:0.6">
<svg width="200" height="12" viewBox="0 0 200 12" xmlns="http://www.w3.org/2000/svg">
<line x1="0" y1="6" x2="80" y2="6" stroke="#c9a96e" stroke-width="1"/>
<circle cx="100" cy="6" r="4" fill="none" stroke="#c9a96e" stroke-width="1"/>
<line x1="120" y1="6" x2="200" y2="6" stroke="#c9a96e" stroke-width="1"/>
</svg>
</div>
"""

TITLE_BANNER = """
<div style="background:linear-gradient(135deg,#1a1a2e 0%,#2d1f1f 50%,#1a1a2e 100%);
            border-bottom:2px solid #c9a96e;padding:20px 24px;text-align:center;
            position:relative;overflow:hidden">
    <div style="position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,#c9a96e,transparent);opacity:0.5"></div>
    <h1 style="color:#c9a96e;margin:0;font-size:2rem;font-family:serif;text-shadow:0 0 20px rgba(201,169,110,0.3)">
        👑 汉献帝之末路
    </h1>
    <p style="color:#9ca3af;margin:8px 0 0;font-size:14px">
        189年，董卓进京，废少帝立献帝。名为天子，实为阶下囚。
    </p>
    <div style="position:absolute;bottom:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,#c9a96e,transparent);opacity:0.3"></div>
</div>
"""


# ── 会话状态管理 ────────────────────────────────────────────────────────
class GameUI:
    def __init__(self):
        self.session: GameSession = None
        self.decree_log: list = []

    def new_game(self, campaign_id: str = ""):
        cid = campaign_id.strip() or str(uuid.uuid4())[:8]
        content = load_game_content()
        self.session = GameSession.new(cid, content)
        self.decree_log = []
        return self._render_state()

    def _bar(self, value: int, total: int = 100, width: int = 10) -> str:
        """渲染进度条。"""
        filled = max(0, min(width, int(value / total * width)))
        empty = width - filled
        return "▓" * filled + "░" * empty

    def _render_state(self) -> str:
        s = self.session.state
        authority = s.metrics.get('威权', 0)
        auth_level = get_authority_level(authority)
        auth_icon = "🔴" if authority >= 80 else ("🟡" if authority >= 50 else ("🟠" if authority >= 20 else "⚫"))
        lines = [
            f"**【{s.year}年{s.period}月 · 第{s.turn}回合 · {s.capital}】**",
            "",
            f"📦 汉室库：{s.metrics.get('汉室库', 0)}万两",
            f"💰 内库：{s.metrics.get('内库', 0)}万两",
            f"⭐ 声望：{s.metrics.get('声望', 0)}/100",
            f"{auth_icon} 威权：{authority}/100 — {auth_level.label}",
            f"⚔️  藩镇：{s.metrics.get('藩镇', 0)}/100",
            "",
        ]
        return "\n".join(lines)

    def _render_dashboard_html(self) -> str:
        """【总览】仪表盘 HTML：数值卡片 + 历史线进度 + 活跃事项。"""
        s = self.session.state
        authority = s.metrics.get('威权', 0)
        auth_level = get_authority_level(authority)
        shengwang = s.metrics.get('声望', 0)
        fanzhen = s.metrics.get('藩镇', 0)
        han_ku = s.metrics.get('汉室库', 0)
        nei_ku = s.metrics.get('内库', 0)

        auth_color = "#ef4444" if authority < 20 else ("#f59e0b" if authority < 50 else "#3b82f6")
        auth_bg = "#2d1f1f" if authority < 20 else ("#2d2a1a" if authority < 50 else "#1a2d2d")

        dong_trapped = s.dong_zhuo_trapped_turn > 0 and s.dong_zhuo_killed_turn == 0
        dong_killed = s.dong_zhuo_killed_turn > 0
        dong_pct = 100 if dong_killed else (20 if dong_trapped else 0)
        dong_label = "已伏诛 ✓" if dong_killed else ("围困中" if dong_trapped else "未触发")
        dong_color = "#22c55e" if dong_killed else ("#f59e0b" if dong_trapped else "#6b7280")

        escape_done = s.emperor_safe_turn > 0
        escape_ongoing = s.emperor_escaped_turn > 0 and not escape_done
        if escape_done:
            esc_pct = 100
            esc_label = "已东归 ✓"
            esc_color = "#22c55e"
        elif escape_ongoing:
            esc_turns = s.turn - s.emperor_escaped_turn
            esc_pct = min(100, int((esc_turns / 5) * 100))
            esc_label = f"逃难中 {esc_turns}/5回合"
            esc_color = "#f59e0b"
        else:
            esc_pct = 0
            esc_label = "未触发"
            esc_color = "#6b7280"

        issues = self.session.db.get_active_issues()
        issues_html = ""
        if issues:
            for iss in issues[:6]:
                pct = int(iss.get("bar_value", 0))
                sev = iss.get("severity", 50)
                sev_color = "#ef4444" if sev >= 70 else "#f59e0b" if sev >= 40 else "#6b7280"
                issues_html += f"""<tr>
                    <td style="color:{sev_color};font-weight:bold;font-size:12px">{iss.get('title','')[:14]}</td>
                    <td style="padding:2px 4px">{self._bar(pct)} {pct}%</td>
                    <td style="color:{sev_color};font-size:12px;text-align:center">{sev}</td>
                </tr>"""
        else:
            issues_html = "<tr><td colspan=3 style='color:#6b7280;font-size:12px'>本回合无活跃事项</td></tr>"

        # 威权恢复行动可用列表
        recovery_actions = auth_level.recovery_actions
        recovery_html = ""
        if recovery_actions:
            action_labels = {
                "求情示弱": "🔓", "笼络近臣": "💰", "施恩示好": "🎁",
                "朝会演讲": "📢", "处理政务": "📋", "颁布诏书": "📜",
                "召见贤才": "👤", "整饬吏治": "⚖️", "祭天祈福": "🙏",
                "军事演练": "⚔️", "册封功臣": "🏅", "颁布罪己诏": "📃",
                "大赦天下": "🌍"
            }
            for act in recovery_actions[:6]:
                icon = action_labels.get(act, "•")
                cost = AUTHORITY_RECOVERY_ACTIONS.get(act, {}).get("cost", 0)
                cost_str = f"({cost}万两)" if cost > 0 else "(免费)"
                recovery_html += f"""<button onclick="this.parentElement.querySelector('.recovery-action-input').value='{act}'" 
                    style="margin:2px;padding:3px 8px;font-size:11px;background:#16213e;color:#e8d5b7;border:1px solid #c9a96e;border-radius:4px;cursor:pointer">{icon}{act}{cost_str}</button>"""

        return f"""<div style="font-family:system-ui,sans-serif">
        <!-- 威权状态卡 -->
        <div style="background:{auth_bg};border:1px solid {auth_color};border-radius:8px;padding:10px;margin-bottom:10px;text-align:center">
            <div style="font-size:11px;color:#9ca3af">当前威权</div>
            <div style="font-size:28px;font-weight:bold;color:{auth_color}">{authority}</div>
            <div style="font-size:12px;color:{auth_color};font-weight:bold">{auth_level.label}</div>
            <div style="font-size:11px;color:#9ca3af;margin-top:4px">诏书效果：{auth_level.decree_mult:.0%} · 召对效果：{auth_level.summon_mult:.0%}</div>
        </div>

        <table style="width:100%;border-collapse:collapse;margin-bottom:8px">
            <tr>
                <td style="padding:8px;border:1px solid #2d2d44;text-align:center;background:#1a1a2e">
                    <div style="font-size:11px;color:#9ca3af">汉室库</div>
                    <div style="font-size:22px;font-weight:bold;color:#c9a96e">{han_ku}</div>
                    <div style="font-size:10px;color:#6b7280">万两</div>
                </td>
                <td style="padding:8px;border:1px solid #2d2d44;text-align:center;background:#1a1a2e">
                    <div style="font-size:11px;color:#9ca3af">内库</div>
                    <div style="font-size:22px;font-weight:bold;color:#c9a96e">{nei_ku}</div>
                    <div style="font-size:10px;color:#6b7280">万两</div>
                </td>
                <td style="padding:8px;border:1px solid #2d2d44;text-align:center;background:#1a1a2e">
                    <div style="font-size:11px;color:#9ca3af">声望</div>
                    <div style="font-size:22px;font-weight:bold;color:#22c55e">{shengwang}</div>
                    <div style="font-size:10px">{self._bar(shengwang)}</div>
                </td>
            </tr>
            <tr>
                <td style="padding:8px;border:1px solid #2d2d44;text-align:center;background:#1a1a2e">
                    <div style="font-size:11px;color:#9ca3af">藩镇</div>
                    <div style="font-size:22px;font-weight:bold;color:#ef4444">{fanzhen}</div>
                    <div style="font-size:10px">{self._bar(fanzhen)}</div>
                </td>
                <td colspan="2" style="padding:8px;border:1px solid #2d2d44;background:#1a1a2e;text-align:center">
                    <div style="font-size:11px;color:#9ca3af">威权诏书倍率</div>
                    <div style="font-size:18px;font-weight:bold;color:{auth_color}">{auth_level.decree_mult:.0%}</div>
                </td>
            </tr>
        </table>

        <h4 style="margin:10px 0 4px;color:#c9a96e;font-size:13px">📜 历史线进度</h4>
        <table style="width:100%;border-collapse:collapse;font-size:12px">
            <tr>
                <td style="padding:3px 6px;color:#e8d5b7">董卓伏诛</td>
                <td style="padding:3px 6px">{self._bar(dong_pct)}</td>
                <td style="padding:3px 6px;color:{dong_color};font-weight:bold">{dong_label}</td>
            </tr>
            <tr>
                <td style="padding:3px 6px;color:#e8d5b7">献帝东归</td>
                <td style="padding:3px 6px">{self._bar(esc_pct)}</td>
                <td style="padding:3px 6px;color:{esc_color};font-weight:bold">{esc_label}</td>
            </tr>
        </table>

        <h4 style="margin:10px 0 4px;color:#c9a96e;font-size:13px">📋 待办事项</h4>
        <table style="width:100%;border-collapse:collapse;font-size:12px">
            <tr style="background:#16213e">
                <th style="padding:3px 6px;text-align:left;color:#c9a96e;font-size:11px">事项</th>
                <th style="padding:3px 6px;text-align:left;color:#c9a96e;font-size:11px">进度</th>
                <th style="padding:3px 6px;text-align:center;color:#c9a96e;font-size:11px">严重度</th>
            </tr>
            {issues_html}
        </table>

        {DIVIDER_SVG}
        <h4 style="margin:8px 0 4px;color:#c9a96e;font-size:12px">🆕 威权恢复行动（当前可用）</h4>
        <div style="font-size:11px;color:#9ca3af;margin-bottom:4px">点击按钮选择，然后点击「执行恢复」</div>
        <div style="margin-bottom:6px" class="recovery-buttons">{recovery_html}</div>
        """

    def _render_powers_html(self) -> str:
        """【势力】势力视图 HTML，按 stance 着色。"""
        powers = self.session.db.list_powers()
        colors = {"loyal": "#3b82f6", "neutral": "#6b7280", "hostile": "#ef4444"}
        labels = {"loyal": "忠", "neutral": "中", "hostile": "敌"}
        rows = []
        for p in powers:
            color = colors.get(p.get("stance", "neutral"), "#6b7280")
            badge = labels.get(p.get("stance", "neutral"), "?")
            mil = p.get('military_strength', 0)
            lev = p.get('leverage', 0)
            mil_bar = self._bar(int(mil) // 5, 100, 10) if mil else "░░░░░░░░░░"
            rows.append(f"""<tr style="color:{color}">
                <td style="padding:5px 6px;font-weight:bold;font-size:13px">{p.get('name','?')}</td>
                <td style="padding:5px 6px;font-size:12px">{p.get('leader','?')}</td>
                <td style="padding:5px 6px;text-align:center"><span style="background:{color}22;padding:1px 6px;border-radius:4px;font-size:11px">{badge}</span></td>
                <td style="padding:5px 6px;font-size:11px;color:#22c55e">{mil_bar}</td>
                <td style="padding:5px 6px;text-align:right;font-size:12px">{mil}</td>
                <td style="padding:5px 6px;text-align:right;font-size:12px">{lev}</td>
            </tr>""")

        header = """<tr style="background:#16213e;font-size:11px">
            <th style="padding:5px 6px;text-align:left;color:#c9a96e">势力</th>
            <th style="padding:5px 6px;text-align:left;color:#c9a96e">首领</th>
            <th style="padding:5px 6px;text-align:center;color:#c9a96e">立场</th>
            <th style="padding:5px 6px;text-align:left;color:#c9a96e">军力</th>
            <th style="padding:5px 6px;text-align:right;color:#c9a96e">军</th>
            <th style="padding:5px 6px;text-align:right;color:#c9a96e">威</th>
        </tr>"""

        return f"""<div style="font-family:system-ui,sans-serif">
        <table style="width:100%;border-collapse:collapse;font-size:13px">
            {header}
            {"".join(rows)}
        </table>
        <p style="font-size:11px;color:#9ca3af;margin-top:8px">
            🟦 忠 · 🟪 中立 · 🟥 敌对 · 军力/威势越高威胁越大
        </p>
        </div>"""

    def _render_ministers(self):
        """在朝大臣列表：带头像网格视图。"""
        ministers = self.session.get_active_ministers()
        if not ministers:
            return "<p style='color:#9ca3af;text-align:center'>无可用大臣</p>"
        return render_avatar_grid_html(ministers, cols=4, size=72)

    def _render_history(self):
        """召对历史：最近10回合。"""
        if not self.session:
            return "_暂无召对记录_"
        rows = self.session.db.conn.execute(
            """SELECT turn, period, role, content, minister_name
               FROM conversation_history
               WHERE campaign_id=?
               ORDER BY id DESC LIMIT 40""",
            (self.session.campaign_id,),
        ).fetchall()
        if not rows:
            return "_暂无召对记录_"
        by_turn: Dict[tuple, Dict] = {}
        for row in reversed(rows):
            turn, period, role, content, minister = row[0], row[1], row[2], row[3], row[4]
            key = (turn, period)
            if key not in by_turn:
                by_turn[key] = {"emperor": "", "minister": "", "minister_name": minister}
            if role == "emperor":
                by_turn[key]["emperor"] = content[:80]
            elif role == "minister":
                by_turn[key]["minister"] = content[:80]
        lines = ["**【召对历史】**", ""]
        for (turn, period), data in sorted(by_turn.items(), key=lambda x: x[0][0], reverse=True)[:10]:
            lines.append(f"**第{turn}回合 · {period}月**")
            if data["emperor"]:
                lines.append(f"👤 天子：{data['emperor']}…")
            if data["minister"]:
                lines.append(f"🏛️ {data['minister_name']}：{data['minister']}…")
            lines.append("")
        return "\n".join(lines)

    def _render_log(self):
        """游戏日志：最近20条。"""
        if not self.session:
            return "_暂无日志_"
        rows = self.session.db.get_recent_log(limit=20)
        if not rows:
            return "_暂无日志_"
        lines = ["**【游戏日志】**", ""]
        for row in rows:
            lines.append(f"第{row['turn']}回合 {row['phase']}：{row['entry'][:60]}")
        return "\n".join(lines)

    def _render_map_html(self) -> str:
        """【🗺️ 地图】SVG 十三州地图。"""
        if not self.session:
            return "<p style='text-align:center;color:#9ca3af;padding:40px'>请先点击「新游戏」初始化</p>"

        s = self.session.state
        capital = getattr(s, 'capital', '洛阳')
        year = getattr(s, 'year', 189)
        period = getattr(s, 'period', '春')
        turn = getattr(s, 'turn', 1)

        powers_raw = self.session.db.list_powers()
        powers = []
        for p in powers_raw:
            regions = self.session.db.list_regions()
            controlled = []
            for r in regions:
                if r.get("controlled_by", "") == p.get("id", ""):
                    rid = r.get("id", "")
                    name_map = {
                        "司隶": "司隶", "youzhou": "幽州", "bingzhou": "并州", "yanzhou": "兖州",
                        "yuzhou": "豫州", "jiujiang": "扬州", "jingzhou": "荆州",
                        "yizhou": "益州", "liangzhou": "凉州", "silu": "司隶",
                    }
                    controlled.append(name_map.get(rid, rid))
            powers.append({
                "name": p.get("name", ""),
                "leader": p.get("leader", ""),
                "stance": p.get("stance", "neutral"),
                "controlled_states": controlled,
            })

        return _render_svg_map(capital=capital, year=year, period=period, turn=turn, powers=powers)

    def _render_intel_html(self) -> str:
        """【情报】视图 HTML：军力排行 + 联盟关系 + 密探情报（威权≥40解锁）。"""
        if not self.session:
            return "<p>请先点击「新游戏」初始化</p>"
        from han_sim.tools import (
            estimate_military_strength, inspect_warlord_alliances,
            check_dongzhuo_trap_status, audit_imperial_treasury,
        )

        s = self.session.state
        db = self.session.db
        authority = s.metrics.get("威权", 0)
        auth_level = get_authority_level(authority)
        intel_unlocked = authority >= 40

        powers = db.list_powers()
        sorted_powers = sorted(
            [p for p in powers if p.get("id") != "han"],
            key=lambda x: int(x.get("military_strength", 0)), reverse=True,
        )
        max_mil = max(int(p.get("military_strength", 0)) for p in sorted_powers) if sorted_powers else 100

        rows_html = []
        for p in sorted_powers[:8]:
            mil = int(p.get("military_strength", 0))
            lev = int(p.get("leverage", 0))
            bar_len = max(1, int(mil / max_mil * 20)) if max_mil else 0
            bar = "█" * bar_len + "░" * (20 - bar_len)
            stance_color = {"loyal": "#3b82f6", "neutral": "#6b7280", "hostile": "#ef4444"}.get(p.get("stance", "neutral"), "#6b7280")
            rows_html.append(f"""<tr style="color:{stance_color}">
                <td style="padding:4px 8px;font-weight:bold">{p.get('name','')}</td>
                <td style="padding:4px 8px;font-family:monospace;color:#22c55e">{bar}</td>
                <td style="padding:4px 8px;text-align:right">{mil}</td>
                <td style="padding:4px 8px;text-align:right">{lev}</td>
            </tr>""")

        trap_status = check_dongzhuo_trap_status(s)
        trap_desc = trap_status.get("description", "")
        trap_color = "#22c55e" if trap_status.get("status") == "伏诛成功" else ("#f59e0b" if trap_status.get("status") == "围困中" else "#6b7280")

        treasury = audit_imperial_treasury(db, s)
        han_ku = treasury.get("汉室库", 0)
        nei_ku = treasury.get("内库", 0)

        return f"""<div style="font-family:system-ui,sans-serif">
        <h4 style="margin:8px 0 4px;color:#c9a96e">⚔️ 诸侯军力排行</h4>
        <table style="width:100%;border-collapse:collapse;font-size:13px">
            <tr style="background:#16213e;font-size:12px">
                <th style="padding:4px 8px;text-align:left;color:#c9a96e">势力</th>
                <th style="padding:4px 8px;text-align:left;color:#c9a96e">军力条</th>
                <th style="padding:4px 8px;text-align:right;color:#c9a96e">军力</th>
                <th style="padding:4px 8px;text-align:right;color:#c9a96e">威势</th>
            </tr>
            {"".join(rows_html)}
        </table>
        <h4 style="margin:12px 0 4px;color:#c9a96e">🕵️ 情报摘要</h4>
        <p style='font-size:13px'>{'🔓 密探已解锁（威权≥40）' if intel_unlocked else f'🔒 密探未解锁（威权需≥40，当前{authority}）'}</p>
        <p style='font-size:13px'>📍 董卓伏诛线：<span style='color:{trap_color}'>{trap_desc}</span></p>
        <p style='font-size:13px'>💰 汉室库：{han_ku}万两 · 内库：{nei_ku}万两</p>
        <p style="font-size:12px;color:#9ca3af">🟦 忠诚 · 🟪 中立 · 🟥 敌对</p>
        </div>"""

    def _render_diary_html(self) -> str:
        """【日记】天子日记视图。"""
        if not self.session:
            return "<p>请先点击「新游戏」初始化</p>"
        entries = self.session.db.list_diary(self.session.campaign_id, limit=15)
        if not entries:
            return "<p style='color:#9ca3af'>暂无天子日记</p>"
        lines = []
        for e in entries:
            turn = e.get("turn", 0)
            year = e.get("year", 0)
            period = e.get("period", 0)
            content = e.get("content", "")
            lines.append(f"<p style='margin:4px 0;font-size:13px'><b>第{turn}回合 · {year}年{period}月</b>：{content[:80]}</p>")
        return f"""<div style="font-family:system-ui,sans-serif">
        <h4 style="margin:8px 0 6px;color:#c9a96e">📖 天子日记</h4>
        {"".join(lines)}
        </div>"""

    def _render_escape_html(self) -> str:
        """【献帝东归】东归系统HTML：当前状态+执行按钮+倒计时。"""
        if not self.session:
            return "<p>请先点击「新游戏」初始化</p>"
        s = self.session.state
        escaped = s.emperor_escaped_turn > 0
        safe = s.emperor_safe_turn > 0

        if safe:
            status_html = f"""<div style="background:#1a3d1a;border:1px solid #22c55e;border-radius:8px;padding:16px;text-align:center">
                <div style="font-size:32px">✅</div>
                <div style="font-size:20px;font-weight:bold;color:#22c55e">献帝已成功东归</div>
                <div style="font-size:13px;color:#9ca3af;margin-top:4px">第{safe}回合抵达许昌，汉室重光</div>
            </div>"""
        elif escaped:
            turns = s.turn - s.emperor_escaped_turn
            left = max(0, 5 - turns)
            status_html = f"""<div style="background:#3d2a1a;border:1px solid #f59e0b;border-radius:8px;padding:16px;text-align:center">
                <div style="font-size:32px">🚗</div>
                <div style="font-size:20px;font-weight:bold;color:#f59e0b">献帝东归中</div>
                <div style="font-size:14px;color:#e8d5b7;margin-top:4px">剩余 <span style="color:#ef4444;font-weight:bold">{left}</span> 回合</div>
            </div>"""
        else:
            dong_killed = s.dong_zhuo_killed_turn > 0
            hint = "董卓已伏诛，可以东归" if dong_killed else "❌ 需先完成董卓伏诛"
            status_html = f"""<div style="background:#2d1f1f;border:1px solid #ef4444;border-radius:8px;padding:16px;text-align:center">
                <div style="font-size:32px">🏰</div>
                <div style="font-size:18px;font-weight:bold;color:#ef4444">献帝困于长安</div>
                <div style="font-size:13px;color:#9ca3af;margin-top:4px">{hint}</div>
            </div>"""

        return f"""<div style="font-family:system-ui,sans-serif">
        {status_html}

        <h4 style="margin:12px 0 6px;color:#c9a96e">📜 东归机制</h4>
        <table style="width:100%;border-collapse:collapse;font-size:13px;background:#1a1a2e;border-radius:6px">
            <tr style="background:#16213e">
                <th style="padding:8px 12px;text-align:left;color:#c9a96e">项目</th>
                <th style="padding:8px 12px;text-align:left;color:#c9a96e">说明</th>
            </tr>
            <tr>
                <td style="padding:6px 12px;color:#e8d5b7;font-weight:bold">触发条件</td>
                <td style="padding:6px 12px;color:#9ca3af">董卓伏诛后（威权>=60成功率80%，<60成功率50%）</td>
            </tr>
            <tr>
                <td style="padding:6px 12px;color:#e8d5b7;font-weight:bold">成功效果</td>
                <td style="padding:6px 12px;color:#22c55e">威权+15，声望+10（威权>=60）</td>
            </tr>
            <tr>
                <td style="padding:6px 12px;color:#e8d5b7;font-weight:bold">失败效果</td>
                <td style="padding:6px 12px;color:#ef4444">威权-10，声望-5，超期5回合则东归失败</td>
            </tr>
        </table>
        """

    def _render_dongzhuo_html(self) -> str:
        """【讨伐董卓】董卓伏诛线HTML：当前状态+触发条件+执行按钮。"""
        if not self.session:
            return "<p>请先点击「新游戏」初始化</p>"
        s = self.session.state
        trapped = s.dong_zhuo_trapped_turn > 0 and s.dong_zhuo_killed_turn == 0
        killed = s.dong_zhuo_killed_turn > 0
        authority = s.metrics.get("威权", 0)

        if killed:
            status_html = """<div style="background:#1a3d1a;border:1px solid #22c55e;border-radius:8px;padding:16px;text-align:center">
                <div style="font-size:32px">✅</div>
                <div style="font-size:20px;font-weight:bold;color:#22c55e">董卓已伏诛</div>
                <div style="font-size:13px;color:#9ca3af;margin-top:4px">第{s.dong_zhuo_killed_turn}回合，天子重光汉室</div>
            </div>"""
        elif trapped:
            turns_left = 6 - (s.turn - s.dong_zhuo_trapped_turn)
            status_html = f"""<div style="background:#3d2a1a;border:1px solid #f59e0b;border-radius:8px;padding:16px;text-align:center">
                <div style="font-size:32px">🔥</div>
                <div style="font-size:20px;font-weight:bold;color:#f59e0b">董卓被围困中</div>
                <div style="font-size:14px;color:#e8d5b7;margin-top:4px">剩余<span style="color:#ef4444;font-weight:bold">{turns_left}</span>回合需完成伏诛</div>
                <div style="font-size:12px;color:#9ca3af;margin-top:4px">威权：{authority}（≥60时所需军力-10）</div>
            </div>"""
        else:
            status_html = f"""<div style="background:#2d1f1f;border:1px solid #ef4444;border-radius:8px;padding:16px;text-align:center">
                <div style="font-size:32px">⚔️</div>
                <div style="font-size:18px;font-weight:bold;color:#ef4444">董卓肆虐中</div>
                <div style="font-size:13px;color:#9ca3af;margin-top:4px">威权：{authority}（需≥40触发伏诛线）</div>
                <div style="font-size:12px;color:#9ca3af;margin-top:4px">诸侯联军军力≥{40 - (10 if authority >= 60 else (5 if authority >= 40 else 0))}方可伏诛</div>
            </div>"""

        return f"""<div style="font-family:system-ui,sans-serif">
        {status_html}

        <h4 style="margin:12px 0 6px;color:#c9a96e">📜 董卓伏诛机制</h4>
        <table style="width:100%;border-collapse:collapse;font-size:13px;background:#1a1a2e;border-radius:6px">
            <tr style="background:#16213e">
                <th style="padding:8px 12px;text-align:left;color:#c9a96e">项目</th>
                <th style="padding:8px 12px;text-align:left;color:#c9a96e">说明</th>
            </tr>
            <tr>
                <td style="padding:6px 12px;color:#e8d5b7;font-weight:bold">触发条件</td>
                <td style="padding:6px 12px;color:#9ca3af">威权≥40即可触发伏诛线</td>
            </tr>
            <tr>
                <td style="padding:6px 12px;color:#e8d5b7;font-weight:bold">成功条件</td>
                <td style="padding:6px 12px;color:#9ca3af">联军军力 ≥ 40（威权≥60时-10）</td>
            </tr>
            <tr>
                <td style="padding:6px 12px;color:#e8d5b7;font-weight:bold">失败惩罚</td>
                <td style="padding:6px 12px;color:#ef4444">威权-10，声望-5，超期6回合则游戏失败</td>
            </tr>
            <tr>
                <td style="padding:6px 12px;color:#e8d5b7;font-weight:bold">成功奖励</td>
                <td style="padding:6px 12px;color:#22c55e">威权+30，声望+20，藩镇-15，汉室库+50</td>
            </tr>
        </table>

        <h4 style="margin:12px 0 6px;color:#c9a96e">⚔️ 执行伏诛</h4>
        <div style="font-size:12px;color:#9ca3af;margin-bottom:8px">
            输入联军总军力（包含诸侯联军+天子兵马），点击「执行伏诛」进行判定
        </div>
        """

    def _render_faction_html(self) -> str:
        """【派系】朝堂派系HTML：四大派系影响力+趋势。"""
        if not self.session:
            return "<p>请先点击「新游戏」初始化</p>"
        from han_sim.models import get_faction_status, FACTION_META, init_faction_influence
        state = self.session.state
        if "faction_influence" not in state.metrics:
            init_faction_influence(state)
        faction_status = get_faction_status(state)

        header = f"""<div style="background:#1a2d1a;border:1px solid #22c55e;border-radius:8px;padding:12px;margin-bottom:12px">
            <span style="font-size:16px;font-weight:bold;color:#c9a96e">⚖️ 朝堂派系</span>
        </div>"""

        trend_icons = {"rising": "📈", "stable": "➡️", "declining": "📉"}
        faction_cards = ""
        for faction, info in faction_status.items():
            meta = FACTION_META.get(faction, {})
            color = meta.get("color", "#9ca3af")
            inf = info["influence"]
            trend = info["trend"]
            icon = trend_icons.get(trend, "➡️")

            # Progress bar
            bar = f"""<div style="background:#2d2d44;border-radius:4px;height:8px;width:100%;margin-top:4px">
                <div style="background:{color};border-radius:4px;height:8px;width:{inf}%;transition:width 0.3s"></div>
            </div>"""

            faction_cards += f"""<div style="background:#1a1a2e;border-radius:8px;padding:12px;margin-bottom:8px;border-left:3px solid {color}">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="font-size:15px;font-weight:bold;color:{color}">{faction}</span>
                    <span style="font-size:18px;font-weight:bold;color:#e8d5b7">{inf}<span style="font-size:11px;color:#9ca3af">/100 {icon}</span></span>
                </div>
                {bar}
                <div style="font-size:11px;color:#9ca3af;margin-top:4px">{meta.get('description', '')}</div>
            </div>"""

        return header + faction_cards

    def _render_decree_html(self) -> str:
        """【诏令】诏令状态机HTML：有效诏书+过期诏书+可发类型。"""
        if not self.session:
            return "<p>请先点击「新游戏」初始化</p>"
        from han_sim.flows import get_decree_dashboard
        state = self.session.state
        dash = get_decree_dashboard(state)

        header = f"""<div style="background:#1a2d1a;border:1px solid #22c55e;border-radius:8px;padding:12px;margin-bottom:12px">
            <span style="font-size:16px;font-weight:bold;color:#c9a96e">📋 诏令状态机</span>
            <span style="font-size:12px;color:#9ca3af;margin-left:12px">总诏书：{dash["total"]}</span>
        </div>"""

        status_colors = {"draft": "#f59e0b", "issued": "#22c55e", "expired": "#ef4444", "executed": "#3b82f6", "cancelled": "#6b7280"}
        by_status_html = ""
        for status, decs in dash["by_status"].items():
            color = status_colors.get(status, "#9ca3af")
            items = []
            for d in decs:
                remaining = f"剩{d['remaining']}回合" if status == "issued" and d['remaining'] > 0 else f"第{d['issued_turn']}回合发布"
                items.append(f"""<div style="background:#1a1a2e;border-radius:6px;padding:6px 8px;margin:2px 0;display:flex;justify-content:space-between">
                    <div>
                        <span style="color:{color};font-weight:bold;font-size:12px">[{d["type"]}]</span>
                        <span style="font-size:13px;color:#e8d5b7">{d["title"]}</span>
                        <span style="font-size:10px;color:#9ca3af">（{d["id"]}）</span>
                    </div>
                    <span style="font-size:11px;color:#9ca3af">{remaining}</span>
                </div>""")
            by_status_html += f"""<div style="margin-bottom:10px">
                <div style="color:{color};font-weight:bold;font-size:13px;margin-bottom:4px">{status.upper()}（{len(decs)}）</div>
                {"".join(items)}
            </div>"""

        # 可发类型
        avail_html = "<table style='width:100%;border-collapse:collapse;font-size:12px;background:#1a1a2e;border-radius:6px'>"
        avail_html += "<tr style='background:#16213e'><th style='padding:6px 8px;text-align:left;color:#c9a96e'>类型</th><th style='padding:6px 8px;text-align:left;color:#c9a96e'>威权需求</th><th style='padding:6px 8px;text-align:left;color:#c9a96e'>有效期</th><th style='padding:6px 8px;text-align:left;color:#c9a96e'>效果</th></tr>"
        for dtype, edesc, ac, vt in dash["available_types"]:
            avail_html += f"<tr><td style='padding:5px 8px;color:#e8d5b7;font-weight:bold'>{dtype}</td><td style='padding:5px 8px;color:#ef4444'>{ac}</td><td style='padding:5px 8px;color:#9ca3af'>{vt}回合</td><td style='padding:5px 8px;color:#22c55e'>{edesc}</td></tr>"
        avail_html += "</table>"

        return header + (by_status_html or "<p style='color:#9ca3af'>暂无诏书</p>") + "<h4 style='color:#c9a96e;margin:12px 0 6px'>可发诏书类型</h4>" + avail_html

    def _render_building_html(self) -> str:
        """【建筑】建筑系统HTML：已建成+可建造列表。"""
        if not self.session:
            return "<p>请先点击「新游戏」初始化</p>"
        from han_sim.flows import get_building_status
        from han_sim.models import BUILDING_TYPES, BUILDING_CATALOG
        state = self.session.state
        status = get_building_status(state)

        header = f"""<div style="background:#1a2d1a;border:1px solid #22c55e;border-radius:8px;padding:12px;margin-bottom:12px">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                    <span style="font-size:16px;font-weight:bold;color:#c9a96e">🏛️ 建筑系统</span>
                    <span style="font-size:12px;color:#9ca3af;margin-left:12px">威权：{status["authority"]}</span>
                </div>
                <div style="text-align:right">
                    <span style="font-size:24px;font-weight:bold;color:#f59e0b">{status["treasury"]}</span>
                    <span style="font-size:12px;color:#9ca3af"> 汉室库</span>
                </div>
            </div>
            <div style="font-size:12px;color:#9ca3af;margin-top:4px">
                已建成：{status["built_count"]} | 年维护费：{status["maintenance_total"]}
            </div>
        </div>"""

        # 按类型展示
        type_colors = {"宫殿": "#c9a96e", "军事": "#ef4444", "经济": "#22c55e", "特殊": "#8b5cf6"}
        built_html = ""
        for btype, bids in BUILDING_TYPES.items():
            color = type_colors.get(btype, "#9ca3af")
            built_in = [bid for bid in bids if bid in status["built"]]
            if not built_in:
                continue
            items = []
            for bid in built_in:
                b = BUILDING_CATALOG.get(bid)
                if not b:
                    continue
                items.append(f"""<div style="background:#1a3d1a;border-radius:6px;padding:6px 8px;margin:2px 0">
                    <span style="font-size:14px;color:#22c55e">✅</span>
                    <span style="font-size:13px;color:#e8d5b7;font-weight:bold">{b.name}</span>
                    <span style="font-size:11px;color:#9ca3af">（{b.location}）</span>
                    <span style="font-size:10px;color:#9ca3af">维护:{b.maintenance}/年</span>
                    <span style="font-size:10px;color:#22c55e">{b.effect}</span>
                </div>""")
            built_html += f"""<div style="margin-bottom:10px">
                <div style="color:{color};font-weight:bold;font-size:13px;margin-bottom:4px">{btype}类</div>
                {"".join(items)}
            </div>"""

        # 可建列表
        avail_html = ""
        for btype, bids in BUILDING_TYPES.items():
            color = type_colors.get(btype, "#9ca3af")
            avail_in = [(b) for b in status["available"] if b[0] in bids]
            if not avail_in:
                continue
            items = []
            for bid, name, cost, maint, unlvl, effect, loc in avail_in:
                items.append(f"""<div style="background:#2d2d1a;border-radius:6px;padding:6px 8px;margin:2px 0">
                    <span style="font-size:13px;color:#f59e0b">{bid}</span>
                    <span style="font-size:13px;color:#e8d5b7;font-weight:bold">{name}</span>
                    <span style="font-size:11px;color:#9ca3af">（{loc}）</span>
                    <span style="font-size:10px;color:#ef4444">费用:{cost} | 威权≥{unlvl}</span>
                    <span style="font-size:10px;color:#22c55e">{effect}</span>
                </div>""")
            avail_html += f"""<div style="margin-bottom:10px">
                <div style="color:{color};font-weight:bold;font-size:13px;margin-bottom:4px">{btype}类（可建）</div>
                {"".join(items)}
            </div>"""

        return header + "<h4 style='color:#c9a96e;margin:12px 0 6px'>已建成</h4>" + (built_html or "<p style='color:#9ca3af'>暂无建筑</p>") + "<h4 style='color:#c9a96e;margin:12px 0 6px'>可建造</h4>" + (avail_html or "<p style='color:#9ca3af'>无</p>")

    def _render_skill_html(self) -> str:
        """【技能树】天子技能树HTML：四系技能树+状态+激活按钮。"""
        if not self.session:
            return "<p>请先点击「新游戏」初始化</p>"
        from han_sim.flows import get_skill_tree_status
        from han_sim.models import SKILL_TREES
        state = self.session.state
        status = get_skill_tree_status(state)
        sp = status["skill_points"]
        auth = status["authority"]
        activated = state.metrics.get("activated_skills", [])

        # 技能点
        header = f"""<div style="background:#1a2d1a;border:1px solid #22c55e;border-radius:8px;padding:12px;margin-bottom:12px">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                    <span style="font-size:16px;font-weight:bold;color:#c9a96e">🌳 天子技能树</span>
                    <span style="font-size:12px;color:#9ca3af;margin-left:12px">威权：{auth}</span>
                </div>
                <div style="text-align:right">
                    <span style="font-size:24px;font-weight:bold;color:#f59e0b">{sp}</span>
                    <span style="font-size:12px;color:#9ca3af"> 技能点</span>
                </div>
            </div>
            <div style="font-size:12px;color:#9ca3af;margin-top:4px">
                已激活：{status["activated_count"]}/{status["total_skills"]} &nbsp;
                可用：{len(status["available"])}
            </div>
        </div>"""

        # 四系技能树
        branch_colors = {"经略": "#22c55e", "权谋": "#8b5cf6", "武功": "#ef4444", "文治": "#3b82f6"}
        trees_html = ""
        for branch, skills in SKILL_TREES.items():
            color = branch_colors.get(branch, "#9ca3af")
            tree_items = []
            for skill in skills:
                sid = skill.sid
                is_act = sid in activated
                is_avail = any(s[0] == sid for s in status["available"])
                is_locked = not is_act and not is_avail

                if is_act:
                    icon = "✅"
                    bg = "#1a3d1a"
                    opacity = "1"
                elif is_avail:
                    icon = "🔓"
                    bg = "#2d2d1a"
                    opacity = "1"
                else:
                    icon = "🔒"
                    bg = "#1a1a2e"
                    opacity = "0.5"

                # Tier badge
                tier_badge = f"<span style='background:{color};color:white;padding:1px 4px;border-radius:3px;font-size:10px'>{skill.tier}阶</span>"
                req_note = f" <span style='color:#ef4444;font-size:10px'>需{skill.requires[0] if skill.requires else ''}</span>" if skill.requires and not is_act else ""

                tree_items.append(f"""<div style="background:{bg};border-radius:6px;padding:6px 8px;margin:2px 0;opacity:{opacity};display:flex;align-items:center;gap:6px">
                    <span>{icon}</span>
                    <span style="font-size:12px;color:#e8d5b7;font-weight:bold">{sid}</span>
                    <span style="font-size:12px;color:#e8d5b7">{skill.name}</span>
                    {tier_badge}
                    <span style="font-size:10px;color:#9ca3af">消耗:{skill.cost} | 威权≥{skill.unlock_level}</span>
                </div>""")

            trees_html += f"""<div style="margin-bottom:12px">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
                    <span style="font-size:16px;font-weight:bold;color:{color}">{branch}系</span>
                    <span style="font-size:11px;color:#9ca3af">{status["branch_progress"][branch]["activated"]}/{status["branch_progress"][branch]["total"]} 已激活</span>
                </div>
                {"".join(tree_items)}
            </div>"""

        return header + trees_html

    def _render_loyalty_html(self) -> str:
        """【忠诚度】忠诚度系统HTML：大臣列表+诸侯忠诚度+恢复行动。"""
        if not self.session:
            return "<p>请先点击「新游戏」初始化</p>"
        from han_sim.flows import LOYALTY_RECOVERY_ACTIONS
        db = self.session.db
        authority = self.session.state.metrics.get("威权", 0)

        # 大臣忠诚度列表
        characters = db.list_characters(status="active")
        char_rows = ""
        for c in characters[:10]:
            loyal = c.get("loyalty", 50)
            bar = self._bar(loyal, 100, 10)
            color = "#22c55e" if loyal >= 70 else ("#f59e0b" if loyal >= 40 else "#ef4444")
            char_rows += f"""<tr>
                <td style="padding:4px 6px;font-weight:bold;font-size:12px">{c.get('name','?')}</td>
                <td style="padding:4px 6px;font-size:12px">{c.get('office','?')}</td>
                <td style="padding:4px 6px;color:{color};font-weight:bold">{loyal}</td>
                <td style="padding:4px 6px">{bar}</td>
            </tr>"""

        # 诸侯忠诚度列表
        powers = db.list_powers()
        power_rows = ""
        for p in powers:
            if p.get("id") == "han":
                continue
            loyal = p.get("loyalty", 50)
            bar = self._bar(loyal, 100, 10)
            stance = p.get("stance", "neutral")
            stance_color = {"loyal": "#3b82f6", "neutral": "#6b7280", "hostile": "#ef4444"}.get(stance, "#6b7280")
            power_rows += f"""<tr>
                <td style="padding:4px 6px;font-weight:bold;font-size:12px;color:{stance_color}">{p.get('name','?')}</td>
                <td style="padding:4px 6px;font-size:12px">{p.get('leader','?')}</td>
                <td style="padding:4px 6px;color:{stance_color};font-weight:bold">{loyal}</td>
                <td style="padding:4px 6px">{bar}</td>
            </tr>"""

        # 恢复行动选项
        recovery_options = list(LOYALTY_RECOVERY_ACTIONS.keys())
        recovery_html = ""
        for act, info in LOYALTY_RECOVERY_ACTIONS.items():
            recovery_html += f"""<button onclick="this.parentElement.querySelector('.loyalty-action-input').value='{act}'" 
                style="margin:2px;padding:3px 8px;font-size:11px;background:#16213e;color:#e8d5b7;border:1px solid #c9a96e;border-radius:4px;cursor:pointer">
                {act}({info['cost']}万两)
            </button>"""

        return f"""<div style="font-family:system-ui,sans-serif">
        <h4 style="margin:8px 0 4px;color:#c9a96e">👤 大臣忠诚度</h4>
        <table style="width:100%;border-collapse:collapse;font-size:12px">
            <tr style="background:#16213e">
                <th style="padding:4px 6px;text-align:left;color:#c9a96e;font-size:11px">大臣</th>
                <th style="padding:4px 6px;text-align:left;color:#c9a96e;font-size:11px">官职</th>
                <th style="padding:4px 6px;text-align:center;color:#c9a96e;font-size:11px">忠诚</th>
                <th style="padding:4px 6px;text-align:left;color:#c9a96e;font-size:11px">状态</th>
            </tr>
            {char_rows}
        </table>

        <h4 style="margin:12px 0 4px;color:#c9a96e">⚔️ 诸侯忠诚度</h4>
        <table style="width:100%;border-collapse:collapse;font-size:12px">
            <tr style="background:#16213e">
                <th style="padding:4px 6px;text-align:left;color:#c9a96e;font-size:11px">势力</th>
                <th style="padding:4px 6px;text-align:left;color:#c9a96e;font-size:11px">首领</th>
                <th style="padding:4px 6px;text-align:center;color:#c9a96e;font-size:11px">忠诚</th>
                <th style="padding:4px 6px;text-align:left;color:#c9a96e;font-size:11px">状态</th>
            </tr>
            {power_rows}
        </table>

        <h4 style="margin:12px 0 4px;color:#c9a96e">🆕 忠诚度恢复行动</h4>
        <div style="font-size:11px;color:#9ca3af;margin-bottom:4px">点击按钮选择，然后从下方下拉菜单选择目标大臣执行</div>
        <div style="margin-bottom:6px" class="loyalty-recovery-buttons">{recovery_html}</div>
        """

    def _render_relocate_html(self) -> str:
        """【迁都】迁都系统HTML：当前都城 + 可选都城 + 迁都效果预览。"""
        if not self.session:
            return "<p>请先点击「新游戏」初始化</p>"
        from han_sim.flows import _CAPITAL_EFFECTS
        s = self.session.state
        current = getattr(s, 'capital', '洛阳')
        authority = s.metrics.get('威权', 0)

        # 检查威权是否足够（迁都需威权>=30）
        can_relocate = authority >= 30

        # 都城选项
        capital_options = [
            {"id": "洛阳", "label": "洛阳", "desc": "东汉国都，汉室正统，但董卓控制中", "color": "#ef4444", "disabled": current == "洛阳"},
            {"id": "许昌", "label": "许昌", "desc": "曹操势力范围，形式统一但受制于人", "color": "#f59e0b", "disabled": current == "许昌"},
            {"id": "长安", "label": "长安", "desc": "西京故都，偏安一隅可避锋芒", "color": "#6b7280", "disabled": current == "长安"},
            {"id": "邺城", "label": "邺城", "desc": "袁绍地盘，藩镇不服风险高", "color": "#6b7280", "disabled": current == "邺城"},
            {"id": "南阳", "label": "南阳", "desc": "光武帝乡，人心尚在，风险中等", "color": "#6b7280", "disabled": current == "南阳"},
        ]

        rows_html = ""
        for cap in capital_options:
            disabled_text = "(当前)" if cap["disabled"] else ("(威权不足)" if not can_relocate and not cap["disabled"] else "")
            effect = _CAPITAL_EFFECTS.get(cap["id"], {})
            effect_str = " / ".join([f"{k}{'+' if v >= 0 else ''}{v}" for k, v in effect.items() if v != 0]) or "无变化"
            color = cap["color"]
            row_class = "opacity:0.5" if cap["disabled"] or (not can_relocate and not cap["disabled"]) else ""
            rows_html += f"""<tr style="{row_class}">
                <td style="padding:8px;font-weight:bold;color:{color};font-size:15px">{cap["label"]}</td>
                <td style="padding:8px;font-size:12px;color:#9ca3af">{cap["desc"]}</td>
                <td style="padding:8px;font-size:12px;color:#e8d5b7;text-align:center">{effect_str}</td>
                <td style="padding:8px;font-size:12px;color:#f59e0b">{disabled_text}</td>
            </tr>"""

        header_html = """<tr style="background:#16213e;font-size:11px">
            <th style="padding:6px 8px;text-align:left;color:#c9a96e">都城</th>
            <th style="padding:6px 8px;text-align:left;color:#c9a96e">说明</th>
            <th style="padding:6px 8px;text-align:center;color:#c9a96e">效果</th>
            <th style="padding:6px 8px;text-align:center;color:#c9a96e">状态</th>
        </tr>"""

        return f"""<div style="font-family:system-ui,sans-serif">
        <div style="background:#1a1a2e;border:1px solid #c9a96e;border-radius:8px;padding:12px;margin-bottom:12px;text-align:center">
            <div style="font-size:12px;color:#9ca3af">当前都城</div>
            <div style="font-size:26px;font-weight:bold;color:#c9a96e">{current}</div>
            <div style="font-size:12px;color:#9ca3af;margin-top:4px">威权：{authority}（迁都需≥30）{'✅ 可迁都' if can_relocate else '❌ 威权不足'}</div>
        </div>

        <h4 style="margin:8px 0 6px;color:#c9a96e">🏰 迁都选项</h4>
        <table style="width:100%;border-collapse:collapse;font-size:13px">
            {header_html}
            {rows_html}
        </table>

        <h4 style="margin:12px 0 6px;color:#c9a96e">📜 迁都效果说明</h4>
        <ul style="font-size:12px;color:#9ca3af;padding-left:20px">
            <li>洛阳：汉室正统，无加成，但董卓控制中风险高</li>
            <li>许昌：曹操控制，形式统一，威权+5但藩镇+3</li>
            <li>长安：西迁避难，声望-5，威权-3，藩镇-5（保守策略）</li>
            <li>邺城：袁绍地盘，藩镇-8但声望-3（风险高）</li>
            <li>南阳：光武帝乡，中庸之选</li>
        </ul>
        </div>"""

    def _render_decree_preview(self, intent: str) -> str:
        """诏书预览：根据输入意图显示预计效果。"""
        if not self.session:
            return ""
        from han_sim.decree import DECREE_EFFECT_TEMPLATES
        effects = DECREE_EFFECT_TEMPLATES.get(intent, [])
        if not effects:
            return f"<p style='color:#6b7280;font-size:12px'>未找到「{intent}」的诏书模板</p>"

        authority = self.session.state.metrics.get('威权', 0)
        auth_level = get_authority_level(authority)
        lines = ["<div style='font-size:12px'>"]
        lines.append(f"<b style='color:#c9a96e'>📜 {intent} 预计效果（威权{authority}，倍率{auth_level.decree_mult:.0%}）</b>")
        lines.append("<table style='width:100%;border-collapse:collapse;font-size:12px;margin-top:6px'>")
        total_cost = 0
        for e in effects:
            metric = e.get("metric", "?")
            delta = e.get("delta", 0)
            actual = int(delta * auth_level.decree_mult)
            sign = "+" if actual >= 0 else ""
            color = "#22c55e" if actual > 0 else ("#ef4444" if actual < 0 else "#9ca3af")
            lines.append(f"<tr><td style='padding:2px 4px;color:#e8d5b7'>{metric}</td><td style='color:{color};text-align:right;font-weight:bold'>{sign}{actual}</td></tr>")
            if metric in ("汉室库", "内库") and delta < 0:
                total_cost += abs(delta)
        lines.append("</table>")
        if total_cost > 0:
            lines.append(f"<div style='color:#f59e0b;font-size:11px;margin-top:4px'>⚠️ 消耗汉室库：{total_cost}万两</div>")
        lines.append("</div>")
        return "\n".join(lines)

    # ── 命令 ──────────────────────────────────────────────────────────

    def cmd_summon(self, minister_name: str, question: str):
        if not self.session:
            return "❗ 请先点击 **新游戏** 开始。"
        if not minister_name:
            return "❗ 请选择或输入大臣姓名。"
        q = question.strip() or "本月局势如何？"
        try:
            result = self.session.summon_minister(minister_name, q)
            ministers = self.session.get_active_ministers()
            minister_data = next((m for m in ministers if m["name"] == minister_name), {})
            portrait_html = ""
            if minister_data:
                portrait_html = render_portrait_with_name_html(
                    name=minister_data.get("name", ""),
                    office=minister_data.get("office", ""),
                    office_type=minister_data.get("office_type", "default"),
                    portrait_id=minister_data.get("portrait_id", ""),
                    show_name=False, size=80,
                )
            lines = [f"**【{minister_name}】**", "", result.chat_text]
            if portrait_html:
                lines = [portrait_html] + lines
            if result.refresh_ministers:
                lines.append("")
                lines.append(f"_（{minister_name} 离开，改日再召。）_")
            return "\n".join(lines)
        except Exception as e:
            return f"❗ 召见失败：{str(e)}"

    def cmd_decree(self, intent: str):
        if not self.session:
            return "❗ 请先点击 **新游戏** 开始。"
        if not intent:
            return "❗ 请输入拟旨意图。"

        if intent == "衣带密诏":
            from han_sim.decree import issue_secret_edict
            result = issue_secret_edict(self.session.state, self.session.db)
            d = result.decree
            lines = [f"**【{'衣带密诏已下' if d.full_text else '衣带密诏失败'}】**", ""]
            if d.full_text:
                lines.append(d.full_text)
            else:
                lines.append(f"_（{d.narrative}）_")
            if result.log_entries:
                lines.append("")
                lines.append("**效果**：" + "；".join(result.log_entries))
            return "\n".join(lines)

        try:
            result = issue_decree(intent, self.session.state, self.session.db)
            d = result.decree
            entry = f"《{d.decree_type}》：{d.full_text[:50]}…"
            self.decree_log.append(entry)
            lines = [f"**【诏书已下】《{d.decree_type}》**", "", d.full_text, "", f"_下达原因：{intent}_"]
            if result.log_entries:
                lines.append("")
                lines.append("**效果**：" + "；".join(result.log_entries))
            return "\n".join(lines)
        except Exception as e:
            return f"❗ 拟旨失败：{str(e)}"

    def cmd_emperor_escape(self, target: str = "许昌"):
        """发起献帝东归行动（从长安逃往许昌）。"""
        if not self.session:
            return "❗ 请先点击 **新游戏** 开始。"
        state = self.session.state
        if state.emperor_safe_turn > 0:
            return f"❗ 献帝已于第{state.emperor_safe_turn}回合成功东归，无需再逃。"
        if state.emperor_escaped_turn > 0:
            return f"❗ 献帝已于第{state.emperor_escaped_turn}回合开始东归，途中。"
        if state.dong_zhuo_killed_turn == 0:
            return "❗ 董卓未伏诛，此时出逃风险极高，不建议东归。"
        try:
            from han_sim.flows import initiate_emperor_escape
            result = initiate_emperor_escape(state, target)
            parts = ["**【献帝东归启动】**", ""]
            parts.append(result.get("narrative", "献帝开始东归之路"))
            parts.append("")
            parts.append(f"目标：{target} | 剩余回合：{result.get('turns_left', 5)}")
            parts.append("")
            for k, v in result.get("effects", {}).items():
                sign = "+" if v >= 0 else ""
                color = "#22c55e" if v > 0 else ("#ef4444" if v < 0 else "#9ca3af")
                parts.append(f"<span style='color:{color};font-weight:bold'>{k} {sign}{v}</span>")
            return "\n".join(parts)
        except Exception as e:
            return f"❗ 东归启动失败：{str(e)}"

    def cmd_dongzhuo_elimination(self, military_input: str):
        """执行董卓伏诛行动：输入联军军力，触发伏诛判定。"""
        if not self.session:
            return "❗ 请先点击 **新游戏** 开始。"
        if not military_input:
            return "❗ 请输入联军军力。"
        try:
            military = int(military_input)
        except ValueError:
            return "❗ 请输入有效的数字军力。"
        if military <= 0:
            return "❗ 军力必须大于0。"
        try:
            from han_sim.flows import execute_dongzhuo_elimination, trigger_dongzhuo_trap
            state = self.session.state
            # 如果尚未触发陷阱，先触发
            if state.dong_zhuo_trapped_turn == 0 and state.dong_zhuo_killed_turn == 0:
                trigger_dongzhuo_trap(state)
            result = execute_dongzhuo_elimination(state, military)
            status = "✅ 董卓伏诛成功！" if result["success"] else "❌ 伏诛失败"
            parts = [f"**【{status}】**"]
            parts.append("")
            parts.append(result["narrative"])
            parts.append("")
            parts.append(f"所需军力：{result['required']}，实际：{result['actual']}")
            parts.append("")
            for k, v in result["effects"].items():
                sign = "+" if v >= 0 else ""
                color = "#22c55e" if v > 0 else ("#ef4444" if v < 0 else "#9ca3af")
                parts.append(f"<span style='color:{color};font-weight:bold'>{k} {sign}{v}</span>")
            return "\n".join(parts)
        except Exception as e:
            return f"❗ 董卓伏诛执行失败：{str(e)}"

    def cmd_issue_decree(self, decree_type: str, title: str, content: str, target: str):
        """发布诏书。"""
        if not self.session:
            return "❗ 请先点击 **新游戏** 开始。"
        if not title:
            return "❗ 请输入诏书标题。"
        try:
            from han_sim.flows import issue_decree
            result = issue_decree(self.session.state, decree_type, title, content, target)
            if result.get("success"):
                return result["narrative"]
            else:
                return f"❌ {result.get('narrative', '发布失败')}"
        except Exception as e:
            return f"❗ 发布失败：{str(e)}"

    def cmd_cancel_decree(self, decree_id: str):
        """取消诏书。"""
        if not self.session:
            return "❗ 请先点击 **新游戏** 开始。"
        if not decree_id:
            return "❗ 请输入诏书ID（如 dec_001）。"
        try:
            from han_sim.flows import cancel_decree
            result = cancel_decree(self.session.state, decree_id.strip())
            if result.get("success"):
                return result["narrative"]
            else:
                return f"❌ {result.get('narrative', '取消失败')}"
        except Exception as e:
            return f"❗ 取消失败：{str(e)}"

    def cmd_build_structure(self, bid: str):
        """建造建筑。"""
        if not self.session:
            return "❗ 请先点击 **新游戏** 开始。"
        if not bid:
            return "❗ 请输入建筑ID。"
        try:
            from han_sim.flows import build_structure
            result = build_structure(self.session.state, bid.strip())
            if result.get("success"):
                parts = [f"✅ **{result['building']}** 建造成功！"]
                parts.append("")
                parts.append(f"剩余汉室库：{result['remaining_treasury']}")
                parts.append(f"建造费用：-{result['cost']}")
                parts.append(f"年维护费：-{result['maintenance']}")
                return "\n".join(parts)
            else:
                return f"❌ {result.get('narrative', '建造失败')}"
        except Exception as e:
            return f"❗ 建造失败：{str(e)}"

    def cmd_activate_skill(self, skill_id: str):
        """激活天子技能。"""
        if not self.session:
            return "❗ 请先点击 **新游戏** 开始。"
        if not skill_id:
            return "❗ 请输入技能ID。"
        try:
            from han_sim.flows import activate_skill
            result = activate_skill(self.session.state, skill_id.strip())
            if result.get("success"):
                parts = [f"✅ **{result['skill']}** 激活成功！"]
                parts.append("")
                parts.append(f"剩余技能点：{result['remaining_points']}")
                parts.append(f"消耗技能点：{result['cost']}")
                return "\n".join(parts)
            else:
                return f"❌ {result.get('narrative', '激活失败')}"
        except Exception as e:
            return f"❗ 技能激活失败：{str(e)}"

    def cmd_loyalty_recovery(self, char_name: str, action: str):
        """对指定大臣执行忠诚度恢复行动。"""
        if not self.session:
            return "❗ 请先点击 **新游戏** 开始。"
        if not char_name or not action:
            return "❗ 请填写大臣姓名和恢复行动。"
        try:
            from han_sim.flows import apply_loyalty_recovery, LOYALTY_RECOVERY_ACTIONS
            chars = self.session.db.list_characters(status="active")
            char = next((c for c in chars if c.get("name") == char_name), None)
            if not char:
                return f"❗ 未找到大臣「{char_name}」，请检查姓名。"
            delta = apply_loyalty_recovery(self.session.state, char["id"], action)
            if delta == 0:
                return f"❗ 忠诚度恢复失败（内库不足或行动无效）"
            effect = LOYALTY_RECOVERY_ACTIONS.get(action, {}).get("effects", {})
            return f"**【忠诚度恢复】{char_name} {action}，忠诚度{delta:+d}**"
        except Exception as e:
            return f"❗ 忠诚度恢复失败：{str(e)}"

    def cmd_relocate_capital(self, new_capital: str):
        """执行迁都。"""
        if not self.session:
            return "❗ 请先点击 **新游戏** 开始。"
        if not new_capital:
            return "❗ 请选择目标都城。"
        current = self.session.state.capital
        if current == new_capital:
            return f"❗ 当前就在 {new_capital}，无需迁都。"
        try:
            from han_sim.flows import relocate_capital
            delta = relocate_capital(self.session.state, new_capital)
            if not delta:
                return f"❗ 迁都至 {new_capital} 失败（未知原因）"
            parts = [f"**【迁都成功】{current} → {new_capital}**"]
            parts.append("")
            for k, v in delta.items():
                sign = "+" if v >= 0 else ""
                color = "#22c55e" if v > 0 else ("#ef4444" if v < 0 else "#9ca3af")
                parts.append(f"<span style='color:{color};font-weight:bold'>{k} {sign}{v}</span>")
            parts.append("")
            parts.append(f"_当前都城：{new_capital}_")
            return "\n".join(parts)
        except Exception as e:
            return f"❗ 迁都失败：{str(e)}"

    def cmd_authority_recovery(self, action: str):
        """执行威权恢复行动。"""
        if not self.session:
            return "❗ 请先点击 **新游戏** 开始。"
        if not action:
            return "❗ 请选择威权恢复行动。"
        try:
            delta = execute_authority_recovery(self.session.state, action)
            if not delta:
                return "❗ 行动执行失败（可能威权不足或内库不够）"
            parts = [f"**【威权恢复：{action}】**"]
            parts.append("")
            for k, v in delta.items():
                sign = "+" if v >= 0 else ""
                color = "#22c55e" if v > 0 else ("#ef4444" if v < 0 else "#9ca3af")
                parts.append(f"<span style='color:{color};font-weight:bold'>{k} {sign}{v}</span>")
            return "\n".join(parts)
        except Exception as e:
            return f"❗ 威权恢复失败：{str(e)}"

    def cmd_review(self):
        if not self.session:
            return "❗ 请先点击 **新游戏** 开始。"
        try:
            triggered = self.session.db.load_state("triggered_events") or []
            sim = run_monthly_simulation(self.session.state, self.session.db, triggered)
            lines = [
                f"**【{self.session.state.year - 1}年{self.session.state.period}月 · 月末推演】**",
                "",
                sim.narrative[:500] if len(sim.narrative) > 500 else sim.narrative,
                "",
            ]
            if sim.historical:
                lines.append("**📜 历史事件**")
                for e in sim.historical:
                    lines.append(f"- **{e['title']}**：{e['summary']}")
                lines.append("")
            if sim.threshold_crisis:
                lines.append("**🚨 危机事件**")
                for e in sim.threshold_crisis:
                    lines.append(f"- **{e['title']}**：{e['summary']}")
                lines.append("")
            if sim.random_events:
                lines.append("**⚡ 突发**")
                for e in sim.random_events:
                    lines.append(f"- **{e['title']}**：{e['summary']}")
                lines.append("")
            net = sim.fiscal.get("net", 0)
            lines.extend([
                "**📊 本月结算**",
                f"- 财政：{'盈余' if net >= 0 else '亏损'}{abs(net)}万两",
                f"- 声望 {sim.metrics_delta.get('声望', 0):+d}",
                f"- 威权 {sim.metrics_delta.get('威权', 0):+d}",
                f"- 藩镇 {sim.metrics_delta.get('藩镇', 0):+d}",
                "",
            ])
            if hasattr(sim, 'warlord_changes') and sim.warlord_changes:
                lines.append("**⚔️ 诸侯动态**")
                for w in sim.warlord_changes[:5]:
                    lines.append(f"- {w.get('id','?')}：{w.get('last_action','按兵不动')}")
                lines.append("")
            if self.decree_log:
                lines.append("**📋 本月诏书**")
                for d in self.decree_log:
                    lines.append(f"- {d}")
                lines.append("")
            lines.append("─" * 40)
            lines.append("")
            lines.append(self._render_state())
            self.decree_log = []
            return "\n".join(lines)
        except Exception as e:
            return f"❗ 月末推演失败：{str(e)}"


# ── Gradio UI ──────────────────────────────────────────────────────────
def build_ui():
    ui = GameUI()

    # 古风CSS：玄黑/朱红/古金
    custom_css = get_theme_css() + """
    /* Step3额外美化 */
    .panel-card {
        background: #1a1a2e;
        border: 1px solid #2d2d44;
        border-radius: 8px;
        padding: 12px;
        margin: 4px 0;
    }
    .gold-border {
        border-left: 3px solid #c9a96e;
        padding-left: 10px;
    }
    .authority-critical {
        animation: pulse-red 2s infinite;
    }
    @keyframes pulse-red {
        0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.4); }
        50% { box-shadow: 0 0 8px 2px rgba(239,68,68,0.6); }
    }
    .tab-selected {
        background: linear-gradient(180deg, #2d2d44 0%, #1a1a2e 100%) !important;
    }
    .btn-royal {
        background: linear-gradient(135deg, #8b0000 0%, #5c0000 100%) !important;
        border: 1px solid #c9a96e !important;
        color: #e8d5b7 !important;
        font-weight: bold !important;
    }
    .btn-royal:hover {
        background: linear-gradient(135deg, #a50000 0%, #7c0000 100%) !important;
        box-shadow: 0 0 12px rgba(201,169,110,0.4) !important;
    }
    .stat-card {
        background: #16213e;
        border: 1px solid #2d2d44;
        border-radius: 6px;
        padding: 8px;
        text-align: center;
    }
    """

    with gr.Blocks(title="汉献帝之末路", css=custom_css, theme=gr.themes.Default(
        primary_hue="orange",
        secondary_hue="orange",
    )) as demo:

        # ── 顶部标题区 ─────────────────────────────────────────────
        gr.HTML(TITLE_BANNER)

        # ── 主布局：三栏 ─────────────────────────────────────────────
        with gr.Row():
            # ── 左侧边栏：状态总览 + 大臣列表 ──────────────────
            with gr.Column(scale=1, min_width=260):
                gr.HTML("<h3 style='color:#c9a96e;padding:8px 0 4px;border-bottom:1px solid #2d2d44'>📊 国势总览</h3>")
                dashboard_display = gr.HTML("*点击「新游戏」初始化*")
                refresh_dashboard_btn = gr.Button("🔄 刷新", size="compact")

                gr.HTML("<h3 style='color:#c9a96e;padding:12px 0 4px;border-bottom:1px solid #2d2d44;margin-top:8px'>👥 在朝大臣</h3>")
                ministers_display = gr.Markdown("*点击「新游戏」查看*")

            # ── 中央主内容区 ─────────────────────────────────────
            with gr.Column(scale=3):
                with gr.Tabs():
                    # Tab1: 召对
                    with gr.TabItem("🎙️ 召对"):
                        gr.Markdown("### 🎙️ 召见大臣")
                        gr.Markdown("*选择或输入大臣姓名，与其对话。*")
                        with gr.Row():
                            minister_input = gr.Textbox(
                                label="大臣姓名", placeholder="如：杨彪", scale=1
                            )
                            summon_btn = gr.Button("召见", variant="primary", scale=0)
                        question_input = gr.Textbox(
                            label="询问内容（选填）",
                            placeholder="本月局势如何？",
                            lines=2,
                        )
                        summon_output = gr.Markdown()

                    # Tab2: 诏书
                    with gr.TabItem("📜 诏书"):
                        gr.Markdown("### 📜 拟旨")
                        gr.Markdown("*输入拟旨意图，下方预览预计效果，确认后再下达诏书。*")
                        with gr.Row():
                            intent_input = gr.Dropdown(
                                label="选择或输入拟旨意图",
                                choices=DECREE_TYPES,
                                value="",
                                allow_custom_value=True,
                            )
                            decree_btn = gr.Button("拟旨", variant="primary")

                        # 诏书预览区
                        decree_preview_display = gr.HTML("<p style='color:#6b7280;font-size:12px'>选择诏书类型后可预览效果</p>")

                        decree_output = gr.Markdown()

                    # Tab3: 势力
                    with gr.TabItem("⚔️ 势力"):
                        gr.Markdown("### ⚔️ 天下诸侯")
                        powers_display = gr.HTML("*点击「新游戏」初始化*")
                        refresh_powers_btn = gr.Button("🔄 刷新势力")

                    # Tab4: 情报
                    with gr.TabItem("🕵️ 情报"):
                        gr.Markdown("### 🕵️ 军情/情报系统")
                        intel_display = gr.HTML("*点击「新游戏」初始化*")
                        refresh_intel_btn = gr.Button("🔄 刷新情报")

                    # Tab5: 地图
                    with gr.TabItem("🗺️ 地图"):
                        gr.Markdown("### 🗺️ 天下大势（点击州名查看详情）")
                        map_display = gr.HTML("*点击「新游戏」初始化地图*")
                        refresh_map_btn = gr.Button("🔄 刷新地图")

                    # Tab6: 历史
                    with gr.TabItem("📖 历史"):
                        gr.Markdown("### 📖 召对历史")
                        history_display = gr.Markdown("*召对记录将显示在这里*")
                        refresh_history_btn = gr.Button("🔄 刷新召对记录")

                    # Tab7: 日记
                    with gr.TabItem("📋 日志"):
                        gr.Markdown("### 📖 天子日记")
                        diary_display = gr.HTML("*天子日记将显示在这里*")
                        refresh_diary_btn = gr.Button("🔄 刷新日记")

                    # Tab7: 献帝东归
                    with gr.TabItem("🚗 东归"):
                        gr.Markdown("### 🚗 献帝东归")
                        escape_display = gr.HTML("*点击「新游戏」初始化*")
                        with gr.Row():
                            escape_target_input = gr.Dropdown(
                                label="目标",
                                choices=["许昌", "洛阳", "邺城"],
                                value="许昌",
                            )
                            escape_btn = gr.Button("发起东归", variant="primary")
                        escape_output = gr.Markdown()

                    # Tab8: 讨伐董卓
                    with gr.TabItem("⚔️ 讨伐"):
                        gr.Markdown("### ⚔️ 董卓伏诛线")
                        dongzhuo_display = gr.HTML("*点击「新游戏」初始化*")
                        with gr.Row():
                            dongzhuo_military_input = gr.Number(
                                label="联军军力",
                                placeholder="输入联军总军力",
                                precision=0,
                            )
                            dongzhuo_btn = gr.Button("执行伏诛", variant="primary")
                        dongzhuo_output = gr.Markdown()

                    # Tab8: 忠诚度
                    with gr.TabItem("💗 忠诚度"):
                        gr.Markdown("### 💗 忠诚度系统")
                        loyalty_display = gr.HTML("*点击「新游戏」初始化*")
                        with gr.Row():
                            loyalty_char_input = gr.Textbox(
                                label="目标大臣姓名",
                                placeholder="如：杨彪",
                                lines=1,
                            )
                            loyalty_action_input = gr.Dropdown(
                                label="恢复行动",
                                choices=["施恩", "嘉奖", "笼络", "赦免", "晋升"],
                                value="",
                            )
                            loyalty_btn = gr.Button("执行", variant="primary")
                        loyalty_output = gr.Markdown()
                        refresh_skill_btn = gr.Button("🔄 刷新技能树")

                    # Tab10: 技能
                    with gr.TabItem("🌳 技能"):
                        gr.Markdown("### 🌳 天子技能树")
                        skill_display = gr.HTML("*点击「新游戏」初始化*")
                        with gr.Row():
                            skill_input = gr.Textbox(
                                label="输入技能ID",
                                placeholder="如：jx_01（输入技能ID激活）",
                                lines=1,
                            )
                            skill_btn = gr.Button("激活技能", variant="primary")
                        skill_output = gr.Markdown()

                    # Tab11: 派系
                    with gr.TabItem("⚖️ 派系"):
                        gr.Markdown("### ⚖️ 朝堂派系")
                        faction_display = gr.HTML("*点击「新游戏」初始化*")
                        faction_output = gr.Markdown()
                        refresh_faction_btn = gr.Button("🔄 刷新派系")

                    # Tab12: 建筑
                    with gr.TabItem("🏛️ 建筑"):
                        gr.Markdown("### 🏛️ 建筑系统")
                        building_display = gr.HTML("*点击「新游戏」初始化*")
                        with gr.Row():
                            building_input = gr.Textbox(
                                label="输入建筑ID",
                                placeholder="如：weiyang",
                                lines=1,
                            )
                            building_btn = gr.Button("建造", variant="primary")
                        building_output = gr.Markdown()
                        refresh_building_btn = gr.Button("🔄 刷新建筑")

                    # Tab11: 诏令
                    with gr.TabItem("📋 诏令"):
                        gr.Markdown("### 📋 诏令状态机")
                        decree_display = gr.HTML("*点击「新游戏」初始化*")
                        with gr.Row():
                            decree_type_input = gr.Dropdown(
                                label="诏书类型",
                                choices=["衣带密诏", "讨伐诏书", "迁都诏书", "嘉奖诏书", "罪己诏", "大赦天下"],
                                value="衣带密诏",
                            )
                        with gr.Row():
                            decree_title_input = gr.Textbox(label="诏书标题", placeholder="如：衣带密诏", lines=1)
                            decree_target_input = gr.Textbox(label="目标", placeholder="如：曹操（可空）", lines=1)
                        with gr.Row():
                            decree_content_input = gr.Textbox(label="内容", placeholder="诏书内容", lines=2)
                        with gr.Row():
                            decree_issue_btn = gr.Button("发布诏书", variant="primary")
                            decree_cancel_btn = gr.Button("取消诏书")
                        decree_output = gr.Markdown()
                        refresh_decree_btn = gr.Button("🔄 刷新诏令")

                    # Tab12: 迁都
                    with gr.TabItem("🏰 迁都"):
                        gr.Markdown("### 🏰 迁都系统")
                        relocate_display = gr.HTML("*点击「新游戏」初始化*")
                        with gr.Row():
                            relocate_input = gr.Dropdown(
                                label="选择目标都城",
                                choices=["洛阳", "许昌", "长安", "邺城", "南阳"],
                                value="",
                            )
                            relocate_btn = gr.Button("执行迁都", variant="primary")
                        relocate_output = gr.Markdown()
                        refresh_relocate_btn = gr.Button("🔄 刷新迁都选项")

            # ── 右侧边栏：操作面板 ───────────────────────────────
            with gr.Column(scale=1, min_width=260):
                gr.HTML("<h3 style='color:#c9a96e;padding:8px 0 4px;border-bottom:1px solid #2d2d44'>⚡ 快捷操作</h3>")

                gr.HTML("<h4 style='color:#c9a96e;padding:4px 0'>🆕 威权恢复</h4>")
                recovery_input = gr.Textbox(
                    label="选择恢复行动",
                    placeholder="从左侧仪表盘点击按钮选择，或直接输入行动名称",
                    lines=1,
                )
                recovery_btn = gr.Button("执行恢复", variant="primary", size="compact")
                recovery_output = gr.Markdown()

                gr.HTML(DIVIDER_SVG)

                gr.HTML("<h4 style='color:#c9a96e;padding:4px 0'>⚖️ 派系态势</h4>")
                gr.HTML('<div id="faction-mini" style="font-size:11px;color:#9ca3af;line-height:1.6">初始化中...</div>')

                gr.HTML(DIVIDER_SVG)

                gr.HTML("<h4 style='color:#c9a96e;padding:4px 0'>📜 快速拟旨</h4>")
                quick_intent = gr.Dropdown(
                    label="常用诏书",
                    choices=DECREE_TYPES[:6],
                    value="",
                    allow_custom_value=True,
                )
                quick_decree_btn = gr.Button("下达诏书", variant="primary", size="compact")
                quick_decree_output = gr.Markdown()

                gr.HTML("<h4 style='color:#c9a96e;padding:12px 0 4px'>🕵️ 快捷召对</h4>")
                quick_minister = gr.Textbox(placeholder="大臣姓名", lines=1)
                quick_summon_btn = gr.Button("召见", size="compact")
                quick_summon_output = gr.Markdown()

                gr.HTML("<h4 style='color:#c9a96e;padding:12px 0 4px'>📋 月末推演</h4>")
                review_btn = gr.Button("⏭️ 月末推演", variant="stop", size="lg")
                review_output = gr.Markdown()

                gr.HTML("<h4 style='color:#c9a96e;padding:12px 0 4px'>🎮 游戏控制</h4>")
                new_game_btn = gr.Button("🆕 新游戏", variant="secondary", size="lg")

        # ── 底部帮助 ────────────────────────────────────────────────
        gr.HTML(f"""
        <div style="background:#1a1a2e;border-top:1px solid #2d2d44;padding:12px 24px;margin-top:8px">
            <p style="color:#6b7280;font-size:12px;margin:0">{HELP}</p>
        </div>
        """)

        # ── 事件绑定 ────────────────────────────────────────────────
        def do_new_game():
            out = ui.new_game()
            ministers = ui._render_ministers()
            history = ui._render_history()
            diary = ui._render_diary_html()
            dash = ui._render_dashboard_html()
            powers = ui._render_powers_html()
            intel = ui._render_intel_html()
            map_html = ui._render_map_html()
            return out, ministers, history, diary, dash, powers, intel, map_html, relocate_html

        def do_refresh_dashboard():
            return ui._render_dashboard_html()
        def do_refresh_powers():
            return ui._render_powers_html()
        def do_refresh_history():
            return ui._render_history()
        def do_refresh_diary():
            return ui._render_diary_html()
        def do_refresh_intel():
            return ui._render_intel_html()
        def do_refresh_map():
            return ui._render_map_html()

        def do_refresh_relocate():
            return ui._render_relocate_html()

        def do_refresh_loyalty():
            return ui._render_loyalty_html()

        def do_refresh_escape():
            return ui._render_escape_html()

        def do_refresh_dongzhuo():
            return ui._render_dongzhuo_html()

        def do_refresh_faction():
            return ui._render_faction_html()

        def do_refresh_decree():
            return ui._render_decree_html()

        def do_refresh_building():
            return ui._render_building_html()

        def do_refresh_skill():
            return ui._render_skill_html()

        # 召对
        summon_btn.click(
            fn=ui.cmd_summon,
            inputs=[minister_input, question_input],
            outputs=summon_output,
        )
        # 快捷召对
        def quick_summon(name):
            if not name:
                return "❗ 请输入大臣姓名"
            return ui.cmd_summon(name, "本月局势如何？")

        quick_summon_btn.click(
            fn=quick_summon,
            inputs=[quick_minister],
            outputs=quick_summon_output,
        )
        # 诏书预览
        intent_input.change(
            fn=ui._render_decree_preview,
            inputs=[intent_input],
            outputs=[decree_preview_display],
        )
        # 诏书
        decree_btn.click(
            fn=ui.cmd_decree,
            inputs=[intent_input],
            outputs=decree_output,
        )
        # 快捷诏书
        def quick_decree(intent):
            if not intent:
                return "❗ 请选择诏书类型"
            return ui.cmd_decree(intent)

        quick_decree_btn.click(
            fn=quick_decree,
            inputs=[quick_intent],
            outputs=quick_decree_output,
        )
        # 迁都
        relocate_btn.click(
            fn=ui.cmd_relocate_capital,
            inputs=[relocate_input],
            outputs=relocate_output,
        )
        # 献帝东归
        escape_btn.click(
            fn=ui.cmd_emperor_escape,
            inputs=[escape_target_input],
            outputs=escape_output,
        )
        # 诏书发布
        decree_issue_btn.click(
            fn=ui.cmd_issue_decree,
            inputs=[decree_type_input, decree_title_input, decree_content_input, decree_target_input],
            outputs=decree_output,
        )
        decree_cancel_btn.click(
            fn=ui.cmd_cancel_decree,
            inputs=[decree_title_input],  # Using title as ID for simplicity
            outputs=decree_output,
        )
        # 建筑建造
        building_btn.click(
            fn=ui.cmd_build_structure,
            inputs=[building_input],
            outputs=building_output,
        )
        # 技能激活
        skill_btn.click(
            fn=ui.cmd_activate_skill,
            inputs=[skill_input],
            outputs=skill_output,
        )
        # 忠诚度恢复
        loyalty_btn.click(
            fn=ui.cmd_loyalty_recovery,
            inputs=[loyalty_char_input, loyalty_action_input],
            outputs=loyalty_output,
        )
        # 董卓伏诛
        dongzhuo_btn.click(
            fn=ui.cmd_dongzhuo_elimination,
            inputs=[dongzhuo_military_input],
            outputs=dongzhuo_output,
        )
        # 威权恢复
        recovery_btn.click(
            fn=ui.cmd_authority_recovery,
            inputs=[recovery_input],
            outputs=[recovery_output],
        )
        # 月末推演
        review_btn.click(
            fn=ui.cmd_review,
            inputs=[],
            outputs=[review_output],
        )
        # 新游戏
        new_game_btn.click(
            fn=do_new_game,
            inputs=[],
            outputs=[ministers_display, history_display,
                     diary_display, dashboard_display, powers_display, intel_display, map_display, relocate_display, loyalty_display, dongzhuo_display, escape_display, skill_display, building_display, decree_display, faction_display],
        )
        # 刷新按钮
        refresh_dashboard_btn.click(fn=do_refresh_dashboard, inputs=[], outputs=[dashboard_display])
        refresh_powers_btn.click(fn=do_refresh_powers, inputs=[], outputs=[powers_display])
        refresh_history_btn.click(fn=do_refresh_history, inputs=[], outputs=[history_display])
        refresh_diary_btn.click(fn=do_refresh_diary, inputs=[], outputs=[diary_display])
        refresh_relocate_btn.click(fn=do_refresh_relocate, inputs=[], outputs=[relocate_display])
        refresh_loyalty_btn.click(fn=do_refresh_loyalty, inputs=[], outputs=[loyalty_display])
        refresh_dongzhuo_btn.click(fn=do_refresh_dongzhuo, inputs=[], outputs=[dongzhuo_display])
        refresh_escape_btn.click(fn=do_refresh_escape, inputs=[], outputs=[escape_display])
        refresh_skill_btn.click(fn=do_refresh_skill, inputs=[], outputs=[skill_display])
        refresh_building_btn.click(fn=do_refresh_building, inputs=[], outputs=[building_display])
        refresh_decree_btn.click(fn=do_refresh_decree, inputs=[], outputs=[decree_display])
        refresh_faction_btn.click(fn=do_refresh_faction, inputs=[], outputs=[faction_display])
        refresh_intel_btn.click(fn=do_refresh_intel, inputs=[], outputs=[intel_display])
        refresh_map_btn.click(fn=do_refresh_map, inputs=[], outputs=[map_display])

        # 初始化
        demo.load(
            fn=do_new_game,
            inputs=[],
            outputs=[ministers_display, history_display,
                     diary_display, dashboard_display, powers_display, intel_display, map_display, relocate_display, loyalty_display, dongzhuo_display, escape_display, skill_display, building_display, decree_display, faction_display],
        )

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=5199,
        share=False,
    )
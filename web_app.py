"""汉献帝之末路 Gradio Web 交互界面。L8。V0.9.6 - UI Step1：1080P桌面端适配。

布局：左侧状态栏 + 右侧主内容区，固定1200px宽度。
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
from han_sim.models import GameState
from han_sim.paths import user_data_path
from han_sim.session import GameSession
from han_sim.conversation import get_recent_exchanges
from han_sim.simulation import run_monthly_simulation
from han_sim.map_view import render_map_html as _render_svg_map
from han_sim.portraits import render_avatar_grid_html, render_portrait_with_name_html
from han_sim.theme import get_theme_css, THEME

# ── API Key ─────────────────────────────────────────────────────────────
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
- **月末推演**：推进时间，结算财政和事件，触发历史事件

**指标说明**：
- 汉室库：财政收入（万两/月）
- 声望：汉室民心（0-100）
- 威权：天子威权（0-100）
- 藩镇：藩镇割据程度（越低越好，0=完全统一）
"""

DECREE_TYPES = [
    "赈济灾民", "减免赋税", "颁布罪己诏", "提拔贤才", "整饬吏治",
    "军事调度", "外交安抚", "流通铜钱", "改革税制", "召集兵马",
    "衣带密诏", "献帝东归",
]


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
        if authority >= 80:
            auth_label = "🔴 诏书如山"
        elif authority >= 50:
            auth_label = "🟡 诏书有效"
        elif authority >= 20:
            auth_label = "🟠 阳奉阴违"
        else:
            auth_label = "⚫ 无人理会"
        lines = [
            f"**【{s.year}年{s.period}月 · 第{s.turn}回合 · {s.capital}】**",
            "",
            f"📦 汉室库：{s.metrics.get('汉室库', 0)}万两",
            f"💰 内库：{s.metrics.get('内库', 0)}万两",
            f"⭐ 声望：{s.metrics.get('声望', 0)}/100",
            f"👑 威权：{authority}/100 — {auth_label}",
            f"⚔️  藩镇：{s.metrics.get('藩镇', 0)}/100",
            "",
        ]
        return "\n".join(lines)

    def _render_dashboard_html(self) -> str:
        """【总览】仪表盘 HTML：数值卡片 + 历史线进度 + 活跃事项。"""
        s = self.session.state
        authority = s.metrics.get('威权', 0)
        shengwang = s.metrics.get('声望', 0)
        fanzhen = s.metrics.get('藩镇', 0)
        han_ku = s.metrics.get('汉室库', 0)
        nei_ku = s.metrics.get('内库', 0)

        auth_color = "#ef4444" if authority < 20 else ("#f59e0b" if authority < 50 else "#3b82f6")

        dong_trapped = s.dong_zhuo_trapped_turn > 0 and s.dong_zhuo_killed_turn == 0
        dong_killed = s.dong_zhuo_killed_turn > 0
        dong_pct = 100 if dong_killed else (20 if dong_trapped else 0)
        dong_label = "已伏诛 ✓" if dong_killed else ("围困中" if dong_trapped else "未触发")

        escape_done = s.emperor_safe_turn > 0
        escape_ongoing = s.emperor_escaped_turn > 0 and not escape_done
        if escape_done:
            esc_pct = 100
            esc_label = "已东归 ✓"
        elif escape_ongoing:
            esc_turns = s.turn - s.emperor_escaped_turn
            esc_pct = min(100, int((esc_turns / 5) * 100))
            esc_label = f"逃难中 {esc_turns}/5回合"
        else:
            esc_pct = 0
            esc_label = "未触发"

        issues = self.session.db.get_active_issues()
        issues_html = ""
        if issues:
            for iss in issues[:6]:
                pct = int(iss.get("bar_value", 0))
                sev = iss.get("severity", 50)
                sev_color = "#ef4444" if sev >= 70 else "#f59e0b" if sev >= 40 else "#6b7280"
                issues_html += f"""<tr>
                    <td style="color:{sev_color};font-weight:bold">{iss.get('title','')[:14]}</td>
                    <td>{self._bar(pct)} {pct}%</td>
                    <td style="color:{sev_color}">{sev}</td>
                </tr>"""
        else:
            issues_html = "<tr><td colspan=3 style='color:#6b7280'>本回合无活跃事项</td></tr>"

        return f"""<div style="font-family:system-ui,sans-serif">
        <table style="width:100%;border-collapse:collapse">
            <tr>
                <td style="padding:10px;border:1px solid #2d2d44;text-align:center;background:#1a1a2e">
                    <div style="font-size:12px;color:#9ca3af">汉室库（万两）</div>
                    <div style="font-size:26px;font-weight:bold;color:#c9a96e">{han_ku}</div>
                </td>
                <td style="padding:10px;border:1px solid #2d2d44;text-align:center;background:#1a1a2e">
                    <div style="font-size:12px;color:#9ca3af">内库（万两）</div>
                    <div style="font-size:26px;font-weight:bold;color:#c9a96e">{nei_ku}</div>
                </td>
                <td style="padding:10px;border:1px solid #2d2d44;text-align:center;background:#1a1a2e">
                    <div style="font-size:12px;color:#9ca3af">声望</div>
                    <div style="font-size:26px;font-weight:bold;color:#22c55e">{shengwang}</div>
                    <div style="font-size:11px">{self._bar(shengwang)}</div>
                </td>
                <td style="padding:10px;border:1px solid #2d2d44;text-align:center;background:#1a1a2e">
                    <div style="font-size:12px;color:#9ca3af">威权</div>
                    <div style="font-size:26px;font-weight:bold;color:{auth_color}">{authority}</div>
                    <div style="font-size:11px">{self._bar(authority)}</div>
                </td>
                <td style="padding:10px;border:1px solid #2d2d44;text-align:center;background:#1a1a2e">
                    <div style="font-size:12px;color:#9ca3af">藩镇</div>
                    <div style="font-size:26px;font-weight:bold;color:#ef4444">{fanzhen}</div>
                    <div style="font-size:11px">{self._bar(fanzhen)}</div>
                </td>
            </tr>
        </table>

        <h4 style="margin:14px 0 6px;color:#c9a96e;font-size:13px">📜 历史线进度</h4>
        <table style="width:100%;border-collapse:collapse">
            <tr>
                <td style="padding:4px 8px;font-size:13px;color:#e8d5b7">董卓伏诛线</td>
                <td style="padding:4px 8px">{self._bar(dong_pct)} {dong_label}</td>
            </tr>
            <tr>
                <td style="padding:4px 8px;font-size:13px;color:#e8d5b7">献帝东归线</td>
                <td style="padding:4px 8px">{self._bar(esc_pct)} {esc_label}</td>
            </tr>
        </table>

        <h4 style="margin:14px 0 6px;color:#c9a96e;font-size:13px">📋 待办事项</h4>
        <table style="width:100%;border-collapse:collapse;font-size:13px">
            <tr style="background:#16213e">
                <th style="padding:4px 8px;text-align:left;color:#c9a96e">事项</th>
                <th style="padding:4px 8px;text-align:left;color:#c9a96e">进度</th>
                <th style="padding:4px 8px;text-align:center;color:#c9a96e">严重度</th>
            </tr>
            {issues_html}
        </table>
        </div>"""

    def _render_powers_html(self) -> str:
        """【势力】势力视图 HTML，按 stance 着色。"""
        powers = self.session.db.list_powers()
        colors = {"loyal": "#3b82f6", "neutral": "#6b7280", "hostile": "#ef4444"}
        labels = {"loyal": "忠", "neutral": "中", "hostile": "敌"}
        rows = []
        for p in powers:
            color = colors.get(p.get("stance", "neutral"), "#6b7280")
            badge = labels.get(p.get("stance", "neutral"), "?")
            rows.append(f"""<tr style="color:{color}">
                <td style="padding:6px 8px;font-weight:bold">{p.get('name','?')}</td>
                <td style="padding:6px 8px">{p.get('leader','?')}</td>
                <td style="padding:6px 8px;text-align:center">{badge}</td>
                <td style="padding:6px 8px;text-align:right">{p.get('military_strength',0)}</td>
                <td style="padding:6px 8px;text-align:right">{p.get('leverage',0)}</td>
                <td style="padding:6px 8px;font-size:12px;color:#9ca3af">{p.get('last_action','按兵不动') or '按兵不动'}</td>
            </tr>""")

        header = """<tr style="background:#16213e;font-size:12px">
            <th style="padding:6px 8px;text-align:left;color:#c9a96e">势力</th>
            <th style="padding:6px 8px;text-align:left;color:#c9a96e">首领</th>
            <th style="padding:6px 8px;text-align:center;color:#c9a96e">立场</th>
            <th style="padding:6px 8px;text-align:right;color:#c9a96e">军力</th>
            <th style="padding:6px 8px;text-align:right;color:#c9a96e">威势</th>
            <th style="padding:6px 8px;text-align:left;color:#c9a96e">近动</th>
        </tr>"""

        return f"""<div style="font-family:system-ui,sans-serif">
        <table style="width:100%;border-collapse:collapse;font-size:13px">
            {header}
            {"".join(rows)}
        </table>
        <p style="font-size:12px;color:#9ca3af;margin-top:8px">
            🟦 忠 · 🟪 中立 · 🟥 敌对 · 军力/威势越高威胁越大
        </p>
        </div>"""

    def _render_ministers(self):
        """在朝大臣列表：带头像网格视图。"""
        ministers = self.session.get_active_ministers()
        if not ministers:
            return "<p style='color:#9ca3af;text-align:center'>无可用大臣</p>"
        return render_avatar_grid_html(ministers, cols=4, size=64)

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
                        "youzhou": "幽州", "bingzhou": "并州", "yanzhou": "兖州",
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
        <p style='font-size:13px'>{"🔓 密探已解锁（威权≥40）" if intel_unlocked else f"🔒 密探未解锁（威权需≥40，当前{authority}）"}</p>
        <p style='font-size:13px'>📍 董卓伏诛线：<span style='color:{trap_color}'>{trap_desc}</span></p>
        <p style='font-size:13px'>💰 汉室库：{han_ku}万两 · 内库：{nei_ku}万两</p>
        <p style="font-size:12px;color:#9ca3af">🟦 忠诚 · 🟪 中立 · 🟥 敌对</p>
        </div>"""

    def _render_diary_html(self) -> str:
        """【日志】天子日记视图。"""
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
    custom_css = get_theme_css()

    with gr.Blocks(title="汉献帝之末路", css=custom_css, theme=gr.themes.Default(
        primary_hue="orange",
        secondary_hue="orange",
    )) as demo:

        # ── 顶部标题区 ─────────────────────────────────────────────
        gr.HTML("""
        <div style="background:#1a1a2e;border-bottom:2px solid #c9a96e;padding:16px 24px;text-align:center">
            <h1 style="color:#c9a96e;margin:0;font-size:1.8rem;font-family:serif">👑 汉献帝之末路</h1>
            <p style="color:#9ca3af;margin:6px 0 0;font-size:14px">189年，董卓进京，废少帝立献帝。名为天子，实为阶下囚。</p>
        </div>
        """)

        # ── 主布局：三栏 ─────────────────────────────────────────────
        with gr.Row():
            # ── 左侧边栏：状态总览 + 大臣列表 ──────────────────
            with gr.Column(scale=1, min_width=260):
                gr.HTML("<h3 style='color:#c9a96e;padding:8px 0 4px'>📊 国势总览</h3>")
                dashboard_display = gr.HTML("*点击「新游戏」初始化*")
                refresh_dashboard_btn = gr.Button("🔄 刷新", size="compact")

                gr.HTML("<h3 style='color:#c9a96e;padding:12px 0 4px'>👥 在朝大臣</h3>")
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
                        intent_input = gr.Dropdown(
                            label="选择或输入拟旨意图",
                            choices=DECREE_TYPES,
                            value="",
                            allow_custom_value=True,
                        )
                        decree_btn = gr.Button("拟旨", variant="primary")
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

            # ── 右侧边栏：操作面板 ───────────────────────────────
            with gr.Column(scale=1, min_width=260):
                gr.HTML("<h3 style='color:#c9a96e;padding:8px 0 4px'>⚡ 快捷操作</h3>")

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
            return out, ministers, history, diary, dash, powers, intel, map_html

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
        # 月末推演
        review_btn.click(
            fn=ui.cmd_review,
            inputs=[],
            outputs=review_output,
        )
        # 新游戏
        new_game_btn.click(
            fn=do_new_game,
            inputs=[],
            outputs=[ministers_display, history_display,
                     diary_display, dashboard_display, powers_display, intel_display, map_display],
        )
        # 刷新按钮
        refresh_dashboard_btn.click(fn=do_refresh_dashboard, inputs=[], outputs=[dashboard_display])
        refresh_powers_btn.click(fn=do_refresh_powers, inputs=[], outputs=[powers_display])
        refresh_history_btn.click(fn=do_refresh_history, inputs=[], outputs=[history_display])
        refresh_diary_btn.click(fn=do_refresh_diary, inputs=[], outputs=[diary_display])
        refresh_intel_btn.click(fn=do_refresh_intel, inputs=[], outputs=[intel_display])
        refresh_map_btn.click(fn=do_refresh_map, inputs=[], outputs=[map_display])

        # 初始化
        demo.load(
            fn=do_new_game,
            inputs=[],
            outputs=[ministers_display, history_display,
                     diary_display, dashboard_display, powers_display, intel_display, map_display],
        )

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=5199,
        share=False,
    )
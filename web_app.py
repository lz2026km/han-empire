"""汉献帝之末路 Gradio Web 交互界面。L8。"""

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
from han_sim.theme import get_theme_css

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

    def _bar(self, value: int, total: int = 100, width: int = 12) -> str:
        """渲染进度条 emoji。"""
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

        # 威权颜色
        if authority >= 50:
            auth_color = "#3b82f6"
        elif authority >= 20:
            auth_color = "#f59e0b"
        else:
            auth_color = "#ef4444"

        # 历史线进度
        dong_trapped = s.dong_zhuo_trapped_turn > 0 and s.dong_zhuo_killed_turn == 0
        dong_killed = s.dong_zhuo_killed_turn > 0
        dong_pct = 100 if dong_killed else (20 if dong_trapped else 0)
        dong_label = "已伏诛 ✓" if dong_killed else ("围困中" if dong_trapped else "未触发")

        escape_ongoing = s.emperor_escaped_turn > 0 and s.emperor_safe_turn == 0
        escape_done = s.emperor_safe_turn > 0
        if escape_done:
            esc_pct = 100
            esc_label = "已东归 ✓"
        elif escape_ongoing:
            esc_turns = s.turn - s.emperor_escaped_turn
            esc_pct = min(100, int((esc_turns / 5) * 100))
            esc_label = f"逃难中 · {esc_turns}/5回合"
        else:
            esc_pct = 0
            esc_label = "未触发"

        # 活跃事项
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
                <td style="padding:8px;border:1px solid #e5e7eb;text-align:center">
                    <div style="font-size:12px;color:#6b7280">汉室库（万两）</div>
                    <div style="font-size:24px;font-weight:bold">{han_ku}</div>
                </td>
                <td style="padding:8px;border:1px solid #e5e7eb;text-align:center">
                    <div style="font-size:12px;color:#6b7280">声望</div>
                    <div style="font-size:24px;font-weight:bold">{shengwang}</div>
                    <div style="font-size:11px">{self._bar(shengwang)}</div>
                </td>
                <td style="padding:8px;border:1px solid #e5e7eb;text-align:center">
                    <div style="font-size:12px;color:#6b7280">威权</div>
                    <div style="font-size:24px;font-weight:bold;color:{auth_color}">{authority}</div>
                    <div style="font-size:11px">{self._bar(authority)}</div>
                </td>
                <td style="padding:8px;border:1px solid #e5e7eb;text-align:center">
                    <div style="font-size:12px;color:#6b7280">藩镇</div>
                    <div style="font-size:24px;font-weight:bold">{fanzhen}</div>
                    <div style="font-size:11px">{self._bar(fanzhen)}</div>
                </td>
            </tr>
        </table>

        <h4 style="margin:12px 0 6px">📜 历史线</h4>
        <table style="width:100%;border-collapse:collapse">
            <tr>
                <td style="padding:4px 8px;font-size:13px">董卓伏诛线</td>
                <td style="padding:4px 8px">{self._bar(dong_pct)} {dong_label}</td>
            </tr>
            <tr>
                <td style="padding:4px 8px;font-size:13px">献帝东归线</td>
                <td style="padding:4px 8px">{self._bar(esc_pct)} {esc_label}</td>
            </tr>
        </table>

        <h4 style="margin:12px 0 6px">📋 待办事项</h4>
        <table style="width:100%;border-collapse:collapse;font-size:13px">
            <tr style="background:#f9fafb">
                <th style="padding:4px 8px;text-align:left">事项</th>
                <th style="padding:4px 8px;text-align:left">进度</th>
                <th style="padding:4px 8px;text-align:center">严重度</th>
            </tr>
            {issues_html}
        </table>
        </div>"""

    def _render_powers_html(self) -> str:
        """【势力】势力视图 HTML，按 stance 着色，含忠诚度。"""
        powers = self.session.db.list_powers()
        colors = {"loyal": "#3b82f6", "neutral": "#6b7280", "hostile": "#ef4444"}
        labels = {"loyal": "忠", "neutral": "中", "hostile": "敌"}
        rows = []
        for p in powers:
            color = colors.get(p.get("stance", "neutral"), "#6b7280")
            badge = labels.get(p.get("stance", "neutral"), "?")
            loyalty = p.get("loyalty", p.get("leverage", 50))
            if loyalty >= 70:
                loyalty_color = "#22c55e"
            elif loyalty >= 40:
                loyalty_color = "#f59e0b"
            else:
                loyalty_color = "#ef4444"
            rows.append(f"""<tr style="color:{color}">
                <td style="padding:4px 8px;font-weight:bold">{p.get('name','?')}</td>
                <td style="padding:4px 8px">{p.get('leader','?')}</td>
                <td style="padding:4px 8px;text-align:center">{badge}</td>
                <td style="padding:4px 8px;text-align:right">{p.get('military_strength',0)}</td>
                <td style="padding:4px 8px;text-align:right">{p.get('leverage',0)}</td>
                <td style="padding:4px 8px;text-align:center;font-weight:bold;color:{loyalty_color}">{loyalty}</td>
                <td style="padding:4px 8px;font-size:12px;color:#9ca3af">{p.get('last_action','按兵不动') or '按兵不动'}</td>
            </tr>""")

        header = """<tr style="background:#f3f4f6;font-size:12px">
            <th style="padding:4px 8px;text-align:left">势力</th>
            <th style="padding:4px 8px;text-align:left">首领</th>
            <th style="padding:4px 8px;text-align:center">立场</th>
            <th style="padding:4px 8px;text-align:right">军力</th>
            <th style="padding:4px 8px;text-align:right">威势</th>
            <th style="padding:4px 8px;text-align:center">忠诚度</th>
            <th style="padding:4px 8px;text-align:left">近动</th>
        </tr>"""

        return f"""<div style="font-family:system-ui,sans-serif">
        <table style="width:100%;border-collapse:collapse;font-size:13px">
            {header}
            {"".join(rows)}
        </table>
        <p style="font-size:12px;color:#9ca3af;margin-top:8px">
            🟦 忠 · 🟪 中立 · 🟥 敌对 · 军力/威势越高威胁越大 · 忠诚度：🟩70+ 🟨40-69 🟥<40
        </p>
        </div>"""

    def _render_ministers(self):
        """在朝大臣列表：带头像网格视图。"""
        ministers = self.session.get_active_ministers()
        if not ministers:
            return "<p style='color:#9ca3af;text-align:center'>无可用大臣</p>"
        return render_avatar_grid_html(ministers, cols=4, size=64)

    def _render_history(self):
        """召对历史：最近10回合，每回合展示关键对话。"""
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
        """【🗺️ 地图】SVG 十三州地图，动态标注势力与献帝位置。"""
        if not self.session:
            return "<p style='text-align:center;color:#9ca3af;padding:40px'>请先点击「新游戏」初始化</p>"

        s = self.session.state
        capital = getattr(s, 'capital', '洛阳')
        year = getattr(s, 'year', 189)
        period = getattr(s, 'period', '春')
        turn = getattr(s, 'turn', 1)

        # 转换 powers 为 map_view 需要的格式
        powers_raw = self.session.db.list_powers()
        powers = []
        for p in powers_raw:
            # 收集该势力控制的所有州
            regions = self.session.db.list_regions()
            controlled = []
            for r in regions:
                if r.get("controlled_by", "") == p.get("id", ""):
                    # region id → 州名映射（简化处理）
                    rid = r.get("id", "")
                    name_map = {
                        "youzhou": "幽州", "bingzhou": "并州", "yanzhou": "兖州",
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

        return _render_svg_map(
            capital=capital,
            year=year,
            period=period,
            turn=turn,
            powers=powers,
        )

        # 8州 + 司隶的 region_id 映射
        PROVINCE_ORDER = [
            "youzhou", "bingzhou", "yanzhou", "yuzhou",
            "jiujiang", "jingzhou", "yizhou", "liangzhou",
        ]
        PROVINCE_NAMES = {
            "youzhou": "幽", "bingzhou": "并", "yanzhou": "兖", "yuzhou": "豫",
            "jiujiang": "扬", "jingzhou": "荆", "yizhou": "益", "liangzhou": "凉",
        }

        regions = {r["id"]: r for r in self.session.db.list_regions()}
        powers = {p["id"]: p for p in self.session.db.list_powers()}

        def get_color(region_id: str) -> str:
            r = regions.get(region_id, {})
            controller = r.get("controlled_by", "")
            if controller == "han":
                return "#3b82f6"  # 忠蓝
            p = powers.get(controller, {})
            stance = p.get("stance", "neutral")
            return {"loyal": "#3b82f6", "neutral": "#6b7280", "hostile": "#ef4444"}.get(stance, "#6b7280")

        def get_label(region_id: str) -> str:
            r = regions.get(region_id, {})
            controller = r.get("controlled_by", "")
            if controller == "han":
                return "汉室"
            p = powers.get(controller, {})
            leader = p.get("leader", "")
            return leader[:2] if leader else controller[:2]

        # 8州 ASCII 行
        top_labels = "    " + "    ".join(PROVINCE_NAMES.get(pid, "") for pid in PROVINCE_ORDER)
        cell_colors = [get_color(pid) for pid in PROVINCE_ORDER]
        cell_labels = [get_label(pid) for pid in PROVINCE_ORDER]

        # 上边框
        border_row = "  ┌" + "───┬" * 7 + "───┐"
        # 数据行：每个格子两行（名字+驻军）
        name_row = "  │" + "│".join(f"{cell_labels[i]:^3}" for i in range(8)) + "│"
        garrison_row = "  │" + "│".join(f"  {PROVINCE_NAMES[PROVINCE_ORDER[i]]} " for i in range(8)) + "│"
        bottom_row = "  └" + "───┴" * 7 + "───┘"

        # 驻军数字：找 armies 里 station 为该州的
        armies = self.session.db.list_armies()
        garrison_info = {}
        for a in armies:
            station = a.get("station", "")
            if station:
                garrison_info[station] = garrison_info.get(station, 0) + a.get("manpower", 0)

        cells_html = []
        for i, pid in enumerate(PROVINCE_ORDER):
            color = cell_colors[i]
            label = cell_labels[i]
            region_name = PROVINCE_NAMES.get(pid, pid)
            garrison = garrison_info.get(pid, 0)
            cells_html.append(
                f"<td style='border:1px solid #e5e7eb;padding:6px 4px;text-align:center;background:#f9fafb'>"
                f"<div style='font-weight:bold;color:{color}'>{label}</div>"
                f"<div style='font-size:11px;color:#9ca3af'>{region_name}州</div>"
                f"<div style='font-size:11px'>兵:{garrison}</div>"
                f"</td>"
            )

        # 司隶
        sili_region = regions.get("luoyang", {})
        sili_controller = sili_region.get("controlled_by", "")
        sili_color = get_color("luoyang")
        sili_power = powers.get(sili_controller, {})
        sili_label = sili_power.get("leader", "")[:2] if sili_power else "未知"

        sili_html = (
            f"<div style='margin-top:12px;text-align:center'>"
            f"<div style='font-size:13px;font-weight:bold'>司隶（长安/洛阳）</div>"
            f"<div style='color:{sili_color}'>[{sili_label} 控制]</div>"
            f"</div>"
        )

        table_html = (
            "<pre style='font-family:monospace;font-size:13px;line-height:1.4'>"
            f"{top_labels}\n"
            f"{border_row}\n"
            f"{name_row}\n"
            f"{garrison_row}\n"
            f"{bottom_row}"
            "</pre>"
        )

        # 州份详细信息
        detail_rows = []
        for pid in PROVINCE_ORDER:
            r = regions.get(pid, {})
            controller = r.get("controlled_by", "")
            p = powers.get(controller, {})
            stance = p.get("stance", "neutral")
            color = get_color(pid)
            stance_label = {"loyal": "忠", "neutral": "中", "hostile": "敌"}.get(stance, "?")
            name = PROVINCE_NAMES.get(pid, pid)
            garrison = garrison_info.get(pid, 0)
            pop = r.get("population", 0)
            detail_rows.append(
                f"<tr style='color:{color}'>"
                f"<td style='padding:4px 8px'>{name}州</td>"
                f"<td style='padding:4px 8px'>{p.get('leader', '无') or '无'}</td>"
                f"<td style='padding:4px 8px;text-align:center'>{stance_label}</td>"
                f"<td style='padding:4px 8px;text-align:right'>{garrison}</td>"
                f"<td style='padding:4px 8px;text-align:right'>{pop}</td>"
                f"</tr>"
            )

        legend_html = (
            "<div style='margin-top:8px;font-size:12px'>"
            "<span style='color:#3b82f6'>🟦 忠</span> · "
            "<span style='color:#6b7280'>🟪 中立</span> · "
            "<span style='color:#ef4444'>🟥 敌对</span>"
            "</div>"
        )

        return (
            "<div style='font-family:system-ui,sans-serif'>"
            f"<h4 style='margin:8px 0 4px'>🗺️ 天下大势</h4>"
            f"{table_html}"
            f"{sili_html}"
            "<table style='width:100%;border-collapse:collapse;font-size:13px;margin-top:12px'>"
            "<tr style='background:#f3f4f6;font-size:12px'>"
            "<th style='padding:4px 8px;text-align:left'>州</th>"
            "<th style='padding:4px 8px;text-align:left'>太守/控制者</th>"
            "<th style='padding:4px 8px;text-align:center'>立场</th>"
            "<th style='padding:4px 8px;text-align:right'>驻军</th>"
            "<th style='padding:4px 8px;text-align:right'>人口</th>"
            "</tr>"
            + "".join(detail_rows)
            + "</table>"
            + legend_html
            + "</div>"
        )

    def _render_intel_html(self) -> str:
        """【情报】视图 HTML：军力排行 ASCII 条形图 + 联盟关系 + 密探情报（威权≥40解锁）。"""
        if not self.session:
            return "<p>请先点击「新游戏」初始化</p>"
        from han_sim.tools import (
            estimate_military_strength,
            inspect_warlord_alliances,
            check_dongzhuo_trap_status,
            audit_imperial_treasury,
        )

        s = self.session.state
        db = self.session.db
        authority = s.metrics.get("威权", 0)
        intel_unlocked = authority >= 40

        # 军力排行榜
        powers = db.list_powers()
        # 按军力排序
        sorted_powers = sorted(
            [p for p in powers if p.get("id") != "han"],
            key=lambda x: int(x.get("military_strength", 0)),
            reverse=True,
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

        intel_section = ""
        if intel_unlocked:
            intel_section += f"<p style='color:#22c55e'>🔓 密探已解锁（威权{authority}≥40）</p>"
        else:
            intel_section += f"<p style='color:#9ca3af'>🔒 密探未解锁（威权需≥40，当前{authority}）</p>"

        # 董卓伏诛线状态
        trap_status = check_dongzhuo_trap_status(s)
        trap_desc = trap_status.get("description", "")
        trap_color = "#22c55e" if trap_status.get("status") == "伏诛成功" else ("#f59e0b" if trap_status.get("status") == "围困中" else "#6b7280")
        intel_section += f"<p style='font-size:13px'>📍 董卓伏诛线：<span style='color:{trap_color}'>{trap_desc}</span></p>"

        # 财政账目
        treasury = audit_imperial_treasury(db, s)
        han_ku = treasury.get("汉室库", 0)
        nei_ku = treasury.get("内库", 0)
        intel_section += f"<p style='font-size:13px'>💰 汉室库：{han_ku}万两 · 内库：{nei_ku}万两</p>"

        return f"""<div style="font-family:system-ui,sans-serif">
        <h4 style="margin:8px 0 4px">⚔️ 诸侯军力排行</h4>
        <table style="width:100%;border-collapse:collapse;font-size:13px">
            <tr style="background:#f3f4f6;font-size:12px">
                <th style="padding:4px 8px;text-align:left">势力</th>
                <th style="padding:4px 8px;text-align:left">军力条</th>
                <th style="padding:4px 8px;text-align:right">军力</th>
                <th style="padding:4px 8px;text-align:right">威势</th>
            </tr>
            {"".join(rows_html)}
        </table>
        <h4 style="margin:12px 0 4px">🕵️ 情报摘要</h4>
        {intel_section}
        <p style="font-size:12px;color:#9ca3af">🟦 忠诚 · 🟪 中立 · 🟥 敌对</p>
        </div>"""

    def _render_diary_html(self) -> str:
        """【日志】天子日记视图：日记体显示。"""
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
            lines.append(
                f"<p style='margin:4px 0'><b>第{turn}回合 · {year}年{period}月</b>：{content[:80]}</p>"
            )
        return f"""<div style="font-family:system-ui,sans-serif">
        <h4 style="margin:8px 0 6px">📖 天子日记</h4>
        {"".join(lines)}
        </div>"""

    def cmd_summon(self, minister_name: str, question: str):
        if not self.session:
            return "❗ 请先点击 **新游戏** 开始。"
        if not minister_name:
            return "❗ 请选择或输入大臣姓名。"
        q = question.strip() or "本月局势如何？"
        try:
            result = self.session.summon_minister(minister_name, q)
            # 查找大臣头像
            ministers = self.session.get_active_ministers()
            minister_data = next((m for m in ministers if m["name"] == minister_name), {})
            portrait_html = ""
            if minister_data:
                portrait_html = render_portrait_with_name_html(
                    name=minister_data.get("name", ""),
                    office=minister_data.get("office", ""),
                    office_type=minister_data.get("office_type", "default"),
                    portrait_id=minister_data.get("portrait_id", ""),
                    show_name=False,
                    size=80,
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

        # 特殊诏书：衣带密诏走独立逻辑
        if intent == "衣带密诏":
            from han_sim.decree import issue_secret_edict
            result = issue_secret_edict(self.session.state, self.session.db)
            d = result.decree
            lines = [
                f"**【{'衣带密诏已下' if d.full_text else '衣带密诏失败'}】**",
                "",
            ]
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
            lines = [
                f"**【诏书已下】《{d.decree_type}》**",
                "",
                d.full_text,
                "",
                f"_下达原因：{intent}_",
            ]
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

    def cmd_relocate_capital(self, new_capital: str):
        if not self.session:
            return "❗ 请先点击 **新游戏** 开始。"
        from han_sim.flows import relocate_capital, _CAPITAL_EFFECTS
        old = self.session.state.capital
        if old == new_capital:
            return f"ℹ️ 当前就在 **{old}**，无需迁都。"
        # 迁都费用：50万两
        cost = 50
        han_ku = self.session.state.metrics.get("汉室库", 0)
        if han_ku < cost:
            return f"❗ 迁都需要 {cost} 万两，汉室库仅剩 {han_ku} 万两，不足以迁都。"
        delta = relocate_capital(self.session.state, new_capital)
        self.session.state.metrics["汉室库"] -= cost
        effects_desc = "，".join([f"{k}{v:+d}" for k, v in delta.items() if v != 0])
        return f"🏛️ **迁都成功**：{old} → **{new_capital}**，消耗 {cost} 万两。指标变化：{effects_desc}"

    def cmd_inspect_power(self, power_name: str):
        if not self.session:
            return "❗ 请先点击 **新游戏**。"
        if not power_name:
            return "ℹ️ 请输入势力名称（如：曹操）。"
        from han_sim.tools import inspect_warlord_alliances
        powers = self.session.db.list_powers()
        matched = [p for p in powers if power_name in p.get("name", "") or power_name in p.get("leader", "")]
        if not matched:
            return f"❗ 未找到势力「{power_name}」。可用势力：{'、'.join(p['name'] for p in powers[:10])}"
        p = matched[0]
        alliances = inspect_warlord_alliances(self.session.db, p["name"])
        loyalty = p.get("loyalty", p.get("leverage", 50))
        loyalty_color = "#22c55e" if loyalty >= 70 else "#f59e0b" if loyalty >= 40 else "#ef4444"
        alliance_text = ""
        if alliances.get("alliances"):
            alliance_text = "<br>".join([f"与 **{a['name']}**（{a['type']}）" for a in alliances["alliances"][:5]])
        elif alliances.get("enemies"):
            alliance_text = "<br>".join([f"敌视 **{e['name']}**" for e in alliances["enemies"][:5]])
        return f"""<div style="font-family:system-ui,sans-serif;padding:12px;background:#f9fafb;border-radius:8px">
            <h4 style="margin:0 0 8px">{p['name']} — {p.get('leader','?')}</h4>
            <table style="width:100%;font-size:13px">
                <tr><td style="padding:4px"><b>立场</b></td><td>{p.get('stance','?')}</td></tr>
                <tr><td style="padding:4px"><b>军力</b></td><td>{p.get('military_strength',0)}</td></tr>
                <tr><td style="padding:4px"><b>威势</b></td><td>{p.get('leverage',0)}</td></tr>
                <tr><td style="padding:4px"><b>忠诚度</b></td><td style="color:{loyalty_color};font-weight:bold">{loyalty}</td></tr>
                <tr><td style="padding:4px"><b>据点</b></td><td>{p.get('base','?')}</td></tr>
                <tr><td style="padding:4px"><b>近动</b></td><td>{p.get('last_action','按兵不动')}</td></tr>
            </table>
            <h5 style="margin:8px 0 4px">关系</h5>
            <p style="font-size:13px">{alliance_text or '暂无结盟/敌对信息'}</p>
        </div>"""

    def _render_skills_html(self):
        """【技能Tab】技能列表HTML，含已学/未学状态。"""
        from han_sim.content import load_game_content
        all_skills = load_game_content().load_emperor_skills()
        acquired = {s["skill_id"] for s in self.session.db.list_acquired_skills(self.session.campaign_id)}
        pts = self.session.state.metrics.get("skill_points", 0)
        pts_html = f"<div style='font-size:16px;font-weight:bold;color:#3b82f6'>剩余技能点：{pts}</div>"

        categories = {}
        for s in all_skills:
            cat = s.get("category", "其他")
            categories.setdefault(cat, []).append(s)

        rows_html = ""
        for cat, skills in categories.items():
            rows_html += f"<tr style='background:#1e293b;color:#94a3b8;font-size:12px'><td colspan=4 style='padding:4px 8px'>{cat}</td></tr>"
            for s in skills:
                sid = s["id"]
                learned = sid in acquired
                cost = s.get("cost", 0)
                can_learn = not learned and pts >= cost
                row_color = "#166534" if learned else ("#854d0e" if can_learn else "#1f2937")
                row_bg = "#14532d" if learned else ("#713f12" if can_learn else "#111")
                name = s.get("name", "?")
                desc = s.get("description", "")
                if len(desc) > 60:
                    desc = desc[:60] + "…"
                status = "✅ 已学" if learned else (f"📖 {cost}点可学" if can_learn else f"🔒 需{cost}点")
                rows_html += f"""<tr style="background:{row_bg};color:#e2e8f0">
                    <td style="padding:6px 8px;font-weight:bold;color:#fbbf24">{name}</td>
                    <td style="padding:6px 8px;font-size:12px">{desc}</td>
                    <td style="padding:6px 8px;text-align:center">{cost}点</td>
                    <td style="padding:6px 8px;text-align:center">{status}</td>
                </tr>"""

        skills_html = f"""<div style="font-family:system-ui,sans-serif">
            {pts_html}
            <table style="width:100%;border-collapse:collapse;font-size:13px;margin-top:8px">
                <tr style="background:#1e293b;color:#94a3b8;font-size:12px">
                    <th style="padding:6px 8px;text-align:left">技能名</th>
                    <th style="padding:6px 8px;text-align:left">效果</th>
                    <th style="padding:6px 8px;text-align:center">消耗</th>
                    <th style="padding:6px 8px;text-align:center">状态</th>
                </tr>
                {rows_html}
            </table>
        </div>"""
        return pts_html, skills_html

    def cmd_learn_skill(self, skill_name: str):
        if not self.session:
            return "❗ 请先点击 **新游戏**。"
        from han_sim.content import load_game_content
        all_skills = load_game_content().load_emperor_skills()
        matched = [s for s in all_skills if skill_name == s.get("name", "")]
        if not matched:
            return f"❗ 未找到技能「{skill_name}」。可用：{'、'.join(s['name'] for s in all_skills[:15])}"
        s = matched[0]
        sid = s["id"]
        cost = s.get("cost", 0)
        pts = self.session.state.metrics.get("skill_points", 0)
        if pts < cost:
            return f"❗ 技能「{s['name']}」需要 {cost} 点，当前仅剩 {pts} 点。"
        acquired = {x["skill_id"] for x in self.session.db.list_acquired_skills(self.session.campaign_id)}
        if sid in acquired:
            return f"ℹ️ 技能「{s['name']}」已经学会了。"
        ok = self.session.db.activate_skill(self.session.campaign_id, sid, self.session.state.turn)
        if ok:
            self.session.state.metrics["skill_points"] -= cost
            return f"✅ 学会了 **{s['name']}**（消耗 {cost} 点，剩余 {pts - cost} 点）。"
        return f"❗ 学习失败。"

    def cmd_forget_skill(self, skill_name: str):
        if not self.session:
            return "❗ 请先点击 **新游戏**。"
        from han_sim.content import load_game_content
        all_skills = load_game_content().load_emperor_skills()
        matched = [s for s in all_skills if skill_name == s.get("name", "")]
        if not matched:
            return f"❗ 未找到技能「{skill_name}」。"
        s = matched[0]
        sid = s["id"]
        acquired = {x["skill_id"] for x in self.session.db.list_acquired_skills(self.session.campaign_id)}
        if sid not in acquired:
            return f"ℹ️ 技能「{s['name']}」尚未学会，无需遗忘。"
        ok = self.session.db.deactivate_skill(self.session.campaign_id, sid)
        if ok:
            refund = s.get("cost", 0)
            self.session.state.metrics["skill_points"] += refund
            return f"🔄 遗忘了 **{s['name']}**（返还 {refund} 点）。"
        return f"❗ 遗忘失败。"

    def cmd_inspect_issue(self, issue_name: str):
        if not self.session:
            return "❗ 请先点击 **新游戏**。"
        if not issue_name:
            return "ℹ️ 请输入事项名称。"
        issues = self.session.db.get_active_issues()
        matched = [i for i in issues if issue_name in i.get("title", "")]
        if not matched:
            # 搜索所有活跃事项的标题
            all_active = self.session.db.get_active_issues()
            matched = [i for i in all_active if issue_name.lower() in i.get("title", "").lower()]
        if not matched:
            return f"❗ 未找到事项「{issue_name}」。可用：{'、'.join(i['title'][:10] for i in issues[:8])}"
        iss = matched[0]
        sev = iss.get("severity", 50)
        sev_color = "#ef4444" if sev >= 70 else "#f59e0b" if sev >= 40 else "#6b7280"
        bar = int(iss.get("bar_value", 40))
        kind = iss.get("kind", "?")
        status = iss.get("status", "active")
        inertia = iss.get("inertia", 0)
        return f"""<div style="font-family:system-ui,sans-serif;padding:12px;background:#f9fafb;border-radius:8px">
            <h4 style="margin:0 0 8px">{iss.get('title','')}</h4>
            <table style="width:100%;font-size:13px">
                <tr><td style="padding:4px"><b>类型</b></td><td>{kind}</td></tr>
                <tr><td style="padding:4px"><b>状态</b></td><td>{status}</td></tr>
                <tr><td style="padding:4px"><b>严重度</b></td><td style="color:{sev_color};font-weight:bold">{sev}</td></tr>
                <tr><td style="padding:4px"><b>进度</b></td><td>{self._bar(bar)} {bar}%</td></tr>
                <tr><td style="padding:4px"><b>惯性</b></td><td>{inertia}</td></tr>
            </table>
            <p style="font-size:13px;color:#374151;margin-top:8px">{iss.get('summary', iss.get('description', '无描述'))}</p>
        </div>"""


# ── Gradio UI ──────────────────────────────────────────────────────────
def build_ui():
    ui = GameUI()

    with gr.Blocks(title="汉献帝之末路") as demo:
        gr.Markdown("# 👑 汉献帝之末路")
        gr.Markdown("_189年，董卓进京，废少帝立献帝。名为天子，实为阶下囚。_")
        gr.Markdown(HELP)

        with gr.Tabs():
            # ── Tab1: 总览仪表盘 ────────────────────────────────
            with gr.TabItem("📊 总览"):
                gr.Markdown("### 📊 汉室国势")
                dashboard_display = gr.HTML("*点击「新游戏」初始化*")
                refresh_dashboard_btn = gr.Button("🔄 刷新总览")

                gr.Markdown("### 🏛️ 迁都")
                capital_label = gr.HTML("<span id='capital-display'>**当前都城：洛阳**</span>")
                gr.Markdown("*选择目标迁都（消耗金钱和时间）*")
                with gr.Row():
                    relocate_btn洛阳 = gr.Button("🏯 洛阳", variant="primary")
                    relocate_btn许昌 = gr.Button("⚔️ 许昌（+威权+藩镇）")
                    relocate_btn长安 = gr.Button("🗼 长安（-威权-藩镇）")
                    relocate_btn邺城 = gr.Button("🏰 邺城（-威权）")
                relocate_output = gr.HTML()

                gr.Markdown("### 📋 事项追踪")
                with gr.Row():
                    issue_name_input = gr.Textbox(label="输入事项名查看详情", placeholder="如：董卓进京", scale=1)
                    inspect_issue_btn = gr.Button("🔍 详情", scale=0)
                issue_detail_display = gr.HTML("")

            # ── Tab2: 召对（现用召见大臣）────────────────────
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

            # ── Tab3: 诏书 ─────────────────────────────────
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

            # ── Tab4: 势力视图 ───────────────────────────────
            with gr.TabItem("⚔️ 势力"):
                gr.Markdown("### ⚔️ 天下诸侯")
                with gr.Row():
                    power_name_input = gr.Textbox(label="输入势力名称查看详情", placeholder="如：曹操", scale=1)
                    inspect_power_btn = gr.Button("🔍 详情", scale=0)
                powers_display = gr.HTML("*点击「新游戏」初始化*")
                refresh_powers_btn = gr.Button("🔄 刷新势力")
                power_detail_display = gr.HTML("")

            # ── Tab5: 历史 ─────────────────────────────────
            with gr.TabItem("📖 历史"):
                gr.Markdown("### 📖 召对历史")
                history_display = gr.Markdown("*召对记录将显示在这里*")
                refresh_history_btn = gr.Button("🔄 刷新召对记录")

            # ── Tab6: 日志/日记 ──────────────────────────────────
            with gr.TabItem("📋 日志"):
                gr.Markdown("### 📖 天子日记")
                diary_display = gr.HTML("*天子日记将显示在这里*")
                refresh_diary_btn = gr.Button("🔄 刷新日记")

            # ── Tab7: 情报 ────────────────────────────────────────────
            with gr.TabItem("🕵️ 情报"):
                gr.Markdown("### 🕵️ 军情/情报系统")
                intel_display = gr.HTML("*点击「新游戏」初始化情报视图*")
                refresh_intel_btn = gr.Button("🔄 刷新情报")

            # ── Tab8: 地图 ────────────────────────────────────────────
            with gr.TabItem("🗺️ 地图"):
                gr.Markdown("### 🗺️ 天下大势（点击州名查看详情）")
                map_display = gr.HTML("*点击「新游戏」初始化地图*")
                refresh_map_btn = gr.Button("🔄 刷新地图")

            # ── Tab9: 天子技能 ────────────────────────────────────────
            with gr.TabItem("⚡ 技能"):
                gr.Markdown("### ⚡ 天子技能")
                skill_points_display = gr.HTML("*点击「新游戏」加载*")
                skill_list_display = gr.HTML("*点击「新游戏」加载*")
                with gr.Row():
                    learn_skill_btn = gr.Button("📖 学习技能", variant="primary")
                    forget_skill_btn = gr.Button("❌ 遗忘技能")
                skill_action_output = gr.HTML("")
                skill_name_input = gr.Textbox(label="输入技能名（精确）学习或遗忘", placeholder="如：知己知彼", scale=1)

        gr.Markdown("---")

        gr.Markdown("### 👥 在朝大臣")
        ministers_display = gr.Markdown("*点击「新游戏」查看*")

        gr.Markdown("---")

        with gr.Row():
            review_btn = gr.Button("⏭️ 月末推演（推进到下月）", variant="stop", size="lg")
        review_output = gr.Markdown()

        gr.Markdown("---")

        with gr.Row():
            new_game_btn = gr.Button("🆕 新游戏", variant="secondary")

        # ── 事件绑定 ──────────────────────────────────────────────
        def do_new_game():
            out = ui.new_game()
            ministers = ui._render_ministers()
            history = ui._render_history()
            diary = ui._render_diary_html()
            dash = ui._render_dashboard_html()
            powers = ui._render_powers_html()
            intel = ui._render_intel_html()
            map_html = ui._render_map_html()
            pts_html, skills_html = ui._render_skills_html()
            return out, ministers, history, diary, dash, powers, intel, map_html, pts_html, skills_html, f"<b style='color:#3b82f6'>当前都城：{ui.session.state.capital}</b>"

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

        def do_refresh_skills():
            return ui._render_skills_html()

        def do_learn_skill(name: str):
            result = ui.cmd_learn_skill(name)
            pts, skills = ui._render_skills_html()
            return result, pts, skills

        def do_forget_skill(name: str):
            result = ui.cmd_forget_skill(name)
            pts, skills = ui._render_skills_html()
            return result, pts, skills

        learn_skill_btn.click(fn=do_learn_skill, inputs=[skill_name_input],
                             outputs=[skill_action_output, skill_points_display, skill_list_display])
        forget_skill_btn.click(fn=do_forget_skill, inputs=[skill_name_input],
                               outputs=[skill_action_output, skill_points_display, skill_list_display])

        summon_btn.click(
            fn=ui.cmd_summon,
            inputs=[minister_input, question_input],
            outputs=summon_output,
        )
        decree_btn.click(
            fn=ui.cmd_decree,
            inputs=[intent_input],
            outputs=decree_output,
        )
        review_btn.click(
            fn=ui.cmd_review,
            inputs=[],
            outputs=review_output,
        )
        new_game_btn.click(
            fn=do_new_game,
            inputs=[],
            outputs=[ministers_display, history_display,
                     diary_display, dashboard_display, powers_display, intel_display, map_display],
        )
        refresh_dashboard_btn.click(
            fn=do_refresh_dashboard,
            inputs=[],
            outputs=dashboard_display,
        )
        refresh_powers_btn.click(
            fn=do_refresh_powers,
            inputs=[],
            outputs=powers_display,
        )
        inspect_power_btn.click(
            fn=ui.cmd_inspect_power,
            inputs=[power_name_input],
            outputs=power_detail_display,
        )
        inspect_issue_btn.click(
            fn=ui.cmd_inspect_issue,
            inputs=[issue_name_input],
            outputs=issue_detail_display,
        )
        refresh_history_btn.click(
            fn=do_refresh_history,
            inputs=[],
            outputs=history_display,
        )
        refresh_diary_btn.click(
            fn=do_refresh_diary,
            inputs=[],
            outputs=diary_display,
        )
        refresh_intel_btn.click(
            fn=do_refresh_intel,
            inputs=[],
            outputs=intel_display,
        )
        refresh_map_btn.click(
            fn=do_refresh_map,
            inputs=[],
            outputs=map_display,
        )

        def do_relocate(capital_name: str):
            result = ui.cmd_relocate_capital(capital_name)
            dash = ui._render_dashboard_html()
            capital_display = f"<b style='color:#3b82f6'>当前都城：{ui.session.state.capital}</b>"
            return result, dash, capital_display

        relocate_btn洛阳.click(fn=lambda: do_relocate("洛阳"), outputs=[relocate_output, dashboard_display, capital_label])
        relocate_btn许昌.click(fn=lambda: do_relocate("许昌"), outputs=[relocate_output, dashboard_display, capital_label])
        relocate_btn长安.click(fn=lambda: do_relocate("长安"), outputs=[relocate_output, dashboard_display, capital_label])
        relocate_btn邺城.click(fn=lambda: do_relocate("邺城"), outputs=[relocate_output, dashboard_display, capital_label])

        # 初始化
        demo.load(
            fn=do_new_game,
            inputs=[],
            outputs=[ministers_display, history_display,
                     diary_display, dashboard_display, powers_display, intel_display, map_display, skill_points_display, skill_list_display, capital_label],
        )

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=5199,
        share=False,
        css=get_theme_css(),
    )
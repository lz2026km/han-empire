"""大臣 Agent 工具集：查询工具 + court tools（拟旨/退下/换人）。L5。

基于 ming_sim/tools.py 改编为汉末版本。
"""

from __future__ import annotations

import difflib
import json
import re
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from han_sim.models import CourtContext
    from han_sim.context import _ctx as _content_ctx

_STATUS_CN = {
    "active": "在朝",
    "dismissed": "已罢黜",
    "imprisoned": "下狱",
    "exiled": "流放",
    "retired": "致仕",
    "dead": "已故",
}


def _normalize_person_name(text: str) -> str:
    return re.sub(r"\s+", "", str(text or "").strip())


def _match_character_by_name(name: str, characters: List[Dict]) -> Dict | None:
    key = _normalize_person_name(name)
    if not key:
        return None
    # 精确匹配
    for c in characters:
        names = [c.get("name", ""), *(c.get("aliases", []) or [])]
        if any(_normalize_person_name(n) == key for n in names):
            return c
    # 包含匹配
    for c in characters:
        names = [c.get("name", ""), *(c.get("aliases", []) or [])]
        if any(key in _normalize_person_name(n) or _normalize_person_name(n) in key for n in names):
            return c
    # 模糊匹配
    choices = {c.get("name", ""): c for c in characters}
    match = difflib.get_close_matches(key, list(choices.keys()), n=1, cutoff=0.6)
    return choices[match[0]] if match else None


def _duty_location(office: str, office_type: str, status: str) -> str:
    if status == "dead":
        return "已故，不在任事。"
    if status == "imprisoned":
        return "系狱待勘。"
    if status in {"dismissed", "exiled", "retired", "offstage"}:
        return "不在朝任事。"
    text = office or office_type
    if not text:
        return "在朝但现职未明。"
    region_markers = ["司隶", "豫州", "兖州", "徐州", "扬州", "荆州", "益州", "凉州", "并州", "幽州", "冀州", "青州"]
    for marker in region_markers:
        if marker in text:
            return f"按现职在{marker}任事。"
    if office_type in {"三公", "九卿", "尚书", "御史", "太尉", "司徒", "司空", "大将军", "侍中", "散骑"}:
        return f"按现职在朝。"
    if office_type == "太守":
        return f"按现职为{office}。"
    if office_type == "刺史":
        return f"按现职刺{office}。"
    return "按现职任事。"


def build_minister_tools(character: Dict, context: "CourtContext"):
    """构建大臣可用的工具集。"""
    characters = [c for c in context.characters.values() if c.get("office_type") != "后宫"]

    def view_state() -> str:
        """查看当前汉室核心国势数值（含派系/阶级/势力）。"""
        return context.state_summary()

    def list_court() -> str:
        """查在朝（及被罢/下狱/流放/致仕）官员名册。"""
        lines = []
        for c in characters:
            if getattr(c, "power_id", "han") != "han":
                continue
            status = context.db.get_character_status(c.get("name", ""))
            tag = _STATUS_CN.get(status, status)
            suffix = "" if status == "active" else f"（{tag}）"
            lines.append(f"{c.get('name', '')}：{c.get('office', '')}，{c.get('faction', '')}{suffix}")
        return "在朝官员名册：\n" + "\n".join(lines)

    def list_personnel() -> str:
        """查看当前人事总表。"""
        lines = []
        for c in characters:
            if getattr(c, "power_id", "han") != "han":
                continue
            status = context.db.get_character_status(c.get("name", ""))
            tag = _STATUS_CN.get(status, status)
            location = _duty_location(c.get("office", ""), c.get("office_type", ""), status)
            lines.append(f"{c.get('name', '')}：{c.get('office', '无官')}，{c.get('faction', '')}，{tag}，{location}")
        return f"当前：{context.state.year}年。\n人事总表：\n" + "\n".join(lines)

    def inspect_minister(name: str) -> str:
        """查某位官员的现任官职、派系、当前状态。"""
        target = _match_character_by_name(name, characters)
        if target is None:
            return f"名册中无『{name}』。可先调 list_personnel/list_court 看在朝官员名单。"
        status = context.db.get_character_status(target.get("name", ""))
        tag = _STATUS_CN.get(status, status)
        location = _duty_location(target.get("office", ""), target.get("office_type", ""), status)
        out = (
            f"{target.get('name', '')}："
            f"现职{target.get('office', '')}，"
            f"职位类型{target.get('office_type', '')}，"
            f"派系{target.get('faction', '')}，状态{tag}。"
            f"任事处：{location}"
        )
        if target.get("summary"):
            out += f"简介：{target.get('summary', '')}"
        return out

    def list_regions() -> str:
        """查看诸州概况。"""
        regions = context.db.list_regions()
        if not regions:
            return "暂无地区数据。"
        lines = ["诸州概况："]
        for r in regions[:8]:
            lines.append(
                f"- {r.get('name', r.get('id', ''))}："
                f"民心{r.get('public_support', 0)}，"
                f"动乱{r.get('unrest', 0)}，"
                f"税收{r.get('tax_per_turn', 0)}，"
                f"掌控：{r.get('controlled_by', '汉室')}"
            )
        return "\n".join(lines)

    def inspect_region(region_name: str) -> str:
        """查某一地区详情。"""
        regions = context.db.list_regions()
        for r in regions:
            if region_name in (r.get("name", ""), r.get("id", "")):
                return (
                    f"{r.get('name', '')}（{r.get('id', '')}）：\n"
                    f"  人口{r.get('population', 0)}万，"
                    f"民心{r.get('public_support', 0)}，"
                    f"动乱{r.get('unrest', 0)}\n"
                    f"  自然灾害：{r.get('natural_disaster', '无')}，"
                    f"人祸：{r.get('human_disaster', '无')}\n"
                    f"  掌控势力：{r.get('controlled_by', '汉室')}，"
                    f"税收{r.get('tax_per_turn', 0)}，"
                    f"粮储{r.get('grain_security', 0)}万石\n"
                    f"  状态：{r.get('status', '安稳')}"
                )
        return f"未找到地区 '{region_name}'。"

    def list_armies() -> str:
        """查看主要军队。"""
        armies = context.db.list_armies()
        if not armies:
            return "暂无军队数据。"
        lines = ["主要军队："]
        for a in armies[:8]:
            lines.append(
                f"- {a.get('name', a.get('id', ''))}："
                f"统帅{a.get('commander', '无')}，"
                f"兵额{a.get('manpower', 0)}，"
                f"驻地{a.get('station', '未知')}，"
                f"欠饷{a.get('arrears', 0)}，"
                f"士气{a.get('morale', 0)}"
            )
        return "\n".join(lines)

    def inspect_army(army_name: str) -> str:
        """查某支军队详情。"""
        armies = context.db.list_armies()
        for a in armies:
            if army_name in (a.get("name", ""), a.get("id", "")):
                return (
                    f"{a.get('name', '')}：\n"
                    f"  统帅{a.get('commander', '无')}，"
                    f"驻地{a.get('station', '未知')}，"
                    f"兵种{a.get('troop_type', '步兵')}\n"
                    f"  兵额{a.get('manpower', 0)}，"
                    f"月饷{a.get('maintenance_per_turn', 0)}，"
                    f"补给{a.get('supply', 0)}，"
                    f"士气{a.get('morale', 0)}\n"
                    f"  训练{a.get('training', 0)}，"
                    f"装备{a.get('equipment', 0)}，"
                    f"欠饷{a.get('arrears', 0)}，"
                    f"机动{a.get('mobility', 0)}\n"
                    f"  归属{a.get('owner_power', '汉室')}，"
                    f"状态：{a.get('status', '驻守')}"
                )
        return f"未找到军队 '{army_name}'。"

    def list_powers() -> str:
        """查看各路诸侯与外族势力。"""
        powers = context.db.list_powers()
        if not powers:
            return "暂无势力数据。"
        lines = ["各路势力："]
        for p in powers[:10]:
            lines.append(
                f"- {p.get('name', p.get('id', ''))}（{p.get('leader', '无领袖')}）："
                f"威势{p.get('leverage', 0)}，"
                f"兵力{p.get('military_strength', 0)}，"
                f"态度{p.get('stance', '未知')}"
            )
        return "\n".join(lines)

    def inspect_power(power_name: str) -> str:
        """查某势力详情。"""
        powers = context.db.list_powers()
        for p in powers:
            if power_name in (p.get("name", ""), p.get("id", "")):
                return (
                    f"{p.get('name', '')}：\n"
                    f"  领袖{p.get('leader', '无')}，"
                    f"威势{p.get('leverage', 0)}，"
                    f"兵力{p.get('military_strength', 0)}\n"
                    f"  态度{p.get('stance', '未知')}，"
                    f"上次动作{p.get('last_action', '无')}，"
                    f"状态{p.get('status', '活跃')}"
                )
        return f"未找到势力 '{power_name}'。"

    def list_issues() -> str:
        """查看当前在办事项。"""
        issues = context.db.get_active_issues()
        if not issues:
            return "本回合无在办事项。"
        lines = ["在办事项："]
        for idx, iss in enumerate(issues, 1):
            lines.append(f"  {idx}. #{iss.get('id', '')} {iss.get('title', '')}（{iss.get('status', '')}）")
        return "\n".join(lines)

    def search_memories(keywords: str) -> str:
        """检索相关旧事记忆摘要。"""
        kw_list = [k.strip() for k in str(keywords or "").split(",") if k.strip()]
        if not kw_list:
            return "请提供关键词（逗号分隔）。"
        memories = context.db.get_memories_by_keywords(kw_list, turn=context.state.turn, limit=8)
        if not memories:
            return f"未找到与「{'、'.join(kw_list)}」相关的旧事记忆。"
        lines = [f"【旧事检索：{' '.join(kw_list)}】"]
        for m in memories:
            lines.append(
                f"- #{m.get('id', '')} {m.get('subject_id', '')}："
                f"{m.get('title', '')}。起因：{m.get('cause', '')}。结果：{m.get('outcome', '')}。"
            )
        return "\n".join(lines)

    def recall_memories_by_time(year: int, keywords: str = "") -> str:
        """按年回忆历史旧事。"""
        turn = (int(year) - 189) * 12 + 1
        kw_list = [k.strip() for k in str(keywords or "").split(",") if k.strip()]
        memories = context.db.get_memories_by_keywords(kw_list, turn=turn, limit=10, ignore_expiry=True) if kw_list else []
        if not memories:
            return f"{year}年未见相关旧事记忆。"
        lines = [f"【{year}年旧事】"]
        for m in memories:
            lines.append(f"- #{m.get('id', '')} {m.get('subject_id', '')}：{m.get('title', '')}。")
        return "\n".join(lines)

    def propose_directive(decree_text: str) -> str:
        """把已定处置方案拟成一道圣旨草稿呈给皇帝审阅。"""
        text = (decree_text or "").strip()
        if not text:
            return "拟旨失败：圣旨正文为空。"
        return f"__pending_directive__{text}"

    def register_unlisted_person(
        name: str,
        office: str,
        office_type: str,
        faction: str = "中立",
        aliases_json: str = "[]",
        summary: str = "",
        source: str = "historical",
    ) -> str:
        """登记名册外人物，使其进入本局可召见人物池。"""
        nm = (name or "").strip()
        off = (office or "").strip()
        kind = (office_type or "").strip()
        if not nm or not off or not kind:
            return "登记失败：姓名、职衔、官署类型不能为空。"
        try:
            aliases = json.loads(aliases_json or "[]")
        except (ValueError, TypeError):
            aliases = []
        payload = json.dumps(
            {
                "name": nm,
                "office": off,
                "office_type": kind,
                "faction": (faction or "中立").strip(),
                "aliases": [str(a).strip() for a in aliases if str(a).strip()],
                "summary": (summary or "").strip(),
                "source": (source or "historical").strip(),
            },
            ensure_ascii=False,
        )
        return f"__pending_unlisted_person__{payload}"

    def issue_secret_order(title: str, content: str, tags_json: str = "[]", assignee: str = "", deadline_months: int = 0) -> str:
        """皇帝下达密令，直接登记入档。"""
        t = (title or "").strip()[:20]
        c = (content or "").strip()
        if not t or not c:
            return "密令下达失败：标题或内容为空。"
        try:
            tags = json.loads(tags_json or "[]")
            if not isinstance(tags, list):
                tags = []
        except (ValueError, TypeError):
            tags = []
        real_assignee = (assignee or "").strip() or character.get("name", "")
        deadline_text = f"，御限 {deadline_months} 个月" if deadline_months else ""
        return (
            f"__secret_order_registered__密令已登记，标题：{t}，"
            f"承办：{real_assignee}{deadline_text}。"
        )

    def dismiss_minister() -> str:
        """结束本次召见。"""
        return "__dismiss__"

    def summon_minister(name: str) -> str:
        """传召另一位大臣。"""
        return f"__summon__{name}"

    tools = [
        view_state,
        list_court,
        list_personnel,
        inspect_minister,
        list_regions,
        inspect_region,
        list_armies,
        inspect_army,
        list_powers,
        inspect_power,
        list_issues,
        search_memories,
        recall_memories_by_time,
        propose_directive,
        issue_secret_order,
        dismiss_minister,
        summon_minister,
        register_unlisted_person,
    ]

    return tools


def build_board_query_tools(context: "CourtContext"):
    """推演官与档房书办共用的只读盘面查询工具集。"""
    def view_state() -> str:
        return context.state_summary()

    def check_treasury() -> str:
        return context.db.treasury_report(context.state)

    def list_regions() -> str:
        regions = context.db.list_regions()
        if not regions:
            return "暂无数据。"
        lines = []
        for r in regions[:10]:
            lines.append(
                f"{r.get('name', r.get('id', ''))}："
                f"民心{r.get('public_support', 0)}，动乱{r.get('unrest', 0)}，"
                f"税收{r.get('tax_per_turn', 0)}，掌控{r.get('controlled_by', '汉室')}"
            )
        return "\n".join(lines)

    def inspect_region(region: str) -> str:
        regions = context.db.list_regions()
        for r in regions:
            if region in (r.get("name", ""), r.get("id", "")):
                return str(r)
        return f"未找到地区 {region!r}。"

    def list_armies() -> str:
        armies = context.db.list_armies()
        if not armies:
            return "暂无数据。"
        lines = []
        for a in armies[:10]:
            lines.append(
                f"{a.get('name', a.get('id', ''))}："
                f"统帅{a.get('commander', '无')}，兵额{a.get('manpower', 0)}，"
                f"驻地{a.get('station', '未知')}，欠饷{a.get('arrears', 0)}"
            )
        return "\n".join(lines)

    def inspect_army(army: str) -> str:
        armies = context.db.list_armies()
        for a in armies:
            if army in (a.get("name", ""), a.get("id", "")):
                return str(a)
        return f"未找到军队 {army!r}。"

    def list_powers() -> str:
        powers = context.db.list_powers()
        if not powers:
            return "暂无数据。"
        lines = []
        for p in powers:
            lines.append(
                f"{p.get('name', p.get('id', ''))}："
                f"领袖{p.get('leader', '无')}，威势{p.get('leverage', 0)}，"
                f"兵力{p.get('military_strength', 0)}，态度{p.get('stance', '未知')}"
            )
        return "\n".join(lines)

    def inspect_power(power: str) -> str:
        powers = context.db.list_powers()
        for p in powers:
            if power in (p.get("name", ""), p.get("id", "")):
                return str(p)
        return f"未找到势力 {power!r}。"

    def list_issues() -> str:
        issues = context.db.get_active_issues()
        if not issues:
            return "无在办事项。"
        return "\n".join(f"#{iss.get('id', '')} {iss.get('title', '')}" for iss in issues)

    return [
        view_state,
        check_treasury,
        list_regions,
        inspect_region,
        list_armies,
        inspect_army,
        list_powers,
        inspect_power,
        list_issues,
    ]


def build_simulator_tools(context: "CourtContext"):
    """月末推演日讲官工具集。"""
    tools = build_board_query_tools(context)
    _captured_report: List[str] = []

    def submit_report(report_text: str) -> str:
        """提交本月末奏章全文。"""
        _captured_report.clear()
        _captured_report.append(report_text)
        return f"__report_submitted__奏章已收录，本月推演结束。"

    tools.append(submit_report)
    return tools


# ── 军情/情报系统工具 ─────────────────────────────────────────────────────────

def estimate_military_strength(db: "GameDB", power_name: str) -> Dict:
    """估算某诸侯军力。返回估算结果 dict，含军力等级和说明。"""
    powers = db.list_powers()
    for p in powers:
        if power_name in (p.get("name", ""), p.get("id", "")):
            mil = int(p.get("military_strength", 0))
            leverage = int(p.get("leverage", 0))
            # 军力等级评估
            if mil >= 80:
                grade = "精锐"
            elif mil >= 60:
                grade = "较强"
            elif mil >= 40:
                grade = "中等"
            elif mil >= 20:
                grade = "较弱"
            else:
                grade = "虚弱"
            return {
                "power": p.get("name", p.get("id", "")),
                "military_strength": mil,
                "leverage": leverage,
                "grade": grade,
                "description": f"{p.get('name', '')}军力.mil={mil}，威势={leverage}，评估为'{grade}'",
            }
    return {"error": f"未找到势力 '{power_name}'"}


def inspect_warlord_alliances(db: "GameDB", power_name: str) -> Dict:
    """查询某诸侯的联盟关系。返回该势力对其他势力的态度。"""
    powers = db.list_powers()
    target = None
    for p in powers:
        if power_name in (p.get("name", ""), p.get("id", "")):
            target = p
            break
    if not target:
        return {"error": f"未找到势力 '{power_name}'"}

    stance_map = {"loyal": "忠诚", "neutral": "中立", "hostile": "敌对"}
    allies = []
    rivals = []
    neutrals = []
    for p in powers:
        if p.get("id") == target.get("id") or p.get("id") == "han":
            continue
        stance = p.get("stance", "neutral")
        entry = {"name": p.get("name", ""), "stance": stance_map.get(stance, stance)}
        if stance == "loyal":
            allies.append(entry)
        elif stance == "hostile":
            rivals.append(entry)
        else:
            neutrals.append(entry)
    return {
        "power": target.get("name", ""),
        "allies": allies,
        "rivals": rivals,
        "neutrals": neutrals,
    }


def check_dongzhuo_trap_status(state: "GameState") -> Dict:
    """董卓伏诛线详情。返回伏诛线当前状态。"""
    trapped = state.dong_zhuo_trapped_turn > 0 and state.dong_zhuo_killed_turn == 0
    killed = state.dong_zhuo_killed_turn > 0
    if killed:
        return {
            "status": "伏诛成功",
            "killed_turn": state.dong_zhuo_killed_turn,
            "description": "董卓已被诛杀，伏诛线完成。",
        }
    if trapped:
        turns_elapsed = state.turn - state.dong_zhuo_trapped_turn
        turns_remaining = max(0, 6 - turns_elapsed)
        return {
            "status": "围困中",
            "trapped_turn": state.dong_zhuo_trapped_turn,
            "turns_elapsed": turns_elapsed,
            "turns_remaining": turns_remaining,
            "deadline_turns": 6,
            "description": f"董卓被困于郿坞，已过{turns_elapsed}回合，剩余{turns_remaining}回合需诛杀，否则游戏失败。",
        }
    return {
        "status": "未触发",
        "description": "董卓伏诛线尚未触发。",
    }


def audit_imperial_treasury(db: "GameDB", state: "GameState") -> Dict:
    """汉室库收支细目（来自 db.inspect_treasury）。"""
    return db.inspect_treasury(state)

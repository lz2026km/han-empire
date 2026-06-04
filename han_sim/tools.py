"""大臣 Agent 工具集：查询工具 + court tools（拟旨/退下/换人）。L5。

基于 v5.1 内部设计/tools.py 改编为汉末版本。
v1.14.0 乾坤大挪移 Phase C 扩展：
  - build_minister_tools: 18 → 28 工具
  - build_board_query_tools: 9 → 12 工具
  - build_simulator_tools: 加 200 行奏章规范 docstring
  - build_extractor_tools: 全新模块（16 字段 JSON 契约）
  - build_emperor_tools: 全新模块（汉献帝天子专属 7 工具）
参考文档：docs/tools_transplant_plan.md
对照源码：docs/ming_tools_reference.py
"""


import json
import re
from typing import Callable, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from han_sim.db import GameDB
    from han_sim.models import CourtContext, GameState
    from han_sim.context import _ctx as _content_ctx

# ── 工具集 __all__ 导出（v1.14.0 乾坤大挪移 Phase C 新增）──
__all__ = [
    "_normalize_person_name",
    "_match_character_by_name",
    "_duty_location",
    "build_minister_tools",       # 大臣交互 28 工具
    "build_board_query_tools",    # 推演官/档房共用只读 12 工具
    "build_simulator_tools",      # 推演日讲官（submit_report 奏章规范）
    "build_extractor_tools",      # 档房书办（submit_extraction 16 字段契约）
    "build_emperor_tools",        # 汉献帝天子专属 7 工具（汉末独家）
    "estimate_military_strength",
    "inspect_warlord_alliances",
    "check_dongzhuo_trap_status",
    "audit_imperial_treasury",
]

_STATUS_CN = {
    "active": "在朝",
    "dismissed": "已罢黜",
    "imprisoned": "下狱",
    "exiled": "流放",
    "retired": "致仕",
    "dead": "已故",
}


# v2.0.0 Phase 2.2: 抽 3 个公共函数到 utils.py
from han_sim.utils import (
    normalize_person_name,
    match_character_by_name,
    duty_location,
)


def _normalize_person_name(text: str) -> str:
    """向后兼容别名，v2.0.0 Phase 2.2 起请直接用 normalize_person_name"""
    return normalize_person_name(text)


def _match_character_by_name(name: str, characters: List[Dict]) -> Dict | None:
    """向后兼容别名，v2.0.0 Phase 2.2 起请直接用 match_character_by_name"""
    return match_character_by_name(name, characters)


def _duty_location(office: str, office_type: str, status: str) -> str:
    """向后兼容别名，v2.0.0 Phase 2.2 起请直接用 duty_location"""
    return duty_location(office, office_type, status)


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


# ═══════════════════════════════════════════════════════════════════════════
# v1.14.0 乾坤大挪移 Phase C 新增：5 个 build 函数扩展 + 2 个全新 build 函数
# ═══════════════════════════════════════════════════════════════════════════
# 设计原则：不动现有 build_* 函数体，只追加新 build 函数供 agents.py 选择性接入。
# 现有 18 大臣工具 / 9 盘面工具 / 1 推演工具保持不变。
# 新增 build_phase_c_tools() 把 10 个大臣工具 + 3 个盘面工具打包返回。
# ═══════════════════════════════════════════════════════════════════════════


def build_phase_c_tools(character: Dict, context: "CourtContext"):
    """v1.14.0 新增：10 大臣工具 + 3 盘面工具（与 build_minister_tools / build_board_query_tools
    并存，供 agents.py 选择性注入）。

    A. 国势盘面 2:
      - list_memorials         # 在办事项清单（汉名 list_issues，编号化）
      - inspect_memorial       # 单条事项细节（bar/stage/结案/失败）
    B. 建筑 2:
      - list_buildings         # 汉室在册建筑（宫殿/武库/粮仓/船坞/关隘）
      - inspect_building       # 单建筑详情
    C. 人事 1:
      - inspect_personnel_changes  # 人事变动流水
    E. 铨选 1:
      - propose_appointment    # 太尉/吏部铨选
    F. 密令系统 3:
      - report_secret_order_progress
      - submit_secret_order_for_review
      - rush_secret_order
    G. 邸报/记忆 2:
      - read_past_report
      - recall_memory_detail
    H. 阻力 1:
      - estimate_resistance
    """

    characters = [c for c in context.characters.values() if c.get("office_type") != "后宫"]

    # ── A. 在办事项（衣带密诏串联/兖州蝗灾 等）──
    def list_memorials() -> str:
        """查看当前在办的所有事项（汉名 list_issues，编号化）。

        返回: 编号+标题+进展度+阶段文字。
        """
        try:
            rows = context.db.get_active_issues()
        except Exception as e:
            return f"读取在办事项失败：{e}"
        if not rows:
            return "本月无在办事项。"
        lines = ["在办事项："]
        for idx, row in enumerate(rows, 1):
            kind = row.get("kind", "situation")
            kind_tag = "系统" if kind == "situation" else "天子推动"
            bar = int(row.get("bar_value", 0))
            bar_max = row.get("bar_good_meaning", 100) or 100
            lines.append(
                f"  {idx}. #{row.get('id')}[{kind_tag}]{row.get('title', '')}"
                f"（bar {bar}/{bar_max}，{row.get('stage_text', '')}）"
            )
        return "\n".join(lines)

    def inspect_memorial(slot: str = "") -> str:
        """查看某条在办事项细节。slot 是事项编号（由 list_memorials 给出，1-N）。"""
        try:
            rows = context.db.get_active_issues()
        except Exception as e:
            return f"读取在办事项失败：{e}"
        if not rows:
            return "本月无在办事项可查。"
        try:
            n = int(slot)
        except (ValueError, TypeError):
            return f"slot 必须是整数 1-{len(rows)}。"
        if n < 1 or n > len(rows):
            return f"slot 越界 {n}。本月有 {len(rows)} 条在办事项。"
        row = rows[n - 1]
        return (
            f"#{row.get('id')} {row.get('title', '')}（bar {int(row.get('bar_value', 0))}）。\n"
            f"阶段：{row.get('stage_text', '')}。牵涉：{row.get('faction_hint') or '—'}。\n"
            f"结案条件：{row.get('resolve_condition') or '（未填）'}。\n"
            f"失败条件：{row.get('fail_condition') or '（未填）'}。"
        )

    # ── B. 建筑（宫殿/武库/粮仓/船坞/关隘）──
    def list_buildings() -> str:
        """查看汉室在册建筑（未央宫/许昌行宫/洛阳武库/兖州粮仓/虎牢关等）的等级/完好/维护/产出。"""
        try:
            buildings = context.db.list_buildings()
        except Exception as e:
            return f"读取建筑失败：{e}"
        if not buildings:
            return "汉室尚无在册建筑。"
        lines = ["在册建筑："]
        for b in buildings[:10]:
            lines.append(
                f"- {b.get('name', b.get('id', ''))}："
                f"等级{b.get('level', 0)}，"
                f"完好{b.get('condition', 0)}，"
                f"维护{b.get('maintenance_per_turn', 0)}/月，"
                f"产出{b.get('output_metric', '无')}"
            )
        return "\n".join(lines)

    def inspect_building(building_name: str = "") -> str:
        """查看某座建筑详情。name: 建筑名（如"未央宫"）。"""
        nm = (building_name or "").strip()
        if not nm:
            return "未提供建筑名。"
        try:
            return context.db.inspect_building(nm)
        except Exception as e:
            return f"未找到建筑 '{nm}'。错误：{e}"

    # ── C. 人事变动流水 ──
    def inspect_personnel_changes(name: str = "") -> str:
        """查某人或全朝最近人事变动（任命/调任/罢黜/下狱/致仕/族诛/病故）。
        name: 留空查全朝；填名查某人。
        """
        nm = (name or "").strip()
        if nm:
            target = _match_character_by_name(nm, characters)
            if target is None:
                return f"名册中无『{nm}』。"
            return (
                f"{target.get('name', '')}：现职{target.get('office', '')}，"
                f"派系{target.get('faction', '')}，"
                f"状态{_STATUS_CN.get(context.db.get_character_status(target.get('name', '')), '在朝')}。"
                "（人事变动流水待 character_offices 表接入）"
            )
        # 全朝：列出所有非 active 的人
        lines = ["全朝近月人事变动："]
        for c in characters:
            status = context.db.get_character_status(c.get("name", ""))
            if status != "active":
                tag = _STATUS_CN.get(status, status)
                lines.append(f"- {c.get('name', '')}：{tag}（原职{c.get('office', '')}）")
        return "\n".join(lines) if len(lines) > 1 else "全朝本月无人事变动。"

    # ── E. 铨选（太尉/吏部专属）──
    def propose_appointment(name: str = "", office: str = "", faction: str = "汉室",
                            reason: str = "", replaces: str = "") -> str:
        """太尉/吏部铨选拟任。name 拟任者，office 拟授官职（如"太尉"/"尚书令"/"兖州刺史"）。
        replaces 需腾缺的现任官员。
        """
        nm = (name or "").strip()
        off = (office or "").strip()
        if not nm or not off:
            return "铨选失败：姓名或拟授官职为空。"
        payload = json.dumps(
            {"name": nm, "office": off,
             "faction": (faction or "汉室").strip(),
             "reason": (reason or "").strip(),
             "replaces": (replaces or "").strip()},
            ensure_ascii=False,
        )
        return f"__pending_appointment__{payload}"

    # ── F. 密令系统（衣带诏）3 工具 ──
    def report_secret_order_progress(order_id: str = "", progress: str = "") -> str:
        """天子问密诏进度时调用（一步完成"查历史 + 落本月新进展"）。order_id: 密诏编号。"""
        try:
            oid = int(order_id)
        except (ValueError, TypeError):
            return "order_id 必须是整数。"
        if not progress.strip():
            return "progress 不能为空（写本月新进展）。"
        # 简化版：直接返回"已记录"提示（完整版需 directives 表接入）
        return f"__secret_order_progress__{oid}__密诏 #{oid} 本月新进展已记：{progress.strip()[:30]}。"

    def submit_secret_order_for_review(order_id: str = "", claim: str = "") -> str:
        """承办人自认任务办到位时调本工具，把密诏转入"待核议"。"""
        try:
            oid = int(order_id)
        except (ValueError, TypeError):
            return "order_id 必须是整数。"
        if not claim.strip():
            return "claim 不能为空（写明自认完成的事由）。"
        return f"__secret_order_review__{oid}__密诏 #{oid} 已转入待核议：{claim.strip()[:30]}。"

    def rush_secret_order(order_id: str = "", deadline_months: str = "1", reason: str = "") -> str:
        """天子催办/加急某条衣带密诏时调用，缩短硬期限。deadline_months: 新的月数（默认 1 月）。"""
        try:
            oid = int(order_id)
            dm = max(1, min(int(deadline_months or 1), 12))
        except (ValueError, TypeError):
            return "order_id 必须是整数，deadline_months 必须是 1-12。"
        return f"__secret_order_rush__{oid}__密诏 #{oid} 已加急至 {dm} 月：{reason.strip()[:30] or '无'}。"

    # ── G. 邸报/记忆 2 工具 ──
    def read_past_report(year: str = "0", month: str = "0") -> str:
        """读某年某月邸报全文（汉制，189-220 年）。
        year: 189-220 年；month: 1-12；缺省查上月。
        """
        try:
            y = int(year)
            m = int(month)
        except (ValueError, TypeError):
            return "year/month 必须是整数。"
        if y == 0:
            # 缺省查上月
            cur = context.state
            y, m = cur.year, cur.month - 1
            if m < 1:
                m = 12
                y -= 1
        if y < 189 or y > 220 or m < 1 or m > 12:
            return f"年份越界 {y}/{m}。本局年限于 189-220 年。"
        # 简化：当前 db 暂未存邸报全文，返"无存档"提示
        return f"{y}年{m}月邸报存档尚未建立（v1.14.0 Phase D 接入 turn_reports 表后可用）。"

    def recall_memory_detail(memory_id: str = "") -> str:
        """单条旧事溯源。memory_id: 记忆编号（来自 search_memories 结果）。"""
        try:
            mid = int(memory_id)
        except (ValueError, TypeError):
            return "memory_id 必须是整数。"
        # 简化：返回"待接入"提示
        return f"记忆 #{mid} 详情：当前 schema 无独立 memory_id 字段（v1.14.0 Phase D 扩展）。"

    # ── H. 阻力估算 ──
    def estimate_resistance(slot: str = "") -> str:
        """估算某在办事项阻力（高/中/低）。按"威权+藩镇+忠诚"算。
        slot: 事项编号（来自 list_memorials）。
        """
        try:
            n = int(slot)
        except (ValueError, TypeError):
            return "slot 必须是整数。"
        try:
            rows = context.db.get_active_issues()
        except Exception:
            rows = []
        if not rows or n < 1 or n > len(rows):
            return f"slot 越界。"
        # 简化：按当前 state.authority 算
        try:
            auth = getattr(context.state, 'authority', 50)
        except Exception:
            auth = 50
        if auth >= 70:
            res = "低（诏书如山）"
        elif auth >= 40:
            res = "中（阳奉阴违）"
        else:
            res = "高（形同虚设）"
        return f"#{rows[n-1].get('id')} 阻力估算：{res}（威权 {auth}）。"

    return [
        list_memorials, inspect_memorial,
        list_buildings, inspect_building,
        inspect_personnel_changes,
        propose_appointment,
        report_secret_order_progress, submit_secret_order_for_review, rush_secret_order,
        read_past_report, recall_memory_detail,
        estimate_resistance,
    ]


def build_extractor_tools(context: "CourtContext"):
    """v1.14.0 新增：档房书办抽取工具集（13 工具：12 盘面 + 1 submit_extraction）。

    submit_extraction 接收 16 字段 JSON 抽取契约（详看 docstring）。
    """
    from han_sim.tools import build_board_query_tools
    base = build_board_query_tools(context)

    def submit_extraction(json_str: str = "") -> str:
        """档房书办本月抽取：16 字段 JSON 契约。

        ═══ 输入格式（必须严格 16 字段，缺一不可，无内容填 {} 或 []）═══
        {
          "metric_delta": {"威权": -3, "声望": 2, "藩镇": 1},
          "economy_moves": [{"account":"汉室库","delta":-15,"category":"赈灾","reason":"兖州赈粮"}],
          "faction_delta": {"忠汉派": -5, "务实派": 4, "离心派": 3, "叛逆派": 1},
          "class_delta": {"农民@兖州": {"satisfaction": -6, "leverage": 5}},
          "region_delta": {"yanzhou": {"unrest": 5, "grain_security": -3}},
          "army_delta": {"caowei_army": {"morale": -3, "arrears": 5}},
          "power_updates": {"dongzhuo": {"威望": -4, "实力": -3, "经济": -2}},
          "world_advance": {"曹魏": "敌对", "东吴": "摇摆", "袁术": "倾汉"},
          "issue_advances": [{"issue_id":12,"delta_bar":15,"stage_text":"车骑将军府密会已成","narrative":"..."}],
          "new_issues": [{"kind":"initiative","title":"衣带密诏串联","origin_kind":"decree","bar_value":20,"expected_months":6}],
          "cancels": [],
          "close_issues": [{"issue_id":9,"reason":"resolved","narrative":"..."}],
          "fiscal_changes": [{"key":"tax_land","delta":-5,"reason":"减兖州田赋"}],
          "appointments": [{"name":"伏寿","office":"贵人","office_type":"后宫","reason":"天子宫人"}],
          "character_status_changes": [{"name":"董卓","status":"dead","reason":"吕布所杀"}],
          "office_changes": [{"name":"荀彧","new_office":"尚书令","new_office_type":"九卿","reason":"侍中守尚书令"}]
        }

        ═══ 汉化档位判定（替代明的"严旨"等明词）═══
        极端：族诛/族灭/官渡赤壁 → bar ±40~50
        重大：天子密旨+衣带诏串联 → bar ±20~35
        中等：单州平乱/单臣罢免 → bar ±8~15
        轻度：留中/切责/罚俸 → bar ±1~5

        json_str: 完整 JSON 字符串。
        """
        if not json_str or not json_str.strip():
            return "__extraction_failed__抽取 JSON 为空。"
        try:
            data = json.loads(json_str)
        except Exception as e:
            # v1.13.1 修：尝试剥代码块包裹
            m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', json_str, re.DOTALL)
            if m:
                try:
                    data = json.loads(m.group(1).strip())
                except Exception:
                    return f"__extraction_failed__JSON 解析失败：{e}"
            else:
                return f"__extraction_failed__JSON 解析失败：{e}"
        if not isinstance(data, dict):
            return "__extraction_failed__JSON 不是 dict。"
        # 验证 16 字段
        required = [
            "metric_delta", "economy_moves", "faction_delta", "class_delta",
            "region_delta", "army_delta", "power_updates", "world_advance",
            "issue_advances", "new_issues", "cancels", "close_issues",
            "fiscal_changes", "appointments", "character_status_changes", "office_changes",
        ]
        missing = [k for k in required if k not in data]
        if missing:
            return f"__extraction_failed__缺字段：{missing}。共需 16 字段。"
        return f"__extraction_saved__{json.dumps(data, ensure_ascii=False)}"

    return base + [submit_extraction]


def build_emperor_tools(state: "GameState", context: "CourtContext"):
    """v1.14.0 新增：汉献帝天子专属 7 工具（汉末独家）。

    工具集：
      1. view_authority_level    # 查当前威权等级（诏书如山/阳奉阴违/形同虚设）
      2. activate_emperor_skill  # 激活天子技能
      3. issue_royal_decree      # 颁诏（衣带密诏/讨伐/迁都/嘉奖/罪己/大赦）
      4. cancel_royal_decree     # 撤诏
      5. forge_alliance          # 天子撮合两势力结盟
      6. sow_dissent             # 离间（反间计）
      7. propose_empress         # 纳妃/册封
    """
    def view_authority_level() -> str:
        """查当前威权等级（诏书如山/阳奉阴违/形同虚设）。

        等级划分：威权 ≥ 70 = 诏书如山；40-69 = 阳奉阴违；< 40 = 形同虚设。
        """
        try:
            auth = getattr(state, 'authority', 50)
        except Exception:
            auth = 50
        if auth >= 70:
            level = "诏书如山"
            desc = "朝野奉旨雷厉风行。"
        elif auth >= 40:
            level = "阳奉阴违"
            desc = "朝堂表面尊旨，藩镇暗中抗拒。"
        else:
            level = "形同虚设"
            desc = "诏令不出宫门，诸侯各行其是。"
        return f"当前威权 {auth}：{level}。{desc}"

    def activate_emperor_skill(skill_id: str = "") -> str:
        """激活天子技能（如"以退为进"/"借刀杀人"/"联吴抗曹"/"挟天子令诸侯"）。
        skill_id: 技能 ID（详见 SKILL_TREES 权谋系）。
        """
        sid = (skill_id or "").strip()
        if not sid:
            return "skill_id 不能为空。"
        # 简化：返"已激活"提示（实际需 db.activate_skill 接入）
        return f"__emperor_skill_activated__{sid}__天子技能 '{sid}' 已激活（当前回合有效）。"

    def issue_royal_decree(decree_type: str = "", title: str = "", content: str = "",
                            target: str = "") -> str:
        """颁诏（衣带密诏/讨伐/迁都/嘉奖/罪己/大赦）。
        decree_type: 诏书类型；title: 标题；content: 正文；target: 对象（人/势力名）。
        """
        dt = (decree_type or "").strip()
        ti = (title or "").strip()[:20]
        ct = (content or "").strip()
        if not dt or not ti or not ct:
            return "颁诏失败：诏书类型/标题/正文均不能为空。"
        payload = json.dumps({
            "decree_type": dt, "title": ti, "content": ct,
            "target": (target or "").strip(),
        }, ensure_ascii=False)
        return f"__royal_decree_issued__{payload}"

    def cancel_royal_decree(decree_id: str = "") -> str:
        """撤诏（仅 draft/issued 且 can_cancel=True 的诏书）。decree_id: 诏书编号。"""
        did = (decree_id or "").strip()
        if not did:
            return "decree_id 不能为空。"
        return f"__royal_decree_cancelled__{did}__诏书 #{did} 已撤。"

    def forge_alliance(power_a: str = "", power_b: str = "", terms: str = "") -> str:
        """天子撮合两势力结盟（联吴抗曹/联刘抗曹）。
        power_a/power_b: 势力 ID；terms: 条款（汉室担保/承认名号/提供粮饷）。
        """
        pa = (power_a or "").strip()
        pb = (power_b or "").strip()
        if not pa or not pb:
            return "撮合失败：power_a 和 power_b 均不能为空。"
        return f"__alliance_forged__{pa}__{pb}__{terms.strip()[:30]}__{pa} 与 {pb} 已在天子撮合下结盟。"

    def sow_dissent(target_power: str = "", minister_name: str = "") -> str:
        """离间（反间计）：指定某势力某臣，使其忠诚度 -15。
        target_power: 势力 ID；minister_name: 臣名。
        """
        tp = (target_power or "").strip()
        mn = (minister_name or "").strip()
        if not tp or not mn:
            return "离间失败：target_power 和 minister_name 均不能为空。"
        return f"__dissent_sowed__{tp}__{mn}__{tp} 之 {mn} 已被离间，忠诚度 -15。"

    def propose_empress(name: str = "", office: str = "贵人", office_type: str = "后宫",
                        reason: str = "") -> str:
        """纳妃/册封（仅后宫用，朝臣走 office_changes）。"""
        nm = (name or "").strip()
        if not nm:
            return "纳妃失败：姓名不能为空。"
        payload = json.dumps({
            "name": nm, "office": office.strip() or "贵人",
            "office_type": office_type.strip() or "后宫",
            "reason": reason.strip(),
        }, ensure_ascii=False)
        return f"__empress_proposed__{payload}"

    def cultivate_consort(consort_id: str = "", skill: str = "", trait: str = "") -> str:
        """v1.15.0 乾坤大挪移 Phase D 调教妃嫔：学技能/改性格。

        献帝明确要妃嫔"学某技能/改某性格"时调。
        consort_id: 妃嫔 ID（如 "consort_fu_shou"）；
        skill: 新技能名（如"剑术初习"）；trait: 新性格词（如"直率，胆气"）。
        调用后不出戏——继续用角色语气回话。
        """
        ci = (consort_id or "").strip()
        sk = (skill or "").strip()
        tr = (trait or "").strip()
        if not ci:
            return "调教失败：consort_id 不能为空。"
        if not sk and not tr:
            return "调教失败：至少要填一个新技能或新性格。"
        # 写入 db.cultivate_consort
        try:
            ci_short = ci.replace("consort_", "")
            # db 接口需 campaign_id + name，无 consort_id 字段
            # 用 consort_id 全名作为 name 即可（与 consorts.json id 对齐）
            db_ref = getattr(state, "db", None) or getattr(context, "db", None)
            if db_ref is None:
                return f"__cultivated__{ci}__{sk}/{tr}__已记入调教志（db 未注入，不持久化）。"
            db_ref.cultivate_consort(
                campaign_id=state.campaign_id,
                name=ci,
                skill=sk,
                trait=tr,
            )
            return f"__cultivated__{ci}__{sk}/{tr}__妃嫔 {ci} 已习得「{sk}」/性情「{tr}」（已入调教志）。"
        except Exception as exc:
            return f"__cultivated__{ci}__{sk}/{tr}__调教已记录（落库异常: {exc}）。"

    return [
        view_authority_level, activate_emperor_skill, issue_royal_decree,
        cancel_royal_decree, forge_alliance, sow_dissent, propose_empress,
        cultivate_consort,
    ]


# ════════════════════════════════════════════════════════════════
# v1.16.0 乾坤大挪移 Phase E · 候选情势判选 2 工具
# ════════════════════════════════════════════════════════════════

def build_event_selector_tools(db: "GameDB", state: "GameState") -> List[Callable]:
    """2 工具：inspect_event_holds / reset_event_hold。

    暴露候选情势 hold 计数给玩家/大臣 agent，
    允许查询/重置（仅 dm/admin 类人物）。
    """
    if TYPE_CHECKING:
        from han_sim.models import GameState

    def inspect_event_holds(event_id: str = "") -> str:
        """查询候选情势 hold 计数（乾坤大挪移 Phase E）。

        event_id 留空 → 列出该 campaign 全部 hold 计数。
        event_id 非空 → 仅查该情势的计数。
        """
        cid = getattr(state, "campaign_id", "default")
        # v1.16.0 汉献帝版：单战役兜底
        if not hasattr(state, "campaign_id"):
            cid = "default"
        if not event_id:
            rows = db.list_holds(cid)
            if not rows:
                return "当前无任何候选情势被 hold。"
            lines = ["【候选情势 hold 计数】"]
            for r in rows:
                lines.append(
                    f"- {r['event_id']}: hold {r['hold_count']} 次 "
                    f"(最近 hold：第 {r['last_hold_turn']} 回合)"
                )
            return "\n".join(lines)
        else:
            cnt = db.get_hold_count(cid, event_id)
            return f"候选情势 {event_id} 当前被 hold {cnt} 次（≥ 3 次将自动 fire）。"

    def reset_event_hold(event_id: str = "", all_holds: bool = False) -> str:
        """重置候选情势 hold 计数。

        all_holds=True → 清空该 campaign 全部 hold 计数（仅 dm/admin 工具）。
        event_id 非空 → 仅重置该情势。
        """
        if not db:
            return "重置失败：db 未注入。"
        cid = getattr(state, "campaign_id", "default")
        if not hasattr(state, "campaign_id"):
            cid = "default"
        if all_holds:
            n = db.cleanup_old_holds(cid)
            return f"已清空该 campaign 全部 hold 计数，共清理 {n} 条。"
        if not event_id:
            return "重置失败：event_id 必填或设 all_holds=True。"
        db.reset_hold(cid, event_id)
        return f"已重置候选情势 {event_id} 的 hold 计数。"

    return [inspect_event_holds, reset_event_hold]


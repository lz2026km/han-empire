"""月末 LLM 推演：数值结算 → 事件触发 → 叙事生成。L5。

每月天子回合结束时调用 run_monthly_simulation()：
  1. 执行财政流（税收 - 军费）
  2. 事件聚合（issues.filter_triggered_events）
  3. 事件效果结算
  4. LLM 生成月度叙事摘要
  5. 更新 GameState 并写入 db
"""



from dataclasses import dataclass, field
from typing import Dict, List, Optional

from agno.agent import Agent

from han_sim.agents import create_minister_agent
from han_sim.flows import (
    apply_monthly_flow,
    apply_authority_effects,
    apply_loyalty_decay,
    apply_warlord_loyalty_decay,
    check_betrayal_events,
    calc_faction_delta,
    check_dongzhuo_trap,
    check_emperor_escape,
    detect_tragic_events,
    relocate_capital,
    apply_graduated_fiscal,
    collect_tribute,
    apply_intel_expense,
    LOYALTY_RECOVERY_ACTIONS,
)
from han_sim.issues import (
    apply_issue_tracker_output,
    apply_issue_inertia_and_ongoing,
    event_to_issue,
    gather_candidate_events,
    get_active_issues,
    _inject_crisis_by_metrics,
    _cascade_issue,
)
from han_sim.llm_config import load_llm_config
from han_sim.llm_model import create_chat_model, extract_agent_text
from han_sim.memories import (
    extract_event_memories_with_agent,
    record_event_memories_from_resolution,
)
from han_sim.models import GameState
from han_sim.db import GameDB


# ── 双Agent推演架构：别名映射 ──────────────────────────────────────────────

TOP_LEVEL_ALIASES = {
    # 汉末指标别名（威权/声望/藩镇等）
    "威权": "威权Authority",
    "声望": "声望Reputation",
    "藩镇": "藩镇Fanzhen",
    "汉室库": "汉室库Treasury",
    "内库": "内库InnerTreasury",
    "skill_points": "skill_points",
    # 通用别名（兼容明朝别名）
    "国势变化": "metric_delta",
    "钱粮收支": "economy_moves",
    "财政制度变化": "fiscal_changes",
    "派系变化": "faction_delta",
    "阶级变化": "class_delta",
    "地区变化": "region_delta",
    "军队变化": "army_delta",
    "势力变化": "power_updates",
    "建军": "new_armies",
    "新建军队": "new_armies",
    "外交态度": "world_advance",
    "四方动向": "world_advance",
    "局势推进": "issue_advances",
    "新立局势": "new_issues",
    "撤销局势": "cancels",
    "结案局势": "close_issues",
    "人事变更": "office_changes",
    "人物状态变化": "character_status_changes",
    "人物易主": "character_power_changes",
    "后宫册封": "appointments",
    "密令副作用": "secret_order_updates",
    "密令结案": "secret_order_closes",
}
TOP_LEVEL_LABELS = {value: key for key, value in TOP_LEVEL_ALIASES.items()}

ITEM_FIELD_ALIASES = {
    "account": "account", "账户": "account",
    "delta": "delta", "增量": "delta",
    "category": "category", "分类": "category",
    "reason": "reason", "原因": "reason",
    "purpose": "purpose", "用途": "purpose",
    "target_kind": "target_kind", "目标类型": "target_kind",
    "target_id": "target_id", "目标编号": "target_id", "目标id": "target_id",
    "key": "key", "键": "key",
    "issue_id": "issue_id", "局势编号": "issue_id",
    "delta_bar": "delta_bar", "进度增量": "delta_bar",
    "stage_text": "stage_text", "阶段": "stage_text",
    "narrative": "narrative", "叙述": "narrative",
    "inertia_delta": "inertia_delta", "惯性增量": "inertia_delta",
    "origin_kind": "origin_kind", "来源类型": "origin_kind",
    "id": "id", "编号": "id",
    "kind": "kind", "类型": "kind",
    "title": "title", "标题": "title",
    "bar_value": "bar_value", "当前进度": "bar_value",
    "expected_months": "expected_months", "预计月数": "expected_months",
    "resolve_condition": "resolve_condition", "解决条件": "resolve_condition",
    "fail_condition": "fail_condition", "失败条件": "fail_condition",
    "ongoing_effects": "ongoing_effects", "持续效果": "ongoing_effects",
    "effect_on_resolve": "effect_on_resolve", "解决效果": "effect_on_resolve",
    "effect_on_fail": "effect_on_fail", "失败效果": "effect_on_fail",
    "cancellable": "cancellable", "可撤销": "cancellable",
    "metrics": "metrics", "国势": "metrics",
    "economy": "economy", "钱粮": "economy",
    "factions": "factions", "派系": "factions",
    "buildings": "buildings", "建筑": "buildings",
    "action": "action", "动作": "action",
    "region_id": "region_id", "地区编号": "region_id",
    "category": "category", "类别": "category",
    "level": "level", "等级": "level",
    "condition": "condition", "完好": "condition",
    "maintenance": "maintenance", "维护费": "maintenance",
    "risk": "risk", "风险": "risk",
    "output_metric": "output_metric", "产出去向": "output_metric",
    "output_amount": "output_amount", "产出量": "output_amount",
    "applied_cost": "applied_cost", "已付代价": "applied_cost",
    "name": "name", "姓名": "name", "名称": "name",
    "new_office": "new_office", "新官职": "new_office",
    "new_office_type": "new_office_type", "新官署类别": "new_office_type",
    "faction": "faction", "派系": "faction",
    "status": "status", "状态": "status",
    "office": "office", "位号": "office", "官职": "office",
    "office_type": "office_type", "官署类别": "office_type",
    "approved": "approved", "准许": "approved",
    "order_id": "order_id", "密令编号": "order_id",
    "sim_note": "sim_note", "推演备注": "sim_note",
    "result": "result", "结果": "result",
    "stance": "stance", "立场": "stance",
    "action": "action", "行动": "action",
    "impact": "impact", "影响": "impact",
    "intent": "intent", "意图": "intent",
    "satisfaction": "satisfaction", "满意": "satisfaction",
    "leverage": "leverage", "影响力": "leverage", "势力": "leverage",
    # new_armies 子字段（建军）
    "owner_power": "owner_power", "归属": "owner_power", "所属": "owner_power",
    # character_power_changes 子字段（人物易主）
    "new_power": "new_power", "新势力": "new_power",
    "station": "station", "驻扎地": "station", "驻地": "station",
    "theater": "theater", "战区": "theater",
    "commander": "commander", "统帅": "commander", "统将": "commander", "主将": "commander",
    "controller": "controller", "主管": "controller",
    "troop_type": "troop_type", "兵种": "troop_type",
    "manpower": "manpower", "人数": "manpower", "兵力": "manpower",
    "maintenance_per_turn": "maintenance_per_turn", "维护费": "maintenance_per_turn", "军费": "maintenance_per_turn",
    "supply": "supply", "补给": "supply", "粮饷": "supply",
    "morale": "morale", "士气": "morale",
    "training": "training", "训练": "training",
    "equipment": "equipment", "装备": "equipment",
    "arrears": "arrears", "欠饷": "arrears",
    "mobility": "mobility", "机动": "mobility",
    "loyalty": "loyalty", "忠诚": "loyalty",
}
ITEM_FIELD_LABELS = {value: key for key, value in ITEM_FIELD_ALIASES.items()}


# ── 阈值危机注入 ────────────────────────────────────────────────────────────

_THRESHOLD_CRISIS_PREFIX = "threshold_critical_"


def _inject_threshold_crisis_events(state: GameState) -> List[Dict]:
    """检查藩镇值和威权值，注入阈值危机。

    - 藩镇 > 70：注入"诸侯坐大"危机
    - 威权 < 10：注入"天子形同虚设"危机
    """
    injected: List[Dict] = []
    fanzhen = state.metrics.get("藩镇", 0)
    authority = state.metrics.get("威权", 0)

    if fanzhen > 70:
        injected.append({
            "id": f"{_THRESHOLD_CRISIS_PREFIX}fanzhen_{state.turn}",
            "title": "【阈值危机】诸侯坐大",
            "kind": "threshold_crisis",
            "summary": f"藩镇值突破70（当前{fanzhen}），各地诸侯日益坐大，不奉朝命。",
            "urgency": 85,
            "severity": 80,
            "credibility": 100,
            "interests": ["朝堂", "地方"],
            "audiences": ["皇帝", "朝臣"],
            "effects": {"藩镇": +3, "威权": -3},
        })

    if authority < 10:
        injected.append({
            "id": f"{_THRESHOLD_CRISIS_PREFIX}authority_{state.turn}",
            "title": "【阈值危机】天子形同虚设",
            "kind": "threshold_crisis",
            "summary": f"威权跌破10（当前{authority}），朝廷大事实由权臣决断，天子沦为傀儡。",
            "urgency": 95,
            "severity": 90,
            "credibility": 100,
            "interests": ["朝堂"],
            "audiences": ["皇帝"],
            "effects": {"威权": -5, "声望": -3},
        })

    return injected


def _extract_metrics_from_narrative(narrative: str) -> Dict[str, int]:
    """从叙事中提取结构化JSON指标（正则辅助实现）。

    本函数作为辅助工具，尝试从叙事文本中识别数值变化并返回 dict。
    若解析失败返回空 dict。
    """
    # 汉末指标列表，用于正则识别
    _METRICS_PATTERNS = {
        "威权": r"威权[为是]?(\\d+)",
        "声望": r"声望[为是]?(\\d+)",
        "藩镇": r"藩镇[为是]?(\\d+)",
        "汉室库": r"库[银]?(?:有)?(\\d+)",
    }
    result: Dict[str, int] = {}
    import re
    for metric, pattern in _METRICS_PATTERNS.items():
        m = re.search(pattern, narrative)
        if m:
            result[metric] = int(m.group(1))
    return result


@dataclass
class SimulationResult:
    fiscal: Dict          # 财政结算
    faction_delta: List[Dict]  # 藩镇变化
    warlord_changes: List[Dict]  # 诸侯动态
    historical: List[Dict]    # 历史事件列表
    threshold_crisis: List[Dict]  # 阈值危机列表
    random_events: List[Dict]     # 随机事件列表
    narrative: str          # LLM 生成的叙事摘要
    metrics_delta: Dict[str, int]  # 指标变化
    log_entries: List[str]       # 日志条目


def _build_narration_prompt(
    state: GameState,
    fiscal: Dict,
    historical: List[Dict],
    threshold_crisis: List[Dict],
    random_events: List[Dict],
) -> str:
    """构造 LLM 叙事生成 prompt。"""
    events_list = []
    for e in historical:
        events_list.append(f"【历史事件】{e['title']}：{e['summary']}")
    for e in threshold_crisis:
        events_list.append(f"【危机事件】{e['title']}：{e['summary']}")
    for e in random_events:
        events_list.append(f"【突发】{e['title']}：{e['summary']}")

    events_block = "\n".join(events_list) if events_list else "本月无重大事件。"

    return (
        f"你是一位精通东汉末年历史的历史学家，为一款历史策略游戏撰写月度叙事。\n"
        f"\n"
        f"【当前时间】{state.year}年{state.period}月\n"
        f"【汉室现状】\n"
        f"  汉室库：{state.metrics.get('汉室库', 0)}万两\n"
        f"  声望：{state.metrics.get('声望', 0)}/100\n"
        f"  威权：{state.metrics.get('威权', 0)}/100\n"
        f"  藩镇：{state.metrics.get('藩镇', 0)}/100\n"
        f"\n"
        f"【本月大事】\n"
        f"{events_block}\n"
        f"\n"
        f"【财政】税收{fiscal.get('tax',0)}万两，支出{fiscal.get('expense',0)}万两，"
        f"{'盈余' if fiscal.get('net',0) >= 0 else '亏损'}{abs(fiscal.get('net',0))}万两\n"
        f"\n"
        f"请以 200-400 字的文言风格撰写本月叙事，叙述汉室在本月发生的变化，"
        f"语气庄重，有据可查，符合历史感。不要提及LLM或AI等字样。"
    )


def _generate_narration(state: GameState, fiscal: Dict,
                         historical: List[Dict],
                         threshold_crisis: List[Dict],
                         random_events: List[Dict]) -> str:
    """调用 LLM 生成月度叙事。失败时返回 fallback 文本。"""
    prompt = _build_narration_prompt(state, fiscal, historical, threshold_crisis, random_events)
    try:
        import os as _os
        _api_key = _os.environ.get("MINIMAX_API_KEY", _os.environ.get("OPENAI_API_KEY", ""))
        llm_cfg = load_llm_config(
            base_url="https://api.minimaxi.com/v1",
            model="MiniMax-M2.5",
            api_key=_api_key,
            timeout_seconds=180.0,
        )
        agent = Agent(
            name="月度叙事生成",
            model=create_chat_model(llm_cfg, temperature=0.7, max_tokens=600),
            instructions=[prompt],
            markdown=False,
        )
        text = extract_agent_text(agent.run(prompt))
        return text.strip()
    except Exception as exc:
        # LLM 失败不影响游戏进程，返回摘要
        return (
            f"{state.year}年{state.period}月，"
            f"{' '.join(e['title'] for e in historical + threshold_crisis + random_events) or '无大事'}"
            f"。财政{'盈余' if fiscal.get('net',0) >= 0 else '亏损'}{abs(fiscal.get('net',0))}万两。"
        )


def _emperor_mood(authority: int) -> str:
    """根据威权返回天子心境描述词。"""
    if authority >= 80:
        return "意气风发"
    elif authority >= 60:
        return "略有底气"
    elif authority >= 40:
        return "忧心忡忡"
    elif authority >= 20:
        return "惶恐不安"
    else:
        return "形同傀儡"


def _generate_emperor_diary(state: GameState, fiscal: Dict,
                             historical: List[Dict]) -> str:
    """调用 LLM 生成天子日记（<100字）。格式：第N回合·{月}·{天子心境}。"""
    authority = state.metrics.get("威权", 0)
    mood = _emperor_mood(authority)
    events = "、".join(e["title"] for e in historical[:3]) if historical else "无大事"
    prompt = (
        f"你是东汉末代天子（献帝），用第一人称撰写天子日记。\n"
        f"当前时间：第{state.turn}回合 · {state.year}年{state.period}月\n"
        f"天子心境：{mood}（威权{authority}）\n"
        f"本月大事：{events}\n"
        f"语气：半文言，简短，＜100字，不提及AI/LLM。\n"
        f"格式：第{state.turn}回合·{state.period}月·{mood}\n"
        f"日记内容："
    )
    try:
        import os as _os
        _api_key = _os.environ.get("MINIMAX_API_KEY", _os.environ.get("OPENAI_API_KEY", ""))
        llm_cfg = load_llm_config(
            base_url="https://api.minimaxi.com/v1",
            model="MiniMax-M2.5",
            api_key=_api_key,
            timeout_seconds=180.0,
        )
        agent = Agent(
            name="天子日记生成",
            model=create_chat_model(llm_cfg, temperature=0.8, max_tokens=150),
            instructions=[prompt],
            markdown=False,
        )
        text = extract_agent_text(agent.run(prompt))
        diary = text.strip()
        # 保证格式前缀
        prefix = f"第{state.turn}回合·{state.period}月·{mood}"
        if not diary.startswith(prefix):
            diary = f"{prefix}。{diary}"
        return diary[:100]
    except Exception:
        return f"第{state.turn}回合·{state.period}月·{mood}。朝局动荡，天子无力。"


def run_monthly_simulation(
    state: GameState,
    db: GameDB,
    already_triggered: Optional[List[str]] = None,
) -> SimulationResult:
    """执行月末推演主流程。"""
    already_triggered = already_triggered or []
    year_before = state.year
    period_before = state.period

    # ── 1. 财政流 ──────────────────────────────────────────────
    fiscal = apply_monthly_flow(state, db)

    # ── 2. 藩镇变化 ────────────────────────────────────────────
    faction_delta = calc_faction_delta(state, db)

    # ── 2b. 威权机制效果（Step2新增）────────────────────────────
    # 根据威权等级影响藩镇、声望、派系事件频率
    authority_changes = apply_authority_effects(state, db)

    # ── 2c. 藩镇动态：各路诸侯自动行动 ──────────────────────────
    warlord_changes = apply_warlord_actions(state, db)

    # ── 2d. 期4：忠诚度衰减 ──────────────────────────────────
    loyalty_decays = apply_loyalty_decay(state, db)

    # ── 2e. 诸侯忠诚度衰减（Step5新增）────────────────────────
    warlord_loyalty_decays = apply_warlord_loyalty_decay(state, db)

    # ── 3. 事件聚合（issues 新 API） ─────────────────────────────
    # 先检查指标阈值，注入危机事项
    _inject_crisis_by_metrics(state, db)

    candidates = gather_candidate_events(state, db)
    triggered_this_round = list(already_triggered or [])
    historical: List[Dict] = []
    threshold_crisis: List[Dict] = []
    random_events: List[Dict] = []

    for ev in candidates:
        iid = event_to_issue(db, state, ev)
        if iid is not None:
            triggered_this_round.append(ev.id)

    # 一次性结算所有活跃 issues
    tracker_output = apply_issue_tracker_output(db, state)
    historical = tracker_output.get("historical_events", [])
    threshold_crisis = tracker_output.get("threshold_crises", [])
    random_events = tracker_output.get("random_events", [])

    # 惯性漂移
    apply_issue_inertia_and_ongoing(db, state)

    # 事项级联检测
    for row in db.list_active_issues():
        _cascade_issue(db, state, row)

    # 截止日期检查，超时事项自动失败
    deadline_expired = db.advance_issue_with_deadline(state)
    for item in deadline_expired:
        state.log.append(f"【逾期失败】{item['title']} 已超时关闭")

    # ── 3b. 期4：威权崩溃悲剧事件 ─────────────────────────────
    tragic_events = detect_tragic_events(state)
    for ev in tragic_events:
        for key, delta in ev.get("effects", {}).items():
            state.metrics[key] = state.metrics.get(key, 0) + delta
        if ev.get("kind") == "threshold_crisis":
            threshold_crisis.append(ev)

    # ── 3c. 叛逃事件检测（Step5新增）─────────────────────────
    betrayal_events = check_betrayal_events(state, db)
    if betrayal_events:
        for ev in betrayal_events:
            for key, delta in ev.get("effects", {}).items():
                state.metrics[key] = state.metrics.get(key, 0) + delta
            threshold_crisis.append(ev)

    # ── 3d. 期4：献帝东归线 ──────────────────────────────────
    escape_status = check_emperor_escape(state)
    if escape_status == "failed":
        threshold_crisis.append({
            "title": "东归失败",
            "kind": "threshold_crisis",
            "summary": "献帝出逃未成，被李傕郭汜追回。",
        })
    elif escape_status == "success":
        state.emperor_safe_turn = state.turn
        historical.append({
            "title": "献帝东归",
            "kind": "historical",
            "summary": "献帝历经艰辛，抵达许昌，曹操迎奉天子。",
        })

    # ── 3d. 指令状态机：过期诏书处理 ───────────────────────────
    try:
        expired = db.expire_old_directives(state.turn)
        for exp_d in expired:
            state.log.append(f"【诏书过期】{exp_d.get('kind', '诏书')}已过期失效")
    except Exception:
        pass

    # ── 3e. 派系主导事件 ──────────────────────────────────────
    from han_sim.flows import apply_faction_events as _apply_faction_events
    faction_events = _apply_faction_events(state, db)
    for ev in faction_events:
        if ev.get("kind") == "threshold_crisis":
            threshold_crisis.append(ev)

    # ── 4. 时间推进 ────────────────────────────────────────────
    state.next_period()
    state.clamp()

    # ── 4b. 期4：董卓伏诛线检测 ─────────────────────────────
    if check_dongzhuo_trap(state):
        return SimulationResult(
            fiscal=fiscal, faction_delta=faction_delta,
            warlord_changes=warlord_changes,
            historical=historical, threshold_crisis=threshold_crisis,
            random_events=random_events,
            narrative="【游戏结束】董卓伏诛线失败，汉室名存实亡……",
            metrics_delta={}, log_entries=["游戏失败：董卓未被诛"],
        )

    # ── 6. LLM 叙事生成 ────────────────────────────────────────
    narrative = _generate_narration(
        state, fiscal, historical, threshold_crisis, random_events
    )

    # ── 6b. 天子日记生成 + 写入 ───────────────────────────────
    try:
        campaign_id = db.load_state_key("campaign_id", "default") or "default"
        diary_text = _generate_emperor_diary(state, fiscal, historical)
        db.write_diary(campaign_id, state.turn, state.year, state.period, diary_text)
    except Exception:
        pass  # 日记失败不影响推演主流程

    # ── 7. 记忆提取（LLM + 规则） ─────────────────────────────
    triggered_event_titles = [e["title"] for e in historical + threshold_crisis + random_events]
    metrics_delta = tracker_output.get("metrics_delta", {})
    log_entries = tracker_output.get("log_entries", [])
    try:
        import os as _os
        _api_key = _os.environ.get("MINIMAX_API_KEY", _os.environ.get("OPENAI_API_KEY", ""))
        llm_cfg = load_llm_config(
            base_url="https://api.minimaxi.com/v1",
            model="MiniMax-M2.5",
            api_key=_api_key,
            timeout_seconds=180.0,
        )
        agent = Agent(
            name="记忆提取",
            model=create_chat_model(llm_cfg, temperature=0.5, max_tokens=800),
            instructions=["你是汉末史官，根据输入提取结构化记忆卡，格式为JSON。"],
            markdown=False,
        )
        extract_event_memories_with_agent(
            agent, db, state,
            decree_text="",  # 诏书内容可后续补入
            narrative=narrative,
            metrics_delta=metrics_delta,
            log_entries=log_entries,
            triggered_event_titles=triggered_event_titles,
        )
    except Exception:
        pass  # 记忆提取失败不影响推演主流程
    record_event_memories_from_resolution(
        db, state,
        decree_text="",
        narrative=narrative,
        metrics_delta=metrics_delta,
        log_entries=log_entries,
        triggered_event_titles=triggered_event_titles,
    )

    # ── 8. 写入 db ─────────────────────────────────────────────
    db.save_state("turn", state.turn)
    db.save_state("year", state.year)
    db.save_state("period", state.period)
    db.save_state("metrics", state.metrics)
    db.save_state("triggered_events", triggered_this_round)
    db.commit()

    return SimulationResult(
        fiscal=fiscal,
        faction_delta=faction_delta,
        warlord_changes=warlord_changes,
        historical=historical,
        threshold_crisis=threshold_crisis,
        random_events=random_events,
        narrative=narrative,
        metrics_delta=metrics_delta,
        log_entries=log_entries,
    )
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
from han_sim.flows import apply_monthly_flow, calc_faction_delta
from han_sim.issues import (
    apply_event_effect,
    filter_triggered_events,
    sample_random_events,
)
from han_sim.llm_config import load_llm_config
from han_sim.llm_model import create_chat_model, extract_agent_text
from han_sim.models import GameState
from han_sim.db import GameDB


@dataclass
class SimulationResult:
    fiscal: Dict          # 财政结算
    faction_delta: List[Dict]  # 藩镇变化
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
        llm_cfg = load_llm_config(
            base_url="https://api.minimax.chat/v1",
            model="MiniMax-M2.7-highspeed",
            api_key="",
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

    # ── 3. 事件聚合 ────────────────────────────────────────────
    historical, threshold_crisis = filter_triggered_events(
        state, db, already_triggered
    )
    random_events = sample_random_events(state, db, already_triggered)

    # 记录本次已触发 id
    triggered_this_round = already_triggered + [
        e["id"] for e in historical + threshold_crisis + random_events
    ]

    # ── 4. 事件效果结算 ────────────────────────────────────────
    metrics_delta: Dict[str, int] = {}
    log_entries: List[str] = []
    for e in historical + threshold_crisis + random_events:
        before = {k: state.metrics.get(k, 0) for k in ("汉室库", "声望", "威权", "藩镇")}
        effects = apply_event_effect(e, state, db)
        after = {k: state.metrics.get(k, 0) for k in before}
        for k in before:
            delta = after[k] - before[k]
            if delta != 0:
                metrics_delta[k] = metrics_delta.get(k, 0) + delta
        log_entries.extend(effects)

    # ── 5. 时间推进 ────────────────────────────────────────────
    state.next_period()
    state.clamp()

    # ── 6. LLM 叙事生成 ────────────────────────────────────────
    narrative = _generate_narration(
        state, fiscal, historical, threshold_crisis, random_events
    )

    # ── 7. 写入 db ─────────────────────────────────────────────
    db.save_state("turn", state.turn)
    db.save_state("year", state.year)
    db.save_state("period", state.period)
    db.save_state("metrics", state.metrics)
    db.save_state("triggered_events", triggered_this_round)
    db.commit()

    return SimulationResult(
        fiscal=fiscal,
        faction_delta=faction_delta,
        historical=historical,
        threshold_crisis=threshold_crisis,
        random_events=random_events,
        narrative=narrative,
        metrics_delta=metrics_delta,
        log_entries=log_entries,
    )
"""事件记忆生成：把诏书与月末推演结果压成渐进式记忆卡。"""

import json
import re
from typing import Any, Dict, List, Optional

try:
    from agno.agent import Agent
except ImportError:
    Agent = None  # type: ignore

from han_sim.agents import parse_agent_json, run_agent_text
from han_sim.db import GameDB
from han_sim.models import GameState


def _short(text: Any, limit: int = 80) -> str:
    s = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(s) <= limit:
        return s
    return s[: limit - 1] + "…"


def _title(text: Any, limit: int = 20) -> str:
    s = _short(text, limit)
    return s or "旧事记忆"


def _directive_summary(text: str) -> str:
    s = re.sub(r"奉天承运皇帝诏曰[:：]?", "", text or "").strip()
    s = s.replace("钦此。", "").replace("钦此", "").strip()
    return _short(s, 80)


def _tags(*values: Any) -> List[str]:
    out: List[str] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            items = value
        else:
            items = [value]
        for item in items:
            tag = str(item or "").strip()
            if tag and tag not in out:
                out.append(tag[:40])
    return out


def _source(
    db: GameDB,
    memory_id: int,
    source_kind: str,
    source_id: str,
    excerpt: str,
    **locator: Any,
) -> None:
    db.add_event_memory_source(
        memory_id,
        source_kind=source_kind,
        source_id=str(source_id or ""),
        excerpt=_short(excerpt, 200),
        locator={k: v for k, v in locator.items() if v not in ("", None)},
    )


def _write_llm_memories(db: GameDB, state: GameState, data: Any) -> int:
    """将 LLM 返回的记忆列表写入 DB。单个失败不阻断其余。"""
    if not isinstance(data, dict):
        return 0
    mem_list = data.get("memories") or []
    count = 0
    for item in mem_list:
        if not isinstance(item, dict):
            continue
        subject_type = str(item.get("subject_type") or "").strip()
        subject_id = str(item.get("subject_id") or "").strip()
        event_type = str(item.get("event_type") or "").strip()
        source_kind = str(item.get("source_kind") or "system").strip()
        source_id = str(item.get("source_id") or state.turn)
        if not subject_type or not subject_id or not event_type:
            continue
        try:
            importance = int(item.get("importance") or 3)
        except (TypeError, ValueError):
            importance = 3
        expires_turn_raw = item.get("expires_turn")
        try:
            expires_turn = int(expires_turn_raw) if expires_turn_raw not in (None, "", "null") else None
        except (TypeError, ValueError):
            expires_turn = None
        tags_val = item.get("tags") if isinstance(item.get("tags"), list) else []
        memory_id = db.upsert_event_memory(
            state,
            subject_type=subject_type,
            subject_id=subject_id,
            event_type=event_type,
            title=_title(item.get("title")),
            cause=_short(item.get("cause")),
            process=_short(item.get("process")),
            outcome=_short(item.get("outcome")),
            sentiment=str(item.get("sentiment") or "neutral"),
            importance=importance,
            tags=_tags(tags_val),
            source_kind=source_kind or "system",
            source_id=source_id,
            expires_turn=expires_turn,
        )
        for src in item.get("sources") or []:
            if isinstance(src, dict):
                _source(
                    db, memory_id,
                    str(src.get("source_kind") or "system"),
                    str(src.get("source_id") or ""),
                    src.get("excerpt") or "",
                    **(src.get("locator") or {}),
                )
        count += 1
    db.prune_event_memories_for_turn(state.turn, per_subject=3)
    return count


def extract_event_memories_with_agent(
    agent: Agent,
    db: GameDB,
    state: GameState,
    decree_text: str,
    narrative: str,
    metrics_delta: Dict[str, int],
    log_entries: List[str],
    triggered_event_titles: List[str],
) -> int:
    """诏书 + 月末推演叙事 → LLM 提取事件记忆卡。"""
    payload = {
        "turn": {"year": state.year, "period": state.period, "turn": state.turn},
        "decree_text": decree_text,
        "narrative": narrative,
        "metrics_delta": metrics_delta,
        "log_entries": log_entries,
        "triggered_events": triggered_event_titles,
        "instruction": "你是汉末史官，从本月诏书与叙事中提取渐进式事件记忆摘要卡。",
    }
    payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=False)
    raw = run_agent_text(agent, payload_json)
    data = parse_agent_json(raw, "记忆抽取")
    return _write_llm_memories(db, state, data)


def extract_chat_memories_for_minister(
    agent: Agent,
    db: GameDB,
    state: GameState,
    minister_name: str,
    chat_history: List[Dict[str, str]],
) -> int:
    """从单个大臣召对记录中提取承诺/建议/情报记忆。"""
    if not chat_history:
        return 0
    payload = {
        "turn": {"year": state.year, "period": state.period, "turn": state.turn},
        "minister_name": minister_name,
        "chat_history": chat_history,
        "instruction": "你是汉末史官，从本次召对中提取结构化记忆卡（承诺/建议/情报），闲聊跳过。",
    }
    payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=False)
    raw = run_agent_text(agent, payload_json)
    data = parse_agent_json(raw, "对话记忆抽取")
    if isinstance(data, dict):
        for item in data.get("memories") or []:
            if isinstance(item, dict):
                item["source_kind"] = "chat_message"
                item["source_id"] = f"{minister_name}:{state.turn}"
    return _write_llm_memories(db, state, data)


def record_event_memories_from_resolution(
    db: GameDB,
    state: GameState,
    decree_text: str,
    narrative: str,
    metrics_delta: Dict[str, int],
    log_entries: List[str],
    triggered_event_titles: List[str],
) -> None:
    """规则型记忆提取（不调用LLM）。诏书关键词 + 事件触发 + 指标大幅变动。"""
    # 1) 诏书中的关键决策
    if decree_text and len(decree_text) > 20:
        summary = _directive_summary(decree_text)
        if summary:
            memory_id = db.upsert_event_memory(
                state,
                subject_type="court",
                subject_id="朝廷",
                event_type="decree_issued",
                title=_title(f"颁布诏书：{summary[:18]}"),
                cause=summary,
                process=f"{state.year}年{state.period}月诏书颁行",
                outcome="诏已执行（已成往事）",
                sentiment="neutral",
                importance=3,
                tags=_tags("诏书", "朝廷", "颁旨"),
                source_kind="decree",
                source_id=str(state.turn),
            )
            _source(db, memory_id, "decree", str(state.turn), decree_text, turn=state.turn)

    # 2) 指标大幅变动
    for metric, delta in metrics_delta.items():
        if abs(delta) >= 8:
            sentiment = "positive" if delta > 0 else "negative"
            importance = 3 if abs(delta) < 15 else 4
            db.upsert_event_memory(
                state,
                subject_type="court",
                subject_id="朝廷",
                event_type="metric_change",
                title=f"【{metric}】{'+' if delta > 0 else ''}{delta}",
                cause=f"本月推演引发{metric}变动",
                process=f"{metric}{'+' if delta > 0 else ''}{delta}",
                outcome=f"{metric}当前值待查",
                sentiment=sentiment,
                importance=importance,
                tags=_tags("指标", metric, "财政", "月末推演"),
                source_kind="simulation",
                source_id=str(state.turn),
            )

    # 3) 触发事件
    for event_title in triggered_event_titles:
        db.upsert_event_memory(
            state,
            subject_type="court",
            subject_id="朝廷",
            event_type="event_triggered",
            title=f"事件：{_title(event_title)}",
            cause=f"{state.year}年{state.period}月事件触发",
            process="待查",
            outcome="事件效果已结算",
            sentiment="neutral",
            importance=3,
            tags=_tags("事件", "触发", event_title),
            source_kind="simulation",
            source_id=str(state.turn),
        )

    # 4) 月末叙事摘要
    if narrative and len(narrative) > 40:
        db.upsert_event_memory(
            state,
            subject_type="court",
            subject_id="朝廷",
            event_type="monthly_narrative",
            title=f"【{state.year}年{state.period}月】{_title(narrative)}",
            cause=f"{state.year}年{state.period}月月度叙事",
            process=narrative[:80],
            outcome="叙事已存档",
            sentiment="neutral",
            importance=2,
            tags=_tags("叙事", "月末", f"{state.year}年"),
            source_kind="simulation_narrative",
            source_id=str(state.turn),
        )
"""事件记忆生成：把诏书与月末推演结果压成渐进式记忆卡。L5。

增强版：从叙事提取结构化记忆卡、大臣召对记忆、规则兜底记忆写入。
"""

import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from agno.agent import Agent
except ImportError:
    Agent = None  # type: ignore

from han_sim.agents import parse_agent_json, parse_agent_json_full, run_agent_text
from han_sim.db import GameDB
from han_sim.models import GameState


# v5.1.0 P0-1: TTL 映射 (importance → 回合数). 5 = 永久 (-1)
TTL_BY_IMPORTANCE: Dict[int, int] = {
    1: 6,
    2: 12,
    3: 24,
    4: 48,
    5: -1,  # 永久
}


def compute_expires_turn(importance: int, current_turn: int) -> int:
    """根据 importance 档位 + 当前回合, 计算 expires_turn。

    importance 5 → -1 (永久, 永不过期)
    其他档位 → current_turn + TTL_BY_IMPORTANCE[imp]
    importance 越界 (0 / 负数 / >5) 自动夹到 [1, 5]
    """
    try:
        importance = int(importance)
    except (TypeError, ValueError):
        importance = 3
    importance = max(1, min(5, importance))
    ttl = TTL_BY_IMPORTANCE.get(importance, 12)
    if ttl == -1:
        return -1
    return int(current_turn) + ttl


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
                source_id=f"{state.turn}:{metric}",
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


# ── LLM 抽取结构化记忆卡 ────────────────────────────────────────────────────


_MEMORY_EXTRACTOR_PROMPT = (
    "你是汉末史官，从本月叙事中提取渐进式事件记忆摘要卡。\n"
    "输出严格 JSON，不加任何解释：\n"
    "{\n"
    '  "memories": [\n'
    '    {\n'
    '      "subject_type": "character|region|army|court|faction",\n'
    '      "subject_id": "人物名/地区名/势力名",\n'
    '      "event_type": "edict_issued|issue_progress|issue_resolved|metric_change|event_triggered|...",\n'
    '      "title": "事件标题（20字以内）",\n'
    '      "cause": "起因（80字以内）",\n'
    '      "process": "过程（80字以内）",\n'
    '      "outcome": "结果（80字以内）",\n'
    '      "sentiment": "positive|negative|neutral",\n'
    '      "importance": 1-5,\n'
    '      "tags": ["标签1", "标签2"]\n'
    '    }\n'
    '  ]\n'
    "}\n"
    "规则：只写有实质内容的事件记忆；闲聊/无意义对话不写；每主题最多3条。\n"
    "importance: 1=日常琐事, 2=普通事件, 3=重要事件, 4=重大转折, 5=历史节点。"
)


def extract_llm_memories(narrative: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从叙事中用 LLM 抽取结构化记忆卡。

    Args:
        narrative: 月末推演叙事文本
        context: 包含 turn/year/period/decree_text/metrics_delta 等上下文

    Returns:
        结构化记忆卡列表
    """
    if not narrative or len(narrative) < 20:
        return []

    payload = {
        "turn": context.get("turn", {}),
        "decree_text": context.get("decree_text", ""),
        "narrative": narrative,
        "metrics_delta": context.get("metrics_delta", {}),
        "log_entries": context.get("log_entries", []),
        "triggered_events": context.get("triggered_events", []),
        "instruction": "提取渐进式事件记忆摘要卡和来源摘录。",
    }
    payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=False)

    # 使用记忆提取 Agent（如果可用）
    try:
        from han_sim.agents import create_memory_extractor_agent
        agent = create_memory_extractor_agent()
        raw = run_agent_text(agent, payload_json)
        data = parse_agent_json_full(raw)
        if data and isinstance(data, dict):
            memories = data.get("memories") or []
            return [m for m in memories if isinstance(m, dict)]
    except Exception:
        pass

    # fallback：简单规则提取
    return []


def _significant_change(field: str, old_val: Any, new_val: Any, threshold: int = 8) -> bool:
    """判断是否显著变化。

    Args:
        field: 字段名
        old_val: 旧值
        new_val: 新值
        threshold: 变化阈值（默认8）

    Returns:
        True if change is significant
    """
    try:
        old_int = int(old_val or 0)
        new_int = int(new_val or 0)
    except (TypeError, ValueError):
        return field in {"natural_disaster", "human_disaster", "status", "last_action"}

    # 特殊字段的敏感度调整
    sensitive_fields = {"arrears", "unrest", "military_pressure", "stance"}
    if field in sensitive_fields:
        return abs(new_int - old_int) >= 3

    return abs(new_int - old_int) >= threshold


def _write_actor_memory(
    db: GameDB,
    state: GameState,
    actor: str,
    event_type: str,
    title: str,
    cause: str,
    process: str,
    outcome: str,
    sentiment: str,
    importance: int,
    tags: List[str],
    source_kind: str,
    source_id: str,
    narrative: str = "",
    decree_text: str = "",
) -> int:
    """写入人物记忆（单个）。

    Returns:
        memory_id or 0 if failed
    """
    if not actor:
        return 0

    memory_id = db.upsert_event_memory(
        state,
        subject_type="character",
        subject_id=actor,
        event_type=event_type,
        title=_title(title),
        cause=_short(cause),
        process=_short(process),
        outcome=_short(outcome),
        sentiment=sentiment,
        importance=importance,
        tags=_tags(actor, tags),
        source_kind=source_kind,
        source_id=source_id,
    )

    if memory_id:
        if decree_text:
            _source(db, memory_id, "decree", state.turn, decree_text, turn=state.turn, field="decree_text")
        if narrative:
            _source(db, memory_id, "simulation_narrative", state.turn, narrative, turn=state.turn, field="narrative")

    return memory_id


def _normalize_memory_item(item: Dict[str, Any], state: GameState) -> Optional[Dict[str, Any]]:
    """归一化记忆条目，补充默认值。"""
    if not isinstance(item, dict):
        return None

    subject_type = str(item.get("subject_type") or "").strip()
    subject_id = str(item.get("subject_id") or "").strip()
    event_type = str(item.get("event_type") or "").strip()
    source_kind = str(item.get("source_kind") or "system").strip()
    source_id = str(item.get("source_id") or str(state.turn)).strip()

    if not subject_type or not subject_id or not event_type:
        return None

    try:
        importance = int(item.get("importance") or 3)
    except (TypeError, ValueError):
        importance = 3

    expires_raw = item.get("expires_turn")
    try:
        expires_turn = int(expires_raw) if expires_raw not in (None, "", "null") else None
    except (TypeError, ValueError):
        expires_turn = None

    return {
        "subject_type": subject_type,
        "subject_id": subject_id,
        "event_type": event_type,
        "title": _title(item.get("title")),
        "cause": _short(item.get("cause")),
        "process": _short(item.get("process")),
        "outcome": _short(item.get("outcome")),
        "sentiment": str(item.get("sentiment") or "neutral"),
        "importance": max(1, min(5, importance)),
        "tags": _tags(*item.get("tags", [])),
        "source_kind": source_kind,
        "source_id": source_id,
        "expires_turn": expires_turn,
        "sources": item.get("sources") or [],
    }


def _write_llm_memories(memories: List[Dict[str, Any]], db: GameDB, state: GameState) -> int:
    """写入 LLM 生成的记忆列表（含每主题最多3条的修剪）。

    Args:
        memories: 归一化后的记忆列表
        db: GameDB 实例
        state: GameState

    Returns:
        写入的记忆数量
    """
    if not memories:
        return 0

    # 按 subject_id 分组，每组最多3条
    subject_memories: Dict[str, List[Tuple[int, Dict[str, Any]]]] = {}
    for mem in memories:
        if not isinstance(mem, dict):
            continue
        sid = f"{mem.get('subject_type', '')}:{mem.get('subject_id', '')}"
        imp = mem.get("importance", 3)
        if sid not in subject_memories:
            subject_memories[sid] = []
        subject_memories[sid].append((imp, mem))

    # 每组只保留最重要的3条
    pruned: List[Dict[str, Any]] = []
    for sid, mems in subject_memories.items():
        mems.sort(key=lambda x: x[0], reverse=True)
        pruned.extend([m for _, m in mems[:3]])

    count = 0
    for item in pruned:
        memory_id = db.upsert_event_memory(
            state,
            subject_type=str(item["subject_type"]),
            subject_id=str(item["subject_id"]),
            event_type=str(item["event_type"]),
            title=str(item["title"]),
            cause=str(item["cause"]),
            process=str(item["process"]),
            outcome=str(item["outcome"]),
            sentiment=str(item["sentiment"]),
            importance=int(item["importance"]),
            tags=list(item["tags"]),
            source_kind=str(item["source_kind"]),
            source_id=str(item["source_id"]),
            expires_turn=item.get("expires_turn"),
        )
        if not memory_id:
            continue
        count += 1

        # 写入来源摘录
        for src in item.get("sources", []):
            if not isinstance(src, dict):
                continue
            src_kind = str(src.get("source_kind") or item["source_kind"]).strip()
            src_id = str(src.get("source_id") or item["source_id"]).strip()
            db.add_event_memory_source(
                memory_id,
                source_kind=src_kind,
                source_id=src_id,
                excerpt=_short(src.get("excerpt"), 200),
                locator=src.get("locator") or {},
            )

    # 修剪每主题最多3条
    db.prune_event_memories_for_turn(state.turn, per_subject=3)
    return count


def record_event_memories_from_resolution(
    db: GameDB,
    state: GameState,
    decree_text: str,
    narrative: str,
    metrics_delta: Dict[str, int],
    log_entries: List[str],
    triggered_event_titles: List[str],
) -> None:
    """规则型记忆提取（不调用LLM）。

    从诏书关键词提取、指标大幅变动、事件触发中生成记忆卡。
    """
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
                source_id=f"{state.turn}:{metric}",
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


def extract_chat_memories_for_minister(
    agent: Agent,
    db: GameDB,
    state: GameState,
    minister_name: str,
    chat_history: List[Dict[str, str]],
) -> int:
    """从单个大臣召对记录中提取承诺/建议/情报记忆。

    Args:
        agent: 记忆提取 Agent
        db: GameDB 实例
        state: GameState
        minister_name: 大臣姓名
        chat_history: 召对聊天记录

    Returns:
        写入的记忆数量
    """
    if not chat_history:
        return 0

    payload = {
        "turn": {"year": state.year, "period": state.period, "turn": state.turn},
        "minister_name": minister_name,
        "chat_history": chat_history,
        "instruction": "从本次召对中提取结构化记忆卡（承诺/建议/情报），闲聊跳过。",
    }
    payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=False)
    raw = run_agent_text(agent, payload_json)
    data = parse_agent_json_full(raw)

    if isinstance(data, dict):
        memories = data.get("memories") or []
        # 强制 source_kind 为 chat_message
        for item in memories:
            if isinstance(item, dict):
                item["source_kind"] = "chat_message"
                item["source_id"] = f"{minister_name}:{state.turn}"

        # 归一化并写入
        normalized = [_normalize_memory_item(m, state) for m in memories]
        normalized = [m for m in normalized if m is not None]
        return _write_llm_memories(normalized, db, state)

    return 0
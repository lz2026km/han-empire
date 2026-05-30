"""Issue 系统：候选事件、issue 立项/推进/结案、tracker 输出落地。L5。

与 decree 诏书系统联动，天子通过诏书推动事项进展。
通过 bind_content() 注入 GameContent（取 EVENTS/SEED_EVENTS/EVENT_BY_ID）。
"""

from __future__ import annotations

import json
import re
import sqlite3
from typing import Dict, List, Optional

from han_sim.constants import TURN_UNIT
from han_sim.content import GameContent
from han_sim.db import GameDB
from han_sim.models import Event, GameState

_content: Optional[GameContent] = None


def bind_content(content: GameContent) -> None:
    global _content
    _content = content


def _ctx() -> GameContent:
    if _content is None:
        raise RuntimeError("issues.bind_content() 未调用：GameContent 未注入。")
    return _content


# 给 issue 结案触发的副作用落库用的占位事件。
_ISSUE_PSEUDO_EVENT = Event(
    id="issue_resolution", title="局势结案", kind="月末", summary="",
    urgency=0, severity=0, credibility=100, interests=[], audiences=[],
)


def _apply_metric_dict(state: GameState, metrics: Dict[str, int]) -> Dict[str, int]:
    """应用 metric 变化，返回实际落账的 delta。"""
    applied: Dict[str, int] = {}
    for k, v in metrics.items():
        if k not in state.metrics:
            continue
        try:
            delta = int(v)
        except (TypeError, ValueError):
            continue
        if delta == 0:
            continue
        old = state.metrics[k]
        state.metrics[k] = max(0, min(100, old + delta))
        applied[k] = state.metrics[k] - old
    return applied


def _apply_economy_list(db: GameDB, state: GameState, economy: List[Dict]) -> List[Dict]:
    """应用经济类效果（国库/内库等）。"""
    applied: List[Dict] = []
    for item in economy:
        if not isinstance(item, dict):
            continue
        account = str(item.get("account") or "")
        delta = 0
        try:
            delta = int(item.get("delta") or 0)
        except (TypeError, ValueError):
            continue
        if delta == 0 or account not in state.metrics:
            continue
        old = state.metrics[account]
        state.metrics[account] = max(0, old + delta)
        applied.append({
            "account": account,
            "delta": state.metrics[account] - old,
        })
    return applied


def _apply_faction_dict(db: GameDB, factions: Dict[str, int]) -> List[Dict]:
    """派系影响力变化。"""
    applied: List[Dict] = []
    for fid, delta in factions.items():
        try:
            delta = int(delta)
        except (TypeError, ValueError):
            continue
        if delta == 0:
            continue
        row = db.conn.execute(
            "SELECT id, leverage FROM factions WHERE id=?",
            (str(fid),),
        ).fetchone()
        if row is None:
            continue
        new_leverage = max(0, min(100, int(row["leverage"]) + delta))
        db.conn.execute(
            "UPDATE factions SET leverage=? WHERE id=?",
            (new_leverage, str(fid)),
        )
        applied.append({"faction": fid, "leverage_delta": new_leverage - int(row["leverage"])})
    if applied:
        db.conn.commit()
    return applied


def issue_to_payload(row: sqlite3.Row, recent_advances: List[sqlite3.Row]) -> Dict[str, object]:
    """喂给推演 agent 的事项精简视图：状态、进度、效果、最近一次推进。"""
    keys = row.keys() if hasattr(row, "keys") else []
    resolve_cond = row["resolve_condition"] if "resolve_condition" in keys else ""
    fail_cond = row["fail_condition"] if "fail_condition" in keys else ""
    return {
        "issue_id": int(row["id"]),
        "title": row["title"],
        "description": row["description"] if "description" in keys else "",
        "状态": row["status"],
        "进度": int(row["progress"] if "progress" in keys else row.get("bar_value", 0)),
        "proposed_by": row["proposed_by"] if "proposed_by" in keys else "",
        f"当前每{TURN_UNIT}效果": json.loads(row["ongoing_effects"] or "{}"),
        "失败效果": json.loads(row["effect_on_fail"] or "{}"),
        "成功效果": json.loads(row["effect_on_resolve"] or "{}"),
        "结案条件": resolve_cond or "(未填)",
        "失败条件": fail_cond or "(未填)",
        "tags": json.loads(row["tags"] or "[]"),
        f"上{TURN_UNIT}推进": (
            {
                "delta_bar": int(recent_advances[0]["delta_bar"]),
                "narrative": recent_advances[0]["narrative"],
            }
            if recent_advances else None
        ),
    }


def _spawned_event_refs(db: GameDB) -> set:
    refs: set = set()
    for r in db.conn.execute("SELECT origin_ref FROM issues WHERE origin_kind='event_pool'").fetchall():
        if r["origin_ref"]:
            refs.add(r["origin_ref"])
    for r in db.conn.execute("SELECT event_id FROM event_triggers").fetchall():
        if r["event_id"]:
            refs.add(r["event_id"])
    return refs


def _event_window_open(ev: Event, state: GameState) -> bool:
    """Return True when the current date is inside an event's optional trigger window."""
    if ev.trigger_year > 0:
        if state.year < ev.trigger_year:
            return False
        if state.year == ev.trigger_year and ev.trigger_month > 0 and state.period < ev.trigger_month:
            return False
    if ev.trigger_end_year > 0:
        if state.year > ev.trigger_end_year:
            return False
        if state.year == ev.trigger_end_year and ev.trigger_end_month > 0 and state.period > ev.trigger_end_month:
            return False
    return True


_GATE_AGG_FUNCS = {
    "max": max,
    "min": min,
    "sum": sum,
    "avg": lambda xs: sum(xs) // max(1, len(xs)),
}


def _eval_gate_key(key: str, metrics: Dict[str, int], db: GameDB) -> Optional[int]:
    """把 gate key 解析成一个 int 值。形式：
      - 'metric_name'                           → metrics[key]
      - 'region.<id>.<field>'                   → regions 表
      - 'region.<id1>|<id2>|.<field>.<agg>'     → 多省聚合 (max/min/avg/sum)
      - 'power.<id>.<field>' / 多 + agg
    解析失败/数据缺失返回 None（gate 视为不通过，由调用方处理）。
    """
    if "." not in key:
        if key in metrics:
            return int(metrics[key])
        return None
    parts = key.split(".")
    table = parts[0]
    if table not in ("region", "power"):
        # 通用 metrics
        if table == "metrics" and len(parts) >= 2:
            return int(metrics.get(parts[1], 0))
        return None
    # 末段可能是 agg，先抽出
    agg = None
    if parts[-1] in _GATE_AGG_FUNCS:
        agg = parts[-1]
        parts = parts[:-1]
    if len(parts) < 3:
        return None
    field = parts[-1]
    id_segment = ".".join(parts[1:-1])
    ids = id_segment.split("|") if "|" in id_segment else [id_segment]
    ids = [x for x in ids if x]
    if not ids:
        return None
    values: List[int] = []
    for cid in ids:
        row = None
        if table == "region":
            row = db.conn.execute(f"SELECT {field} FROM regions WHERE id=?", (cid,)).fetchone()
        elif table == "power":
            row = db.conn.execute(f"SELECT {field} FROM powers WHERE id=?", (cid,)).fetchone()
        if row is None:
            return None
        try:
            values.append(int(row[0]))
        except (TypeError, ValueError):
            return None
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    if agg is None:
        agg = "min"
    return _GATE_AGG_FUNCS[agg](values)


def _gate_passed(gate: Dict[str, str], metrics: Dict[str, int], db: GameDB) -> bool:
    """trigger_gate 全部条件满足才返回 True。条件形如 '<=240'。"""
    for key, cond in gate.items():
        m = re.match(r"^(>=|<=|>|<|==)\s*(-?\d+)$", cond.strip())
        if not m:
            return False
        op, num = m.group(1), int(m.group(2))
        val = _eval_gate_key(key, metrics, db)
        if val is None:
            return False
        if op == ">=" and not val >= num:
            return False
        if op == "<=" and not val <= num:
            return False
        if op == ">" and not val > num:
            return False
        if op == "<" and not val < num:
            return False
        if op == "==" and not val == num:
            return False
    return True


def gather_candidate_events(state: GameState, db: GameDB) -> List[Event]:
    """程序筛选：历史锚定事件按 trigger 时间到点+trigger_condition 达标、
    seed 情势按 trigger_gate 达标，都排除已触发过的。
    返回的候选清单交推演 agent 因果判定是否真触发。
    """
    c = _ctx()
    spawned = _spawned_event_refs(db)
    candidates: List[Event] = []

    # 历史锚定 EVENTS
    for ev in getattr(c, "events", []):
        if ev.id in spawned or ev.trigger_year <= 0:
            continue
        if not _event_window_open(ev, state):
            continue
        if ev.trigger_condition and not _gate_passed(ev.trigger_condition, state.metrics, db):
            continue
        candidates.append(ev)

    # seed 情势
    for ev in getattr(c, "seed_events", []):
        if ev.id in spawned:
            continue
        if not _event_window_open(ev, state):
            continue
        if _gate_passed(ev.trigger_gate, state.metrics, db):
            candidates.append(ev)

    return candidates


def _bar_ascii(value: int, width: int = 20) -> str:
    value = max(0, min(100, int(value)))
    pos = int(round(value / 100 * (width - 1)))
    return "●" + ("━" * pos) + "○" + ("━" * (width - 1 - pos))


def _format_issue_ongoing(ongoing_raw: str) -> str:
    """简短描述每月固定影响。"""
    try:
        eff = json.loads(ongoing_raw or "{}")
    except Exception:
        return ""
    parts: List[str] = []
    metrics = eff.get("metrics") or {}
    for key, val in metrics.items():
        if isinstance(val, (int, float)) and val:
            parts.append(f"{key}{'+' if val > 0 else ''}{int(val)}")
    return "、".join(parts)


def show_active_issues(db: GameDB) -> None:
    """打印当前进行中的事项（调试用）。"""
    issues = db.list_active_issues()
    if not issues:
        return
    print(f"─── 待办事项 ({len(issues)}) ───")
    for row in issues:
        progress = int(row.get("progress", 0))
        bar = _bar_ascii(progress)
        status = row.get("status", "active")
        title = row.get("title", "")
        proposed_by = row.get("proposed_by", "")
        print(f"  #{int(row['id'])} [{status}] {title}")
        print(f"    {bar}  {progress}%  提出者:{proposed_by}")
        ongoing = _format_issue_ongoing(row.get("ongoing_effects", ""))
        if ongoing:
            print(f"    每{TURN_UNIT}：{ongoing}")
    print()


# 会崩坏的局势 kinds
_COLLAPSIBLE_KINDS = frozenset({
    "人祸", "兵变", "流寇", "民变", "抗税",
})


def _normalize_cancellable(raw: object) -> str:
    """归一化 cancellable 值。"""
    val = str(raw or "").strip().lower()
    if val in ("decree", "never", "by_progress"):
        return val
    if val in ("by_policy", "policy"):
        return "decree"
    if val in ("none", "no", "false"):
        return "never"
    if val in ("yes", "true", "auto"):
        return "by_progress"
    return "by_progress"


def _compute_inertia(ni: Dict[str, object]) -> int:
    """从 expected_months 算 inertia。"""
    em_raw = ni.get("expected_months")
    if em_raw is not None:
        try:
            em = int(em_raw)
        except (TypeError, ValueError):
            em = 0
        if em != 0:
            inertia = round(100 / em)
            return max(-10, min(10, inertia))
    return max(-10, min(10, int(ni.get("inertia") or 0)))


def event_to_issue(db: GameDB, state: GameState, ev: Event) -> Optional[int]:
    """把一个预设 event（EVENTS / SEED_EVENTS）落成一条 situation issue。
    供推演判定触发后调用。已触发过（origin_ref 命中）则跳过返回 None。
    """
    if db.find_any_issue_by_origin("event_pool", ev.id) is not None:
        return None
    # 初值由 severity 推一个偏中性的 progress
    progress = max(20, min(60, 50 - int(ev.severity / 5)))
    # 默认 inertia
    ongoing: Dict[str, object] = {}
    inertia = -5

    if ev.kind in ("天灾", "灾情", "饥荒"):
        ongoing = {"metrics": {"声望": -2}}
        inertia = -10
    elif ev.kind in ("人祸", "兵变", "流寇", "民变", "抗税"):
        ongoing = {"metrics": {"声望": -2}}
        inertia = -10
    elif ev.kind in ("外族", "边事"):
        ongoing = {"metrics": {"威权": -1}}
        inertia = -5
    elif ev.kind in ("丰收", "祥瑞"):
        ongoing = {"metrics": {"声望": 2}}
        inertia = +10
    elif ev.kind in ("友邦", "归附", "盟约"):
        ongoing = {"metrics": {"威权": 1}}
        inertia = +5

    try:
        return db.insert_issue(
            state,
            title=ev.title,
            description=ev.summary[:200] if ev.summary else "",
            origin_kind="event_pool",
            origin_ref=ev.id,
            progress=progress,
            proposed_by="event_pool",
            tags=[ev.kind],
            ongoing_effects=ongoing,
            cancellable="never",
            effect_on_resolve={"metrics": {"声望": 5}} if ev.kind not in _COLLAPSIBLE_KINDS else {},
            effect_on_fail={"metrics": {"声望": -5, "威权": -3}} if ev.kind in _COLLAPSIBLE_KINDS else {},
            resolve_condition=ev.resolve_condition or "",
            fail_condition=ev.fail_condition or "",
        )
    except Exception as exc:
        print(f"[WARN] 事件 {ev.title} 立项失败：{exc}；跳过。")
        return None


# ── 诏书联动 ────────────────────────────────────────────────────────────────────


def apply_issue_tracker_output(
    db: GameDB,
    state: GameState,
    tracker_output: Dict[str, object],
) -> Dict[str, object]:
    """落地推演 agent 的 tracker JSON 到 db 和 state。"""
    touched_ids: set = set()
    applied_advances: List[Dict[str, object]] = []
    applied_new: List[Dict[str, object]] = []
    applied_closes: List[Dict[str, object]] = []
    applied_cancels: List[Dict[str, object]] = []

    # 1) advances
    for adv in tracker_output.get("advances", []) or []:
        try:
            issue_id = int(adv.get("issue_id"))
        except (TypeError, ValueError):
            continue
        delta_bar = int(adv.get("delta_bar") or 0)
        stage_text = str(adv.get("stage_text") or "")[:120]
        narrative = str(adv.get("narrative") or "")[:400]
        metric_delta_raw = adv.get("metric_delta") or {}
        applied_metrics = _apply_metric_dict(state, metric_delta_raw if isinstance(metric_delta_raw, dict) else {})
        inertia_delta = int(adv.get("inertia_delta") or 0)

        new_row = db.advance_issue(
            state, issue_id,
            trigger_kind="decree",
            delta_bar=delta_bar,
            stage_text=stage_text,
            narrative=narrative,
            metric_delta=applied_metrics,
            inertia_delta=inertia_delta,
        )
        if new_row is None:
            continue
        touched_ids.add(issue_id)

        # 终结结算
        if new_row["status"] == "resolved":
            effect = json.loads(new_row["effect_on_resolve"] or "{}")
            _apply_metric_dict(state, effect.get("metrics") or {})
            _apply_economy_list(db, state, effect.get("economy") or [])
        elif new_row["status"] == "failed":
            effect = json.loads(new_row["effect_on_fail"] or "{}")
            _apply_metric_dict(state, effect.get("metrics") or {})
            _apply_economy_list(db, state, effect.get("economy") or [])

        applied_advances.append({
            "issue_id": issue_id,
            "title": new_row["title"],
            "from_value": int(new_row["progress"]) - delta_bar,
            "to_value": int(new_row["progress"]),
            "stage_text": new_row["stage_text"],
            "status": new_row["status"],
            "narrative": narrative,
        })

    # 2) new_issues
    for ni in tracker_output.get("new_issues", []) or []:
        title = str(ni.get("title") or "")
        origin_kind = str(ni.get("origin_kind") or "").lower()
        if origin_kind == "event_pool":
            event_id = str(ni.get("id") or ni.get("origin_ref") or "").strip()
            event_by_id = getattr(_ctx(), "event_by_id", {})
            ev = event_by_id.get(event_id)
            if ev is None:
                applied_new.append({"title": title or event_id, "rejected": True, "reason": "event_pool id 非预设事件"})
                continue
            if getattr(ev, "event_type", "situation") != "situation":
                db.mark_event_triggered(state, ev.id)
                applied_new.append({"title": ev.title, "rejected": False, "reason": f"event_type 非 situation"})
                continue
            issue_id = event_to_issue(db, state, ev)
            if issue_id is None:
                applied_new.append({"title": title, "rejected": True, "reason": "事件已触发过"})
            else:
                applied_new.append({"issue_id": issue_id, "title": ev.title, "rejected": False})
            continue
        if origin_kind not in ("decree", ""):
            applied_new.append({"title": title, "rejected": True, "reason": f"来源 '{origin_kind}' 不许新立"})
            continue

        kind = str(ni.get("kind") or "initiative")
        total_active = len(db.list_active_issues())
        if total_active >= 20:
            applied_new.append({"title": title, "rejected": True, "reason": "事项过多，朝廷难再添新工。"})
            continue

        try:
            issue_id = db.insert_issue(
                state,
                title=title[:60] or "无名事项",
                description=str(ni.get("description") or "")[:200],
                origin_kind="decree",
                origin_ref=str(ni.get("origin_ref") or ""),
                progress=int(ni.get("progress", ni.get("bar_value", 25))),
                proposed_by=str(ni.get("proposed_by") or "天子"),
                total_steps=int(ni.get("total_steps", 0)),
                current_step=int(ni.get("current_step", 0)),
                deadline_turn=int(ni.get("deadline_turn") or 0) if ni.get("deadline_turn") else 0,
                tags=list(ni.get("tags") or []),
                ongoing_effects=dict(ni.get("ongoing_effects") or {}),
                cancellable=_normalize_cancellable(ni.get("cancellable")),
                effect_on_resolve=dict(ni.get("effect_on_resolve") or {}),
                effect_on_fail=dict(ni.get("effect_on_fail") or {}),
                resolve_condition=str(ni.get("resolve_condition") or "")[:300],
                fail_condition=str(ni.get("fail_condition") or "")[:300],
            )
            applied_new.append({"issue_id": issue_id, "title": title, "rejected": False})
        except Exception as exc:
            print(f"[WARN] new_issue 落库失败：{exc}；跳过 {title}")
            applied_new.append({"title": title, "rejected": True, "reason": str(exc)})

    # 3) closes
    for cl in tracker_output.get("close_issues", []) or []:
        try:
            issue_id = int(cl.get("issue_id"))
        except (TypeError, ValueError):
            continue
        reason = str(cl.get("reason") or "").strip().lower()
        if reason not in ("resolved", "failed"):
            print(f"[WARN] close_issues: reason 非法 '{reason}'，跳过 issue {issue_id}")
            continue
        narrative = str(cl.get("narrative") or "")[:400]
        try:
            new_row = db.close_issue(state, issue_id, reason=reason, narrative=narrative)
        except Exception as exc:
            print(f"[WARN] close_issue 落库失败：{exc}；跳过 issue {issue_id}")
            continue
        if new_row is None:
            continue
        touched_ids.add(issue_id)

        if reason == "resolved":
            effect = json.loads(new_row["effect_on_resolve"] or "{}")
        else:
            effect = json.loads(new_row["effect_on_fail"] or "{}")
        _apply_metric_dict(state, effect.get("metrics") or {})
        _apply_economy_list(db, state, effect.get("economy") or [])

        applied_closes.append({
            "issue_id": issue_id,
            "title": new_row["title"],
            "reason": reason,
            "narrative": narrative,
        })

    # 4) cancels
    for cn in tracker_output.get("cancels", []) or []:
        try:
            issue_id = int(cn.get("issue_id"))
        except (TypeError, ValueError):
            continue
        row = db.conn.execute("SELECT * FROM issues WHERE id=?", (issue_id,)).fetchone()
        if row is None or row["status"] != "active":
            continue
        if row["cancellable"] != "decree":
            # 不可撤
            db.advance_issue(
                state, issue_id,
                trigger_kind="decree",
                delta_bar=0,
                stage_text=row["stage_text"],
                narrative=str(cn.get("narrative") or "此事非诏可消。")[:400],
                metric_delta={"威权": -2},
            )
            state.metrics["威权"] = max(0, int(state.metrics.get("威权", 0)) - 2)
            touched_ids.add(issue_id)
            applied_cancels.append({"issue_id": issue_id, "rejected": True, "title": row["title"]})
            continue
        # 可撤
        cost = cn.get("applied_cost") or {}
        if isinstance(cost, dict):
            _apply_metric_dict(state, cost.get("metrics") or {})
            _apply_economy_list(db, state, cost.get("economy") or [])
        db.cancel_issue(
            state, issue_id,
            narrative=str(cn.get("narrative") or "")[:400],
            applied_cost=cost if isinstance(cost, dict) else {},
        )
        touched_ids.add(issue_id)
        applied_cancels.append({"issue_id": issue_id, "rejected": False, "title": row["title"]})

    state.clamp()
    return {
        "advances": applied_advances,
        "new_issues": applied_new,
        "closes": applied_closes,
        "cancels": applied_cancels,
        "touched_ids": sorted(touched_ids),
    }


def apply_issue_inertia_and_ongoing(
    db: GameDB,
    state: GameState,
    touched_ids: Optional[set] = None,
) -> None:
    """每月末应用进行中 issue 的 inertia 漂移和 ongoing_effects。"""
    _ = touched_ids
    active = db.list_active_issues()
    period_metric_acc: Dict[str, int] = {}

    for row in active:
        issue_id = int(row["id"])
        bar = int(row["progress"])
        inertia = int(row.get("inertia", 0))

        # 1) inertia 漂移
        if inertia != 0:
            new_bar = max(0, min(100, bar + inertia))
            actual = new_bar - bar
            if actual != 0:
                new_row = db.advance_issue(
                    state, issue_id,
                    trigger_kind="inertia",
                    delta_bar=actual,
                    stage_text=row["stage_text"],
                    narrative="局势自有其势，本月按其本然推移。",
                    metric_delta={},
                )
                if new_row is None:
                    continue
                if new_row["status"] == "resolved":
                    effect = json.loads(new_row["effect_on_resolve"] or "{}")
                    _apply_metric_dict(state, effect.get("metrics") or {})
                    _apply_economy_list(db, state, effect.get("economy") or [])
                    continue
                elif new_row["status"] == "failed":
                    effect = json.loads(new_row["effect_on_fail"] or "{}")
                    _apply_metric_dict(state, effect.get("metrics") or {})
                    _apply_economy_list(db, state, effect.get("economy") or [])
                    continue
                row = db.conn.execute("SELECT * FROM issues WHERE id=?", (issue_id,)).fetchone()
                if row is None:
                    continue
                bar = int(row["progress"])

        # 2) ongoing_effects
        ongoing = json.loads(row.get("ongoing_effects") or "{}")
        if not ongoing:
            continue
        # 折扣系数
        if bar >= 80:
            scale = 0.3
        elif bar >= 40:
            scale = 0.6
        else:
            scale = 1.0

        metric_part: Dict[str, int] = {}
        for k, v in (ongoing.get("metrics") or {}).items():
            try:
                raw = int(v)
            except (TypeError, ValueError):
                continue
            if raw == 0:
                continue
            scaled = int(round(raw * scale))
            if scaled == 0:
                continue
            cap = 5  # 每月最多 +/-5
            already = period_metric_acc.get(k, 0)
            remaining = cap - abs(already)
            if remaining <= 0:
                continue
            if scaled > 0:
                allowed = min(scaled, remaining)
            else:
                allowed = max(scaled, -remaining)
            if allowed == 0:
                continue
            state.metrics[k] = int(state.metrics.get(k, 0)) + allowed
            period_metric_acc[k] = already + allowed
            metric_part[k] = allowed

        economy_part = _apply_economy_list(db, state, ongoing.get("economy") or [])

        if metric_part or economy_part:
            db.conn.execute(
                """
                INSERT INTO issue_advances (
                    issue_id, turn, trigger_kind, delta_bar,
                    from_value, to_value, narrative, metric_delta
                ) VALUES (?, ?, 'ongoing', 0, ?, ?, ?, ?)
                """,
                (
                    issue_id, state.turn, bar, bar,
                    f"持续效果落账 (折扣 {int(scale*100)}%)",
                    json.dumps({"metrics": metric_part, "economy": economy_part}, ensure_ascii=False),
                ),
            )
            db.conn.commit()

    state.clamp()


def get_active_issues(db: GameDB) -> List[Dict]:
    """返回所有进行中的事项列表。"""
    return db.list_active_issues()


def get_issues_by_tag(db: GameDB, tag: str) -> List[Dict]:
    """按标签筛选进行中的事项。"""
    all_issues = db.list_active_issues()
    return [row for row in all_issues if tag in (json.loads(row.get("tags", "[]") or "[]"))]
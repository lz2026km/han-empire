"""Issue 系统：候选事件、issue 立项/推进/结案、tracker 输出落地。L5。

与 decree 诏书系统联动，天子通过诏书推动事项进展。
通过 bind_content() 注入 GameContent（取 EVENTS/SEED_EVENTS/EVENT_BY_ID）。
"""


import json
import re
import sqlite3
from typing import Any, Dict, List, Optional, Union

from han_sim.constants import TURN_UNIT
from han_sim.content import GameContent
from han_sim.db import GameDB
from han_sim.models import Event, GameState

_content: Optional[GameContent] = None



# ════════════════════════════════════════════════════════════════
# 1. 基础设施 (binding/上下文/应用)
# ════════════════════════════════════════════════════════════════
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



# ════════════════════════════════════════════════════════════════
# 2. issue 序列化 (payload/事件注入)
# ════════════════════════════════════════════════════════════════
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



# ════════════════════════════════════════════════════════════════
# 3. gate 解析 旧版 3 参数 (key, metrics, db)
# ════════════════════════════════════════════════════════════════
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



# ════════════════════════════════════════════════════════════════
# 4. 事件筛选 (gate 触发 → 候选事件)
# ════════════════════════════════════════════════════════════════
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



# ════════════════════════════════════════════════════════════════
# 5. UI 展示 (bar/格式化)
# ════════════════════════════════════════════════════════════════
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



# ════════════════════════════════════════════════════════════════
# 6. issue 转换 (event→issue)
# ════════════════════════════════════════════════════════════════
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



# ════════════════════════════════════════════════════════════════
# 7. tracker 输出 + inertia 旧版 (apply_issue_inertia_and_ongoing L598 老版)
# ════════════════════════════════════════════════════════════════
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
        bar = int(row["bar_value"])
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
                bar = int(row["bar_value"])

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



# ════════════════════════════════════════════════════════════════
# 8. active issue 查询 (get_active_issues/by_tag/by_kind/deadline)
# ════════════════════════════════════════════════════════════════
def get_active_issues(db: GameDB) -> List[Dict]:
    """返回所有进行中的事项列表。"""
    return db.list_active_issues()


def get_issues_by_tag(db: GameDB, tag: str) -> List[Dict]:
    """按标签筛选进行中的事项。"""
    all_issues = db.list_active_issues()
    return [row for row in all_issues if tag in (json.loads(row.get("tags", "[]") or "[]"))]


# v2.0.0 Phase 2.6: 阈值危机注入 + 事项级联（部分）已抽到 issues_crisis.py
from han_sim.issues_crisis import (  # noqa: F401
    _inject_crisis_by_metrics,
    _cascade_issue,
)
# ── 阈值危机注入 ────────────────────────────────────────────────────────────



# ════════════════════════════════════════════════════════════════
# 9. 危机注入 (threshold crisis)
# ════════════════════════════════════════════════════════════════
def _inject_threshold_crisis_events(
    candidate_events: List[Event],
    existing_candidates: List[Event],
    state: GameState,
    db: GameDB,
) -> None:
    """根据指标阈值自动注入危机事项到候选列表。

    - 藩镇 > 70 → "诸侯坐大"危机
    - 威权 < 10 → "天子形同虚设"危机
    - 声望 < 15 → "民心尽失"危机

    防重复：existing_candidates 中查重
    """
    fanzhen = state.metrics.get("藩镇", 0)
    authority = state.metrics.get("威权", 0)
    reputation = state.metrics.get("声望", 0)

    existing_titles = {ev.title for ev in existing_candidates}

    # 藩镇 > 70 → 诸侯坐大
    if fanzhen > 70 and "诸侯坐大" not in existing_titles:
        crisis_ev = Event(
            id="threshold_crisis_fanzhen",
            title="诸侯坐大",
            kind="危机",
            summary=f"藩镇值突破70（当前{fanzhen}），各地诸侯日益坐大，不奉朝命。",
            urgency=75,
            severity=75,
            credibility=100,
            interests=["藩镇", "朝廷"],
            audiences=["天子", "大臣"],
            trigger_year=0,
            trigger_month=0,
        )
        candidate_events.append(crisis_ev)

    # 威权 < 10 → 天子形同虚设
    if authority < 10 and "天子形同虚设" not in existing_titles:
        crisis_ev = Event(
            id="threshold_crisis_authority",
            title="天子形同虚设",
            kind="危机",
            summary=f"威权跌破10（当前{authority}），朝廷大事实由权臣决断，天子沦为傀儡。",
            urgency=90,
            severity=90,
            credibility=100,
            interests=["威权", "朝廷"],
            audiences=["天子", "权臣"],
            trigger_year=0,
            trigger_month=0,
        )
        candidate_events.append(crisis_ev)

    # 声望 < 15 → 民心尽失
    if reputation < 15 and "民心尽失" not in existing_titles:
        crisis_ev = Event(
            id="threshold_crisis_reputation",
            title="民心尽失",
            kind="危机",
            summary=f"声望跌破15（当前{reputation}），民间已不再信任汉室，天下思乱。",
            urgency=85,
            severity=85,
            credibility=100,
            interests=["声望", "民心"],
            audiences=["天子", "百姓"],
            trigger_year=0,
            trigger_month=0,
        )
        candidate_events.append(crisis_ev)


# ── trigger_gate 解析 ───────────────────────────────────────────────────────


_GATE_AGG_FUNCS = {
    "max": max,
    "min": min,
    "sum": sum,
    "avg": lambda xs: sum(xs) // max(1, len(xs)),
}



# ════════════════════════════════════════════════════════════════
# 10. gate 解析 新版 payload 字典 (gate, payload) - 与 §3 老版并存
# ════════════════════════════════════════════════════════════════
def _eval_gate_key(gate: Dict[str, str], payload: Dict[str, Any]) -> Optional[bool]:
    """解析 trigger_gate 条件。

    支持格式：
    - 'region.<id>.<field>' → regions 表字段
    - 'region.<id1>|<id2>|.<field>.<agg>' → 多省聚合
    - 'army.<id>.<field>' → armies 表
    - 'class.<id>.<field>' → classes 表
    - 'metrics.<metric>' → state.metrics

    Args:
        gate: 形如 {"region.幽州.稳定": ">=80", "metrics.藩镇": "<50"} 的字典
        payload: 包含 metrics/state/db 的上下文

    Returns:
        True if all conditions passed, False if any failed, None if evaluation error
    """
    metrics = payload.get("metrics", {})
    db = payload.get("db")

    for key, cond in gate.items():
        m = re.match(r"^(>=|<=|>|<|==)\s*(-?\d+)$", cond.strip())
        if not m:
            return None  # 格式错误
        op, num = m.group(1), int(m.group(2))

        # 解析 key
        val = _eval_gate_key_single(key, metrics, db)
        if val is None:
            return False  # key 不存在视为不通过

        passed = _compare_op(op, val, num)
        if not passed:
            return False

    return True



# ════════════════════════════════════════════════════════════════
# 10. gate 解析 新版 payload 字典 (gate, payload) - 与 §3 老版并存
# ════════════════════════════════════════════════════════════════
def _eval_gate_key_single(key: str, metrics: Dict[str, int], db: Optional[object]) -> Optional[int]:
    """解析单个 gate key 为 int 值。"""
    if "." not in key:
        # 直接是 metrics
        if key in metrics:
            return int(metrics[key])
        return None

    parts = key.split(".")
    table = parts[0]
    if table == "metrics" and len(parts) >= 2:
        return int(metrics.get(parts[1], 0))

    if table not in ("region", "army", "class", "building", "power"):
        return None

    # 末段可能是 agg
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

    if not ids or db is None:
        return None

    values: List[int] = []
    for cid in ids:
        try:
            row = db.conn.execute(f"SELECT {field} FROM {table}s WHERE id=?", (cid,)).fetchone()
        except Exception:
            row = None
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


def _compare_op(op: str, val: int, num: int) -> bool:
    """比较操作符。"""
    if op == ">=":
        return val >= num
    if op == "<=":
        return val <= num
    if op == ">":
        return val > num
    if op == "<":
        return val < num
    if op == "==":
        return val == num
    return False


# ── 终结效果计算 ────────────────────────────────────────────────────────────



# ════════════════════════════════════════════════════════════════
# 11. situation 应用 (apply_issue_inertia_and_ongoing L937 新版)
# ════════════════════════════════════════════════════════════════
def _situation_terminal_effects(issue_id: int, reason: str) -> Dict[str, Any]:
    """终结效果计算（resolved/failed）。

    Args:
        issue_id: 事项ID
        reason: "resolved" 或 "failed"

    Returns:
        effect dict，包含 metrics/economy/faction 等
    """
    effects: Dict[str, Any] = {}

    # 这里需要查 db 获取 issue 信息
    # 已在 apply_issue_tracker_output 中处理
    _ = issue_id
    _ = reason
    return effects


# ── 惯性漂移 + ongoing effects ──────────────────────────────────────────────


def apply_issue_inertia_and_ongoing(
    db: GameDB,
    state: GameState,
    touched_ids: Optional[set] = None,
) -> None:
    """每月末应用进行中 issue 的惯性漂移和 ongoing_effects。

    惯性漂移：每月 ±10 随机漂移（基于 inertia 字段）
    ongoing_effects 折扣：
      - bar >= 80: 30%
      - bar 40-80: 60%
      - bar < 40: 100%
    """
    _ = touched_ids  # 未使用
    active = db.list_active_issues()
    period_metric_acc: Dict[str, int] = {}

    for row in active:
        issue_id = int(row["id"])
        bar = int(row.get("bar_value", 0))
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
                # 重新读取最新 bar
                row = db.conn.execute("SELECT * FROM issues WHERE id=?", (issue_id,)).fetchone()
                if row is None:
                    continue
                bar = int(row["bar_value"])

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


# ═══════════════════════════════════════════════════════════════════════════
# 密令核议系统
# ═══════════════════════════════════════════════════════════════════════════


# ════════════════════════════════════════════════════════════════
# 12. secret order 密令 (含 deadline/状态/审查/日志)
# ════════════════════════════════════════════════════════════════
def check_secret_order_deadline(db: GameDB, turn: int) -> list:
    """检查期限届满的密令，自动转为 pending_review。
    
    查找所有 status='active' 且 due_turn <= turn 的密令，更新其状态为 'pending_review'。
    
    Args:
        db: GameDB 实例
        turn: 当前回合
        
    Returns:
        pending_order_ids: 被转为待核议状态的密令 ID 列表
    """
    pending = []
    orders = db.conn.execute(
        'SELECT * FROM secret_orders WHERE status=? AND due_turn<=? AND due_turn>0',
        ('active', turn)
    ).fetchall()
    for order in orders:
        db.conn.execute(
            'UPDATE secret_orders SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?',
            ('pending_review', order['id'])
        )
        pending.append(order['id'])
    if pending:
        db.conn.commit()
    return pending


def get_secret_orders_by_status(db: GameDB, status: str) -> list:
    """获取指定状态的密令列表。
    
    Args:
        db: GameDB 实例
        status: 密令状态，如 'active', 'pending_review', 'done', 'failed', 'exposed'
        
    Returns:
        符合条件的密令记录列表
    """
    return db.conn.execute(
        'SELECT * FROM secret_orders WHERE status=? ORDER BY importance DESC, turn_issued DESC',
        (status,)
    ).fetchall()


def apply_secret_order_review(
    db: GameDB,
    state: GameState,
    turn: int,
    year: int,
    period: int,
) -> dict:
    """月末密令核议 - 处理 pending_review 密令，执行五维判定。
    
    五维判定逻辑：
    1. 任务可行性（物理上是否可行）- 解析 content/tags 判断任务类型
    2. 承办人能力（ability/loyalty/integrity）- 查 characters 表
    3. 目标实力（被对付者的 leverage）- 查 factions/powers 表
    4. 暴露风险（sim_note 中的走漏线索）- 解析 sim_note 关键词
    5. 陈词真伪（承办人是否虚报）- 综合评估
    
    判定结果写入 result 字段，状态转为 done/failed/exposed。
    
    Args:
        db: GameDB 实例
        state: 当前游戏状态
        turn: 当前回合
        year: 当前年份
        period: 当前期
        
    Returns:
        {
            'done': [{order_id, title, narrative}, ...],   # 成功密令
            'failed': [{order_id, title, reason, narrative}, ...],  # 失败密令
            'exposed': [{order_id, title, narrative}, ...]  # 暴露密令
        }
    """
    results = {'done': [], 'failed': [], 'exposed': []}
    
    # 1. 查找所有 pending_review 密令
    pending_orders = get_secret_orders_by_status(db, 'pending_review')
    if not pending_orders:
        return results
    
    for order in pending_orders:
        order_id = order['id']
        minister_name = order['minister_name']
        title = order['title']
        content = order['content']
        tags = json.loads(order['tags'] or '[]')
        importance = int(order['importance'])
        sim_note = order['sim_note']
        
        # 五维判定变量
        feasibility_score = 50   # 任务可行性 0-100
        capability_score = 50    # 承办人能力 0-100
        target_score = 50         # 目标实力 0-100 (越低越容易被对付)
        exposure_score = 0        # 暴露风险 0-100 (越高越容易暴露)
        truth_score = 50          # 陈词真伪 0-100 (越高越可信)
        
        # ── 维度1：任务可行性 ──────────────────────────────────────────
        # 基于任务类型和标签判断物理可行性
        tags_lower = [t.lower() for t in tags]
        
        # 刺杀类任务需要特殊条件
        if '刺杀' in tags or '暗杀' in tags:
            if '武力' in tags or '军事' in tags:
                feasibility_score = 30  # 刺杀难度高
            else:
                feasibility_score = 20
        # 监视/刺探类
        elif '监视' in tags or '刺探' in tags:
            feasibility_score = 70
        # 离间/策反类
        elif '离间' in tags or '策反' in tags:
            feasibility_score = 50
        # 暗杀/行刺类
        elif '行刺' in tags or '暗杀' in tags:
            feasibility_score = 25
        # 传递情报类
        elif '传递' in tags or '送信' in tags:
            feasibility_score = 80
        # 政治手腕类（默认）
        else:
            feasibility_score = 60
        
        # 重要性影响：越重要的任务难度可能更高
        if importance <= 2:
            feasibility_score -= 10  # 极高重要性任务更难
        elif importance >= 5:
            feasibility_score += 10  # 低重要性任务较易
        
        # ── 维度2：承办人能力 ──────────────────────────────────────────
        minister_row = db.conn.execute(
            'SELECT ability, loyalty, integrity FROM characters WHERE name=?',
            (minister_name,)
        ).fetchone()
        
        if minister_row:
            ability = int(minister_row['ability'])
            loyalty = int(minister_row['loyalty'])
            integrity = int(minister_row['integrity'])
            # 能力综合分 = 能力值*0.4 + 忠诚度*0.3 + 正值*0.3
            capability_score = ability * 0.4 + loyalty * 0.3 + integrity * 0.3
            # 忠诚度影响完成任务意愿
            if loyalty < 30:
                capability_score *= 0.5  # 低忠诚大幅降低
            elif loyalty < 50:
                capability_score *= 0.8
        else:
            capability_score = 30  # 未找到承办人，默认低分
        
        # ── 维度3：目标实力 ────────────────────────────────────────────
        # 从 content 中解析目标（简化版：查找势力名称）
        target_leverage = 50  # 默认中等实力
        # 尝试从 sim_note 中获取目标信息
        if sim_note:
            # 查找是否有目标势力相关信息
            powers = db.conn.execute('SELECT id, name, leverage FROM powers').fetchall()
            for power in powers:
                if power['name'] in content or power['name'] in sim_note:
                    target_leverage = int(power['leverage'])
                    break
            # 查找派系
            if target_leverage == 50:
                factions = db.conn.execute('SELECT name, leverage FROM factions').fetchall()
                for faction in factions:
                    if faction['name'] in content or faction['name'] in sim_note:
                        target_leverage = int(faction['leverage'])
                        break
        # 目标实力越低（leverage小），越容易被对付
        target_score = 100 - target_leverage
        
        # ── 维度4：暴露风险 ───────────────────────────────────────────
        # 解析 sim_note 中的走漏线索
        exposure_keywords = [
            '泄露', '暴露', '走漏', '被告发', '被察觉',
            '有人知道', '风声', '传开', '传出去',
            '被发现', '目击', '有人看见', '泄露',
            '暴露风险', '高风险', '警惕', '怀疑',
        ]
        for keyword in exposure_keywords:
            if keyword in sim_note:
                exposure_score += 15
        # 重要性高的任务暴露后果更严重
        if importance <= 2:
            exposure_score += 20
        elif importance >= 5:
            exposure_score -= 10
        exposure_score = min(100, max(0, exposure_score))
        
        # ── 维度5：陈词真伪 ───────────────────────────────────────────
        # 基于承办人能力和忠诚度判断其报告的真实性
        truth_score = capability_score  # 简单复用能力分
        # 检查 sim_note 中是否有虚报嫌疑
        false_report_keywords = ['虚报', '夸大', '隐瞒', '伪造', '欺骗']
        for keyword in false_report_keywords:
            if keyword in sim_note:
                truth_score -= 30
        truth_score = min(100, max(0, truth_score))
        
        # ── 综合判定 ──────────────────────────────────────────────────
        # 成功概率 = 可行性 * 0.3 + 承办人能力 * 0.3 + 目标实力 * 0.2 + 真伪 * 0.2
        success_prob = (
            feasibility_score * 0.3 +
            capability_score * 0.3 +
            target_score * 0.2 +
            truth_score * 0.2
        )
        
        # 暴露风险单独判定
        exposed = exposure_score > 60
        
        # 生成判定叙事
        narrative_parts = [
            f"【五维判定】",
            f"可行性:{feasibility_score:.0f} | 承办能力:{capability_score:.0f}",
            f"目标难度:{target_score:.0f} | 暴露风险:{exposure_score:.0f}",
            f"陈词真伪:{truth_score:.0f}",
            f"综合成功率:{success_prob:.1f}%"
        ]
        
        if exposed:
            # 暴露情况
            new_status = 'exposed'
            narrative_parts.append("【结果】密令暴露！任务失败，承办人可能被追查。")
            narrative = "；".join(narrative_parts)
            results['exposed'].append({
                'order_id': order_id,
                'title': title,
                'narrative': narrative,
                'feasibility': feasibility_score,
                'capability': capability_score,
                'target': target_score,
                'exposure': exposure_score,
                'truth': truth_score,
            })
        elif success_prob >= 60:
            # 成功
            new_status = 'done'
            narrative_parts.append("【结果】密令执行成功！")
            narrative = "；".join(narrative_parts)
            results['done'].append({
                'order_id': order_id,
                'title': title,
                'narrative': narrative,
                'success_prob': success_prob,
            })
        else:
            # 失败
            new_status = 'failed'
            narrative_parts.append("【结果】密令执行失败。")
            narrative = "；".join(narrative_parts)
            results['failed'].append({
                'order_id': order_id,
                'title': title,
                'narrative': narrative,
                'success_prob': success_prob,
                'reason': '综合判定失败',
            })
        
        # 更新密令状态和结果
        db.conn.execute(
            '''UPDATE secret_orders 
               SET status=?, result=?, turn_closed=?, updated_at=CURRENT_TIMESTAMP
               WHERE id=?''',
            (new_status, narrative, turn, order_id)
        )
    
    if pending_orders:
        db.conn.commit()
    
    return results


def append_secret_order_sim_note(
    db: GameDB,
    order_id: int,
    note: str,
    turn: int,
) -> None:
    """为密令追加推演副作用记录到 sim_note 字段。
    
    Args:
        db: GameDB 实例
        order_id: 密令 ID
        note: 要追加的副作用描述
        turn: 当前回合
    """
    if not note:
        return
    
    # 获取当前 sim_note
    row = db.conn.execute(
        'SELECT sim_note FROM secret_orders WHERE id=?',
        (order_id,)
    ).fetchone()
    
    if row is None:
        return
    
    current_note = row['sim_note'] or ''
    # 追加新记录，带回合标记
    if current_note:
        new_note = current_note + f"\n[T{turn}] {note}"
    else:
        new_note = f"[T{turn}] {note}"
    
    db.conn.execute(
        'UPDATE secret_orders SET sim_note=?, updated_at=CURRENT_TIMESTAMP WHERE id=?',
        (new_note, order_id)
    )
    db.conn.commit()
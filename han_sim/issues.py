"""事件聚合：历史锚定触发 + 阈值危机生成 + 随机事件候选。L5。

每月末推演前，由 simulation 调用，收集所有"本月应该出现"的事件，
分为三类：
  1. 历史锚定事件  — 严格按 trigger_year / trigger_month 触发
  2. 阈值危机事件  — metrics 或实体字段达到条件时触发
  3. 随机事件候选  — urgency 高且尚未触发的事件，按概率抽取
"""



import re
from typing import Any, Dict, List, Optional, Tuple

from han_sim.db import GameDB
from han_sim.models import GameState


# ── 条件求值 ────────────────────────────────────────────────────────────────

def _eval_gate(value: int, op: str, threshold: int) -> bool:
    """判断数值条件是否满足。"""
    if op == ">":
        return value > threshold
    if op == ">=":
        return value >= threshold
    if op == "<":
        return value < threshold
    if op == "<=":
        return value <= threshold
    if op == "==":
        return value == threshold
    if op == "!=":
        return value != threshold
    return False


def _get_value(db: GameDB, key_path: str) -> Optional[Any]:
    """从 db/state 中按路径取元数据值。

    key_path 格式：
      metrics.威权        → state.metrics["威权"]
      powers.dongzhuo.status → db.get_power("dongzhuo")["status"]
      regions.capital.unrest → db.list_regions() 中找 id=capital 的 unrest
      characters.caocao.power_id → db.get_character("cao-cao")["power_id"]
    """
    parts = key_path.split(".")
    if parts[0] == "metrics":
        _, metric_key = parts
        return None  # caller passes state separately
    if parts[0] == "powers":
        _, power_id, field = parts
        row = db.conn.execute(
            "SELECT * FROM powers WHERE id=?", (power_id,)
        ).fetchone()
        return dict(row)[field] if row else None
    if parts[0] == "regions":
        _, region_id, field = parts
        row = db.conn.execute(
            "SELECT * FROM regions WHERE id=?", (region_id,)
        ).fetchone()
        return dict(row)[field] if row else None
    if parts[0] == "characters":
        _, char_id, field = parts
        row = db.conn.execute(
            "SELECT * FROM characters WHERE id=? OR name=?", (char_id, char_id)
        ).fetchone()
        return dict(row)[field] if row else None
    return None


def _check_trigger_gate(
    trigger_gate: Dict[str, str],
    state: GameState,
    db: GameDB,
) -> bool:
    """检查 trigger_gate 所有条件是否满足。"""
    if not trigger_gate:
        return True
    for key_path, cond in trigger_gate.items():
        m = re.match(r"(.*?)\s*(>=|<=|==|!=|>|<)\s*(\d+)", cond.strip())
        if not m:
            continue
        op = m.group(2)
        threshold = int(m.group(3))

        if key_path.startswith("metrics."):
            metric_key = key_path.split(".", 1)[1]
            value = state.metrics.get(metric_key, 0)
        else:
            value = _get_value(db, key_path)
            if value is None:
                return False

        if not _eval_gate(value, op, threshold):
            return False
    return True


def _check_trigger_condition(
    trigger_condition: Dict[str, str],
    state: GameState,
    db: GameDB,
) -> bool:
    """检查 trigger_condition（等号条件），要求完全相等。"""
    if not trigger_condition:
        return True
    for key_path, expected in trigger_condition.items():
        if key_path.startswith("metrics."):
            continue  # metrics 在 trigger_gate 中处理
        actual = _get_value(db, key_path)
        if actual is None:
            return False
        if str(actual) != str(expected):
            return False
    return True


def _in_time_window(event: Dict, year: int, month: int) -> bool:
    """检查事件是否在时间窗口内。"""
    ty = event.get("trigger_year", 0)
    tm = event.get("trigger_month", 0)
    if ty and tm:
        # 历史锚定：精确到年月
        if year > ty or (year == ty and month < tm):
            return False
        tey = event.get("trigger_end_year", 0)
        tem = event.get("trigger_end_month", 0)
        if tey and tem:
            if year > tey or (year == tey and month > tem):
                return False
        return True
    # 无时间锚定：年内任意月均可能
    if not ty:
        return True
    return year >= ty


# ── 事件过滤 ────────────────────────────────────────────────────────────────

def filter_triggered_events(
    state: GameState,
    db: GameDB,
    triggered_ids: Optional[List[str]] = None,
) -> Tuple[List[Dict], List[Dict]]:
    """收集本月所有可触发事件。

    Returns:
        historical: 历史锚定事件（一定触发）
        threshold_crisis: 阈值危机事件（条件满足则触发）
    """
    triggered_ids = triggered_ids or []
    all_events = db.list_events()
    year = state.year
    month = state.period

    historical = []
    threshold_crisis = []

    for e in all_events:
        if e["id"] in triggered_ids:
            continue
        if not _in_time_window(e, year, month):
            continue

        kind = e.get("kind", "")
        if kind == "historical":
            # 历史事件：时间窗口内即触发
            if _check_trigger_gate(e.get("trigger_gate", {}), state, db):
                historical.append(e)
        elif kind == "threshold_crisis":
            if _check_trigger_gate(e.get("trigger_gate", {}), state, db):
                if _check_trigger_condition(e.get("trigger_condition", {}), state, db):
                    threshold_crisis.append(e)
        # random / emperor_action 由 simulation 单独处理

    return historical, threshold_crisis


def sample_random_events(
    state: GameState,
    db: GameDB,
    already_triggered: List[str],
    max_count: int = 2,
) -> List[Dict]:
    """从随机事件候选池中按 urgency 概率抽样。"""
    all_events = db.list_events()
    candidates = []
    for e in all_events:
        if e["id"] in already_triggered:
            continue
        if e.get("kind") not in ("random", "emperor_action"):
            continue
        if not _in_time_window(e, state.year, state.period):
            continue
        urgency = e.get("urgency", 0)
        # 基准概率 10%，urgency 每点 +1%，最高 70%
        prob = min(0.70, 0.10 + urgency / 100 * 0.60)
        import random as _random
        if _random.random() < prob:
            candidates.append(e)

    # 按 urgency 降序，取最多 max_count 个
    candidates.sort(key=lambda x: x.get("urgency", 0), reverse=True)
    return candidates[:max_count]


# ── 事件效果应用 ─────────────────────────────────────────────────────────────

def apply_event_effect(e: Dict, state: GameState, db: GameDB) -> List[str]:
    """对事件效果字段进行结算，返回操作摘要列表。"""
    effects: List[str] = []
    summary = e.get("summary", "")

    # 硬编码核心历史事件效果（未来可扩展为 trigger_effects JSON 字段）
    eid = e["id"]

    if eid == "dongzhuo_enter":
        state.metrics["威权"] = max(0, state.metrics.get("威权", 0) - 60)
        state.metrics["声望"] = max(0, state.metrics.get("声望", 0) - 40)
        effects.append("威权 -60（董卓进京，天子威严尽失）")
        effects.append("声望 -40（天下失望）")

    elif eid == "luoyang_burned":
        state.metrics["汉室库"] = max(0, state.metrics.get("汉室库", 0) - 80)
        state.metrics["声望"] = max(0, state.metrics.get("声望", 0) - 50)
        state.metrics["威权"] = max(0, state.metrics.get("威权", 0) - 30)
        effects.append("汉室库 -80（洛阳遭焚，皇室资财尽毁）")
        effects.append("声望 -50")
        effects.append("威权 -30")

    elif eid == "lvbu_zhuofu":
        state.metrics["威权"] = min(100, state.metrics.get("威权", 0) + 20)
        state.metrics["声望"] = min(100, state.metrics.get("声望", 0) + 15)
        effects.append("威权 +20（董卓伏诛，人心大快）")
        effects.append("声望 +15")

    elif eid == "lijue_guoha":
        state.metrics["威权"] = max(0, state.metrics.get("威权", 0) - 40)
        state.metrics["声望"] = max(0, state.metrics.get("声望", 0) - 30)
        effects.append("威权 -40（李傕郭汜之乱）")
        effects.append("声望 -30")

    elif eid == "guangwu_restored":
        state.metrics["声望"] = min(100, state.metrics.get("声望", 0) + 25)
        state.metrics["威权"] = min(100, state.metrics.get("威权", 0) + 10)
        effects.append("声望 +25（献帝东归，人心稍安）")
        effects.append("威权 +10")

    # 阈值危机：generic 效果（根据 severity 扣除 metrics）
    elif e.get("kind") == "threshold_crisis":
        severity = e.get("severity", 50)
        delta = -round(severity / 10)
        state.metrics["威权"] = max(0, state.metrics.get("威权", 0) + delta)
        state.metrics["声望"] = max(0, state.metrics.get("声望", 0) + delta)
        effects.append(f"危机「{e['title']}」触发，威权{delta}，声望{delta}")

    # 记录日志
    log_entry = f"事件触发「{e['title']}」：{summary}"
    db.append_log(state.turn, "simulation", log_entry)
    return effects
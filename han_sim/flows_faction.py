# -*- mode: python ; coding: utf-8 -*-
"""
汉献帝之末路 - 派系系统流（v2.0.0 Phase 2.4 拆自 flows.py）

职责：派系影响力计算、派系-诏书修正、派系事件、派系日志。
参考源：flows.py:22-225（180 行）
"""
from __future__ import annotations

from typing import Dict, List

from han_sim.models import GameState
from han_sim.db import GameDB


FACTION_THRESHOLDS: Dict[str, Dict[str, int]] = {
    "忠汉派": {"dominant": 70, "rising": 50, "declining": 20},
    "务实派": {"dominant": 65, "rising": 45, "declining": 15},
    "离心派": {"dominant": 60, "rising": 40, "declining": 25},
    "叛逆派": {"dominant": 55, "rising": 35, "declining": 15},
}

FACTION_DECREE_MODIFIERS: Dict[str, Dict[str, float]] = {
    "忠汉派": {"诏书": 0.15, "军事": 0.10, "财政": 0.05},
    "务实派": {"诏书": 0.05, "军事": 0.10, "财政": 0.15},
    "离心派": {"诏书": -0.10, "军事": -0.05, "财政": 0.05},
    "叛逆派": {"诏书": -0.15, "军事": -0.10, "财政": -0.10},
}

FACTION_METRIC_SENSITIVITY: Dict[str, Dict[str, float]] = {
    "忠汉派": {"威权": 0.4, "声望": 0.2, "藩镇": -0.3},
    "务实派": {"威权": 0.1, "声望": 0.3, "藩镇": 0.1},
    "离心派": {"威权": -0.3, "声望": -0.2, "藩镇": 0.4},
    "叛逆派": {"威权": -0.4, "声望": -0.2, "藩镇": 0.5},
}


def calc_faction_influence(state: GameState, db: GameDB) -> Dict[str, float]:
    """计算四大派系影响力。v2.0.0 Phase 2.4: 抽自 flows.py:46"""
    characters = db.list_characters(status="active")

    loyal_count = sum(1 for c in characters if c.get("loyalty", 0) >= 70)
    waiting_count = sum(1 for c in characters if 40 <= c.get("loyalty", 0) < 70)
    离心_count = sum(1 for c in characters if 10 <= c.get("loyalty", 0) < 40)
    叛逆_count = sum(1 for c in characters if c.get("loyalty", 0) < 10)

    authority = state.metrics.get("威权", 0)
    reputation = state.metrics.get("声望", 0)
    fanzhen = state.metrics.get("藩镇", 0)

    base_influences = {
        "忠汉派": loyal_count * 10,
        "务实派": waiting_count * 8,
        "离心派": (离心_count + 叛逆_count) * 15,
        "叛逆派": 叛逆_count * 20,
    }

    influences = {
        "忠汉派": base_influences["忠汉派"]
                  + authority * FACTION_METRIC_SENSITIVITY["忠汉派"]["威权"]
                  + reputation * FACTION_METRIC_SENSITIVITY["忠汉派"]["声望"]
                  + fanzhen * FACTION_METRIC_SENSITIVITY["忠汉派"]["藩镇"],
        "务实派": base_influences["务实派"]
                  + authority * FACTION_METRIC_SENSITIVITY["务实派"]["威权"]
                  + reputation * FACTION_METRIC_SENSITIVITY["务实派"]["声望"]
                  + fanzhen * FACTION_METRIC_SENSITIVITY["务实派"]["藩镇"],
        "离心派": base_influences["离心派"]
                  + authority * FACTION_METRIC_SENSITIVITY["离心派"]["威权"]
                  + reputation * FACTION_METRIC_SENSITIVITY["离心派"]["声望"]
                  + fanzhen * FACTION_METRIC_SENSITIVITY["离心派"]["藩镇"],
        "叛逆派": base_influences["叛逆派"]
                  + authority * FACTION_METRIC_SENSITIVITY["叛逆派"]["威权"]
                  + reputation * FACTION_METRIC_SENSITIVITY["叛逆派"]["声望"]
                  + fanzhen * FACTION_METRIC_SENSITIVITY["叛逆派"]["藩镇"],
    }

    return {k: max(0, v) for k, v in influences.items()}


def apply_faction_events(state: GameState, db: GameDB) -> List[Dict]:
    """检测派系主导事件。v2.0.0 Phase 2.4: 抽自 flows.py:97"""
    influences = calc_faction_influence(state, db)
    prev_influences = state.metrics.get("_prev_faction_influence", {})
    events: List[Dict] = []

    for faction, threshold in FACTION_THRESHOLDS.items():
        inf = influences.get(faction, 0)
        prev = prev_influences.get(faction, 0)

        if inf >= threshold["dominant"]:
            effect_map = {
                "忠汉派": {"威权": +2, "声望": +5},
                "务实派": {"声望": +3, "藩镇": -1},
                "离心派": {"威权": -2, "藩镇": +3},
                "叛逆派": {"威权": -5, "藩镇": +10},
            }
            effects = effect_map.get(faction, {})
            for metric, delta in effects.items():
                if metric == "威权":
                    state.metrics["威权"] = max(0, min(100, state.metrics.get("威权", 0) + delta))
                elif metric == "声望":
                    state.metrics["声望"] = max(0, min(100, state.metrics.get("声望", 0) + delta))
                elif metric == "藩镇":
                    state.metrics["藩镇"] = max(0, min(100, state.metrics.get("藩镇", 0) + delta))
            events.append({
                "faction": faction,
                "title": f"{faction}主导",
                "type": "dominant",
                "effects": effects,
            })
            state.log.append(f"【派系事件】{faction}主导朝政，{'/'.join([f'{k}{v:+d}' for k,v in effects.items()])}")

        elif inf >= threshold["rising"] and prev < threshold["rising"]:
            rise_effects = {
                "忠汉派": {"威权": +1},
                "务实派": {"声望": +2},
                "离心派": {"藩镇": +1},
                "叛逆派": {"藩镇": +2},
            }
            effects = rise_effects.get(faction, {})
            for metric, delta in effects.items():
                if metric == "威权":
                    state.metrics["威权"] = max(0, min(100, state.metrics.get("威权", 0) + delta))
                elif metric == "声望":
                    state.metrics["声望"] = max(0, min(100, state.metrics.get("声望", 0) + delta))
                elif metric == "藩镇":
                    state.metrics["藩镇"] = max(0, min(100, state.metrics.get("藩镇", 0) + delta))
            events.append({
                "faction": faction,
                "title": f"{faction}崛起",
                "type": "rising",
                "effects": effects,
            })
            state.log.append(f"【派系动态】{faction}势力崛起，{'/'.join([f'{k}{v:+d}' for k,v in effects.items()])}")

        elif inf <= threshold["declining"] and prev > threshold["declining"] and prev > 0:
            events.append({
                "faction": faction,
                "title": f"{faction}失势",
                "type": "declining",
                "effects": {},
            })
            state.log.append(f"【派系动态】{faction}声势渐弱")

    state.metrics["_prev_faction_influence"] = influences.copy()
    return events


def get_faction_decree_modifier(faction: str, decree_type: str) -> float:
    """获取特定派系对特定类型诏书的效果修正。v2.0.0 Phase 2.4: 抽自 flows.py:180"""
    faction_mods = FACTION_DECREE_MODIFIERS.get(faction, {})
    return faction_mods.get(decree_type, 0.0)


def calc_decree_faction_modifier(state: GameState, decree_type: str = "诏书") -> float:
    """计算针对特定诏书类型的派系综合修正。v2.0.0 Phase 2.4: 抽自 flows.py:186"""
    faction_data = state.metrics.get("faction_influence", {})
    total_mod = 0.0
    for faction, mod_values in FACTION_DECREE_MODIFIERS.items():
        inf = faction_data.get(faction, 20)
        base_mod = mod_values.get(decree_type, 0.0)
        intensity = max(0, (inf - 30) / 70)
        total_mod += base_mod * intensity
    return max(-0.3, min(0.3, total_mod))


def log_faction_influence_change(
    state: GameState,
    db: GameDB,
    action_type: str,
    details: Dict[str, int],
) -> None:
    """记录派系影响力变化的详细日志。v2.0.0 Phase 2.4: 抽自 flows.py:205"""
    influences = calc_faction_influence(state, db)
    prev = state.metrics.get("_prev_faction_influence", {})

    log_parts = [f"【派系变动】{action_type}："]
    for faction, inf in influences.items():
        prev_val = prev.get(faction, inf)
        delta = inf - prev_val
        if delta != 0:
            log_parts.append(f"{faction}{delta:+d}({prev_val:.0f}→{inf:.0f})")

    if len(log_parts) > 1:
        state.log.append("".join(log_parts))

    state.metrics["_prev_faction_influence"] = influences.copy()

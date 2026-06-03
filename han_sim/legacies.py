"""v5.1.0 P0-4: Opening Legacies 开幕负担

仿 ming_sim/models.py:200-211 OpeningLegacy + ming_sim/legacies.py:88 check_clear_gates
本模块:
  1. apply_legacy_modifiers(state, db): 把活跃 legacy 的 modifier 注入 state.metrics
  2. 修饰 modifier: 简单 metric 增减 + 复杂 modifier (decay_authority, faction_decay 等)
  3. legacy_summary(db): UI 弹窗用
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from han_sim.db import GameDB
from han_sim.models import GameState


# modifier 字段含义映射 (供 UI 展示)
MODIFIER_LABELS = {
    "威权": "威权减值",
    "声望": "民心减值",
    "藩镇": "藩镇增值",
    "decay_authority": "威权衰减加速",
    "faction_decay": "派系忠诚度衰减加速",
    "military_pressure_total": "边防压力增值",
}


def apply_legacy_modifiers(state: GameState, db: GameDB) -> Dict[str, int]:
    """v5.1.0 P0-4: 把所有 active legacy 的 modifier 注入 state.

    返回: 实际应用的 modifier dict (供日志记录)
    """
    applied: Dict[str, int] = {}
    try:
        legacies = db.list_active_legacies(turn=state.turn)
    except Exception:
        return applied

    for leg in legacies:
        modifiers = leg.get("modifiers", {})
        if isinstance(modifiers, str):
            try:
                modifiers = json.loads(modifiers)
            except Exception:
                continue
        if not isinstance(modifiers, dict):
            continue

        for key, delta in modifiers.items():
            try:
                delta_int = int(delta)
            except (TypeError, ValueError):
                continue

            # 0 跳过
            if delta_int == 0:
                continue

            # 直接 metric 增减
            if key in state.metrics and isinstance(state.metrics[key], (int, float)):
                state.metrics[key] = state.metrics[key] + delta_int
                # 累加 modifier 应用计数 (同 key 累加)
                applied[key] = applied.get(key, 0) + delta_int
            # 特殊 modifier (decay_authority / faction_decay / military_pressure_total):
            # 不直接动 metrics, 而是通过 state.legacy_modifiers 段暴露给 flows
            elif key in ("decay_authority", "faction_decay", "military_pressure_total"):
                if not hasattr(state, "legacy_modifiers") or state.legacy_modifiers is None:
                    state.legacy_modifiers = {}
                state.legacy_modifiers[key] = state.legacy_modifiers.get(key, 0) + delta_int
                applied[key] = applied.get(key, 0) + delta_int

    if applied:
        state.clamp()
    return applied


def get_legacy_modifier(state: GameState, modifier_key: str, default: float = 0.0) -> float:
    """读 legacy 累加 modifier (供 flows.py 用)."""
    if not hasattr(state, "legacy_modifiers") or not state.legacy_modifiers:
        return default
    return float(state.legacy_modifiers.get(modifier_key, default))


def format_legacy_for_display(legacy: Dict) -> Dict[str, Any]:
    """v5.1.0 P0-4: 把 legacy 字典格式化为 UI 卡片数据."""
    modifiers = legacy.get("modifiers", {})
    if isinstance(modifiers, str):
        try:
            modifiers = json.loads(modifiers)
        except Exception:
            modifiers = {}
    return {
        "id": legacy.get("id"),
        "key": legacy.get("legacy_key", ""),
        "name": legacy.get("name", ""),
        "narrative_hint": legacy.get("narrative_hint", ""),
        "modifiers": [
            {"key": k, "delta": int(v), "label": MODIFIER_LABELS.get(k, k)}
            for k, v in modifiers.items() if isinstance(v, (int, float))
        ],
        "duration_months": legacy.get("duration_months", 0),
        "status": legacy.get("status", ""),
        "clear_gate": legacy.get("clear_gate", {}),
    }


def get_active_legacy_summary(db: GameDB) -> List[Dict[str, Any]]:
    """v5.1.0 P0-4: 返所有 active legacy 的 UI 摘要."""
    rows = db.list_active_legacies(turn=0)  # turn=0 不限
    return [format_legacy_for_display(r) for r in rows]

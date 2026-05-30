"""季节/年度财政流与数值/经济/派系 delta 应用。L6。"""



import json
from typing import Dict, List, Optional, Tuple

from han_sim.constants import TURN_UNIT
from han_sim.db import GameDB
from han_sim.models import GameState, monthly_amount


def _province_efficiency(fiscal: dict, gentry_resistance: int, unrest: int) -> float:
    corruption = fiscal.get("corruption", 50)
    rate = (1.0
            - gentry_resistance / 100 * 0.55
            - corruption / 100 * 0.45
            - max(0, unrest - 20) / 100 * 0.30)
    return max(0.05, min(1.00, rate))


def calc_province_fiscal(
    state: GameState,
    db: GameDB,
) -> Tuple[int, int, List[Dict]]:
    """按省计算月度财政收入。
    返回 (总税收, 总支出, 各省摘要列表)
    """
    regions = db.list_regions()
    total_tax = 0
    total_expense = 0
    summaries = []

    for reg in regions:
        fiscal = reg.get("fiscal", {})
        tax_base = reg.get("tax_per_turn", 0)
        unrest = reg.get("unrest", 0)
        gentry = reg.get("gentry_resistance", 0)
        efficiency = _province_efficiency(fiscal, gentry, unrest)
        actual_tax = int(tax_base * efficiency)
        total_tax += actual_tax
        summaries.append({
            "region": reg["name"],
            "tax_base": tax_base,
            "efficiency": round(efficiency, 2),
            "actual": actual_tax,
        })

    # 军队维护费
    armies = db.list_armies()
    for army in armies:
        if army.get("status") == "active":
            total_expense += army.get("maintenance_per_turn", 0)

    return total_tax, total_expense, summaries


def apply_monthly_flow(state: GameState, db: GameDB) -> Dict:
    """月度结算：税收 - 支出，记录日志。"""
    tax, expense, provinces = calc_province_fiscal(state, db)
    net = tax - expense
    state.metrics["汉室库"] = state.metrics.get("汉室库", 0) + net
    state.clamp()

    log_entry = f"本月：税收{tax}万两，支出{expense}万两，{'盈余' if net >= 0 else '亏损'}{abs(net)}万两"
    state.log.append(log_entry)
    return {
        "tax": tax,
        "expense": expense,
        "net": net,
        "treasury": state.metrics.get("汉室库", 0),
        "provinces": provinces,
    }


def calc_faction_delta(state: GameState, db: GameDB) -> List[Dict]:
    """计算派系变化：藩镇割据程度年度变化。"""
    powers = db.list_powers()
    deltas = []
    for p in powers:
        # 藩镇越大，汉室威权越低
        if p.get("kind") == "warlord":
            strength = p.get("military_strength", 0)
            delta = round(strength / 50)
            deltas.append({"power": p["name"], "威权冲击": -delta})
            state.metrics["威权"] = max(0, state.metrics.get("威权", 0) - delta)
    return deltas
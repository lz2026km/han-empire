"""季节/年度财政流与数值/经济/派系 delta 应用。L6。"""



import json
import random
from typing import Dict, List, Optional, Tuple

from han_sim.constants import TURN_UNIT
from han_sim.db import GameDB
from han_sim.models import GameState, monthly_amount


def loyalty_multiplier(loyalty: int) -> float:
    """忠诚度修正系数，决定诏书/召对效果折扣。"""
    if loyalty >= 70: return 1.0
    if loyalty >= 40: return 0.8
    if loyalty >= 10: return 0.5
    return 0.2


def get_minister_loyalty_context(db: GameDB, name: str) -> str:
    """返回大臣忠诚度描述词，供召对 prompt 使用。"""
    row = db.conn.execute("SELECT loyalty FROM characters WHERE name=?", (name,)).fetchone()
    if not row:
        return "忠诚度未知。"
    loyalty = int(row["loyalty"])
    if loyalty >= 70:
        return f"忠诚度{loyalty}（忠诚可靠，愿为陛下效死）。"
    if loyalty >= 40:
        return f"忠诚度{loyalty}（持观望之心，行事保留）。"
    if loyalty >= 10:
        return f"忠诚度{loyalty}（离心离德，阳奉阴违）。"
    return f"忠诚度{loyalty}（心怀异志，必欲取而代之）。"


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


def apply_warlord_actions(state: GameState, db: GameDB) -> List[Dict]:
    """每回合各路诸侯自动行动：写入 powers.last_action，推进藩镇值。
    参照 ming_sim/db.apply_power_deltas() + power_payload()。
    """
    changes: List[Dict] = []
    # 含汉室自身，取除汉室外所有势力
    powers = db.list_powers()
    faction_leverage_delta = 0  # 所有势力的 leverage 变化汇总

    for p in powers:
        pid = p.get("id", "")
        if pid == "han":
            continue
        stance = p.get("stance", "neutral")
        mil = int(p.get("military_strength", 0))
        leverage = int(p.get("leverage", 0))
        last_action = p.get("last_action", "")

        delta_leverage = 0
        delta_mil = 0
        narrative = last_action or "按兵不动"

        if stance == "hostile":
            delta_leverage = min(8, mil // 15)
            delta_mil = min(5, mil // 20)
            narratives = [
                "整军经武，窥伺中原", "遣使联络诸侯，图谋共伐",
                "扩充军队，实力渐涨", "割据自守，不奉朝命",
                "虎视眈眈，伺机而动",
            ]
            narrative = random.choice(narratives)
        elif stance == "neutral":
            if random.random() < 0.35:
                delta_leverage = random.choice([-1, 0, 1])
                narratives = ["观望待变", "遣使入朝探听虚实", "整饬内政"]
                narrative = random.choice(narratives)
        elif stance == "loyal":
            if state.metrics.get("威权", 0) < 20:
                narrative = "人心渐离，忠诚难恃"

        new_lev = max(0, min(100, leverage + delta_leverage))
        new_mil = max(0, min(100, mil + delta_mil))
        faction_leverage_delta += new_lev - leverage

        if delta_leverage or delta_mil:
            db.conn.execute(
                "UPDATE powers SET leverage=?, military_strength=?, last_action=? WHERE id=?",
                (new_lev, new_mil, narrative[:80], pid))
            changes.append({"id": pid, "last_action": narrative, "leverage": new_lev})

    if changes:
        db.conn.commit()

    # 藩镇值 = 所有敌对/中立势力 leverage 总和，映射到 0-100
    hostile_total = sum(
        int(p["leverage"]) for p in powers
        if p["id"] != "han" and p["stance"] in ("hostile", "neutral"))
    new_fanzhen = min(100, max(0, hostile_total // 10 + 20))
    old_fanzhen = state.metrics.get("藩镇", 80)
    if new_fanzhen != old_fanzhen:
        state.metrics["藩镇"] = new_fanzhen
        state.log.append(f"【藩镇动态】天下诸侯动作频繁，藩镇值：{old_fanzhen} → {new_fanzhen}")

    return changes


def calc_faction_delta(state: GameState, db: GameDB) -> List[Dict]:
    """计算派系变化：藩镇根据威权/诏书/事件动态消长。"""
    powers = db.list_powers()
    deltas = []

    for p in powers:
        if p.get("kind") == "warlord":
            strength = p.get("military_strength", 0)
            delta = round(strength / 50)
            deltas.append({"power": p["name"], "威权冲击": -delta})
            state.metrics["威权"] = max(0, state.metrics.get("威权", 0) - delta)

    # 威权反作用于藩镇：威权高则藩镇削弱
    authority = state.metrics.get("威权", 0)
    if authority >= 70:
        state.metrics["藩镇"] = max(0, state.metrics.get("藩镇", 0) - 2)
    elif authority <= 10:
        state.metrics["藩镇"] = min(100, state.metrics.get("藩镇", 0) + 1)

    return deltas


# ── 期4 新增机制 ──────────────────────────────────────────────────────────

def apply_loyalty_decay(state: GameState, db: GameDB) -> List[Dict]:
    """每月忠诚度衰减：威权低则加速衰减，权臣麾下角色衰减更快。"""
    characters = db.list_characters()
    decays = []
    authority = state.metrics.get("威权", 0)
    # 威权越低，基础衰减越大
    base_decay = max(0, (30 - authority) // 10)  # 威权30时base_decay=0，威权0时base_decay=3

    for char in characters:
        if char.get("status") != "active":
            continue
        lid = char["id"]
        power_id = char.get("power_id", "")
        loyalty = char.get("loyalty", 50)

        # 权臣麾下：跟随其主公的势力状态
        decay = base_decay
        if power_id in ("dongzhuo", "caocao", "lvbu"):
            decay += 1  # 权臣麾下衰减更快

        new_loyalty = max(0, loyalty - decay)
        char["loyalty"] = new_loyalty
        db.upsert_character(char)
        decays.append({"character": char["name"], "from": loyalty, "to": new_loyalty, "decay": decay})

    return decays


# 迁都效果表
_CAPITAL_EFFECTS = {
    "洛阳": {"声望": 0, "威权": 0, "藩镇": 0},
    "长安": {"声望": -5, "威权": -3, "藩镇": -5},   # 西迁避难，人心涣散
    "许昌": {"声望": +2, "威权": +5, "藩镇": +3},   # 曹操控制下，形式统一
    "邺城": {"声望": -3, "威权": -5, "藩镇": -8},   # 袁绍地盘，藩镇不服
    "南阳": {"声望": -2, "威权": -2, "藩镇": -3},
}


def relocate_capital(state: GameState, new_capital: str) -> Dict[str, int]:
    """迁都：返回指标变化量。调用前需验证合法性。"""
    old = state.capital
    if old == new_capital:
        return {}
    effects = _CAPITAL_EFFECTS.get(new_capital, {})
    delta = {}
    for key, val in effects.items():
        state.metrics[key] = state.metrics.get(key, 50) + val
        delta[key] = val
    state.capital = new_capital
    state.log.append(f"【迁都】汉室迁都：{old} → {new_capital}，威权{'+' if delta.get('威权',0)>=0 else ''}{delta.get('威权',0)}")
    return delta


def check_dongzhuo_trap(state: GameState) -> bool:
    """董卓伏诛线检测。
    若 dong_zhuo_trapped_turn > 0 且距被困已满6回合仍未诛董卓 → 游戏失败。
    若 dong_zhuo_killed_turn > 0 → 伏诛成功。
    返回 True 表示触发游戏失败。
    """
    if state.dong_zhuo_killed_turn > 0:
        return False  # 已伏诛，正常继续
    if state.dong_zhuo_trapped_turn > 0:
        trapped_turns = state.turn - state.dong_zhuo_trapped_turn
        if trapped_turns >= 6:
            # 游戏失败：董卓未被诛，天子彻底沦为傀儡
            state.log.append("【游戏失败】董卓围攻未解，汉室名存实亡……")
            return True
    return False


def check_emperor_escape(state: GameState) -> str:
    """献帝东归线检测。
    若 emperor_escaped_turn > 0 且 emperor_safe_turn = 0：
      - 5回合内到达许昌 → 设置 emperor_safe_turn，返回 'success'
      - 超过5回合未到达 → 东归失败，返回 'failed'
    若 emperor_safe_turn > 0 → 东归已完成
    返回状态: 'ongoing' | 'success' | 'failed' | 'none'
    """
    if state.emperor_safe_turn > 0:
        return "success"
    if state.emperor_escaped_turn == 0:
        return "none"

    escape_turns = state.turn - state.emperor_escaped_turn
    if escape_turns >= 5:
        if state.emperor_safe_turn == 0:
            state.log.append("【东归失败】献帝未能抵达许昌，被李傕郭汜追回。")
            return "failed"
    return "ongoing"


def detect_tragic_events(state: GameState) -> List[Dict]:
    """检测威权崩溃导致的悲剧性事件（每回合最多触发一个）。"""
    events = []
    authority = state.metrics.get("威权", 0)

    if authority <= 5 and state.turn % 3 == 0:
        events.append({
            "title": "天子形同虚设",
            "kind": "threshold_crisis",
            "summary": "威权降至5以下，朝廷大事皆由权臣决断，天子沦为摆设。",
            "effects": {"威权": -2, "声望": -3}
        })
    if state.metrics.get("声望", 0) <= 5 and state.turn % 2 == 0:
        events.append({
            "title": "民心尽失",
            "kind": "threshold_crisis",
            "summary": "汉室民心崩溃，百姓不再以汉室为正朔。",
            "effects": {"声望": -5, "藩镇": +5}
        })
    return events
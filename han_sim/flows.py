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


# ── 派系影响力计算 ────────────────────────────────────────────────────────

def calc_faction_influence(state: GameState, db: GameDB) -> Dict[str, float]:
    """计算四大派系影响力。

    - 忠汉派：忠诚大臣数量×10 + 威权×0.3
    - 务实派：观望大臣数量×8 + 声望×0.2
    - 离心派：离心/叛逆大臣数量×15 + 藩镇×0.5
    - 叛逆派：叛逆大臣数量×20 + (藩镇>60? +30 : 0)

    返回 {派系名: 影响力值}
    """
    characters = db.list_characters(status="active")

    # 忠诚度分段统计
    loyal_count = sum(1 for c in characters if c.get("loyalty", 0) >= 70)
    waiting_count = sum(1 for c in characters if 40 <= c.get("loyalty", 0) < 70)
    离心_count = sum(1 for c in characters if 10 <= c.get("loyalty", 0) < 40)
    叛逆_count = sum(1 for c in characters if c.get("loyalty", 0) < 10)

    authority = state.metrics.get("威权", 0)
    reputation = state.metrics.get("声望", 0)
    fanzhen = state.metrics.get("藩镇", 0)

    influences = {
        "忠汉派": loyal_count * 10 + authority * 0.3,
        "务实派": waiting_count * 8 + reputation * 0.2,
        "离心派": (离心_count + 叛逆_count) * 15 + fanzhen * 0.5,
        "叛逆派": 叛逆_count * 20 + (30 if fanzhen > 60 else 0),
    }
    return influences


def apply_faction_events(state: GameState, db: GameDB) -> List[Dict]:
    """检测派系主导事件（影响力>70），触发相应效果。

    - 忠汉派主导 → 威权+2/声望+5
    - 叛逆派主导 → 威权-5/藩镇+10
    返回触发的事件列表。
    """
    influences = calc_faction_influence(state, db)
    events: List[Dict] = []

    if influences.get("忠汉派", 0) > 70:
        state.metrics["威权"] = state.metrics.get("威权", 0) + 2
        state.metrics["声望"] = state.metrics.get("声望", 0) + 5
        events.append({
            "faction": "忠汉派",
            "title": "忠汉派主导",
            "effects": {"威权": +2, "声望": +5},
        })

    if influences.get("叛逆派", 0) > 70:
        state.metrics["威权"] = max(0, state.metrics.get("威权", 0) - 5)
        state.metrics["藩镇"] = state.metrics.get("藩镇", 0) + 10
        events.append({
            "faction": "叛逆派",
            "title": "叛逆派主导",
            "effects": {"威权": -5, "藩镇": +10},
        })

    return events


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


def _governor_ability_modifier(db: GameDB, region_id: str) -> float:
    """太守能力修正：查找地区太守的能力值，映射为 0.5~1.5 修正系数。"""
    chars = db.list_characters(status="active")
    for c in chars:
        office = c.get("office", "")
        office_type = c.get("office_type", "")
        # 太守职衔一般包含"太守"字样，或 office_type 为"太守"
        if "太守" in office or office_type == "太守":
            loc = c.get("location", "")
            # 匹配太守驻地
            if region_id in loc or loc in region_id:
                ability = c.get("ability", 50)
                return 0.5 + (ability / 100) * 1.0  # 能力50→0.5，能力150→1.5
    return 1.0  # 无太守信息，返回无修正


# 兖/豫/荆 基础田赋收入（万两/回合）
_PROVINCE_TAX_BASE = {
    "yanzhou": 12,
    "yuzhou": 10,
    "jingzhou": 14,
}


def calc_province_fiscal(
    state: GameState,
    db: GameDB,
) -> Tuple[int, int, List[Dict]]:
    """按省计算月度财政收入（分级结构化版本）。
    返回 (总税收, 总支出, 各省摘要列表)
    各省税收 = 基础田赋收入 ×太守能力修正 × 效率系数
    """
    regions = db.list_regions()
    total_tax = 0
    total_expense = 0
    summaries = []

    for reg in regions:
        reg_id = reg.get("id", "")
        fiscal = reg.get("fiscal", {})
        unrest = reg.get("unrest", 0)
        gentry = reg.get("gentry_resistance", 0)
        efficiency = _province_efficiency(fiscal, gentry, unrest)
        ability_mod = _governor_ability_modifier(db, reg_id)

        # 基础田赋收入（仅兖/豫/荆 计田赋）
        tax_base = _PROVINCE_TAX_BASE.get(reg_id, reg.get("tax_per_turn", 0))
        actual_tax = int(tax_base * ability_mod * efficiency)
        total_tax += actual_tax
        summaries.append({
            "region": reg["name"],
            "region_id": reg_id,
            "tax_base": tax_base,
            "ability_mod": round(ability_mod, 2),
            "efficiency": round(efficiency, 2),
            "actual": actual_tax,
        })

    # 军队维护费
    armies = db.list_armies()
    for army in armies:
        if army.get("status") == "active":
            total_expense += army.get("maintenance_per_turn", 0)

    return total_tax, total_expense, summaries


# ── 分级财政流 ────────────────────────────────────────────────────────────────

def apply_graduated_fiscal(state: GameState, db: GameDB) -> Dict:
    """计算并应用分级财政：
    - 田赋收入：按州（兖/豫/荆）基础收入×太守能力修正
    - 盐铁专营：威权≥30时内库+10，否则被截留
    - 暗探开支：威权≥40时每回合汉室库-5（解锁情报加成）
    返回财政明细 dict。
    """
    authority = state.metrics.get("威权", 0)
    tax, expense, provinces = calc_province_fiscal(state, db)

    # 盐铁专营
    salt_iron = 10 if authority >= 30 else 0
    intercepted = 0 if authority >= 30 else 10
    state.metrics["内库"] = state.metrics.get("内库", 0) + salt_iron

    # 暗探开支
    intel_expense = 5 if authority >= 40 else 0
    if intel_expense > 0:
        state.metrics["汉室库"] = state.metrics.get("汉室库", 0) - intel_expense

    net = tax + salt_iron - expense - intel_expense
    state.metrics["汉室库"] = state.metrics.get("汉室库", 0) + (tax - expense - intel_expense)
    state.clamp()

    return {
        "田赋": tax,
        "盐铁专营": salt_iron,
        "盐铁截留": intercepted,
        "暗探开支": intel_expense,
        "总支出": expense,
        "净收": net,
        "provinces": provinces,
    }


def collect_tribute(state: GameState, db: GameDB) -> List[Dict]:
    """威权≥50时，忠诚诸侯自动缴纳贡金：leverage×0.5
    返回缴纳诸侯列表。
    """
    authority = state.metrics.get("威权", 0)
    if authority < 50:
        return []

    tributes: List[Dict] = []
    powers = db.list_powers()
    for p in powers:
        if p.get("id") == "han" or p.get("kind") == "faction":
            continue
        if p.get("stance") == "loyal":
            leverage = int(p.get("leverage", 0))
            amount = leverage // 2
            if amount > 0:
                state.metrics["汉室库"] = state.metrics.get("汉室库", 0) + amount
                tributes.append({
                    "power": p.get("name", p.get("id", "")),
                    "leverage": leverage,
                    "tribute": amount,
                })
    return tributes


def apply_intel_expense(state: GameState, db: GameDB) -> Dict:
    """威权≥40时每回合暗探开支汉室库-5，解锁情报加成。
    返回本回合暗探情报状态。
    """
    authority = state.metrics.get("威权", 0)
    intel_active = authority >= 40
    cost = 5 if intel_active else 0
    if cost > 0:
        state.metrics["汉室库"] = state.metrics.get("汉室库", 0) - cost
        state.clamp()
    return {
        "active": intel_active,
        "cost": cost,
        "intel_bonus": "情报加成已解锁" if intel_active else "情报未解锁",
    }


def apply_building_maintenance(state: GameState, db: GameDB) -> Dict:
    """每月维护费扣除 + 建筑效果结算。
    - 未央宫（长安）：威权+3/年
    - 洛阳武库：军事效果+15%
    - 许昌行宫：都城威权衰减-50%
    - 各州粮仓：税收+10%
    """
    buildings = db.list_buildings()
    total_maintenance = 0
    effects: Dict[str, Dict[str, int]] = {}
    authority_decay_modifier = 1.0  # 许昌行宫效果

    for b in buildings:
        if b.get("status") != "正常":
            continue
        maintenance = b.get("maintenance", 0)
        total_maintenance += maintenance

        metric = b.get("output_metric", "")
        amount = b.get("output_amount", 0)
        category = b.get("category", "")

        # 维护费扣除（从内库支付）
        if maintenance > 0:
            state.metrics["内库"] = state.metrics.get("内库", 0) - maintenance

        # 建筑效果结算
        if metric and amount:
            if metric == "威权":
                state.metrics["威权"] = state.metrics.get("威权", 0) + amount
            elif metric == "汉室库":
                state.metrics["汉室库"] = state.metrics.get("汉室库", 0) + amount
            elif metric == "声望":
                state.metrics["声望"] = state.metrics.get("声望", 0) + amount
            elif metric == "军备":
                # 军事调度效果通过 effect_pct 记录
                pass
            effects[b.get("name", b["id"])] = {metric: amount}

        # 许昌行宫：都城威权衰减-50%
        if category == "内廷" and b.get("output_metric") == "威权" and b.get("level", 0) >= 3:
            authority_decay_modifier = 0.5

        # 各州粮仓：税收+10%
        if category == "财政" and "粮仓" in b.get("name", ""):
            # 在 calc_province_fiscal 里通过效率系数体现，这里记录
            effects[b.get("name", b["id"])] = {"税收": 10}

    state.clamp()
    return {
        "total_maintenance": total_maintenance,
        "effects": effects,
        "authority_decay_modifier": authority_decay_modifier,
        "net": -total_maintenance,
    }


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


# ── 威权机制（Step2）─────────────────────────────────────────────

# ── 威权恢复行动（Step2新增）────────────────────────────────────

AUTHORITY_RECOVERY_ACTIONS: Dict[str, Dict] = {
    "求情示弱": {"effects": {"威权": +3, "声望": -2}, "cost": 5, "description": "向权臣示弱，以求保全"},
    "笼络近臣": {"effects": {"威权": +2, "内库": -5}, "cost": 5, "description": "赏赐近臣，收买人心"},
    "施恩示好": {"effects": {"威权": +4, "内库": -10}, "cost": 10, "description": "对大臣施恩，培养忠诚"},
    "朝会演讲": {"effects": {"威权": +5, "声望": +3}, "cost": 0, "description": "在朝会上演讲，提振天子威权"},
    "处理政务": {"effects": {"威权": +3, "声望": +1}, "cost": 0, "description": "亲力亲为处理政务，展现勤政姿态"},
    "颁布诏书": {"effects": {"威权": +2, "藩镇": -1}, "cost": 5, "description": "正常颁布诏书，维护天子权威"},
    "召见贤才": {"effects": {"威权": +4, "声望": +2}, "cost": 10, "description": "召见民间贤才，提振朝野信心"},
    "整饬吏治": {"effects": {"威权": +5, "声望": +3, "藩镇": -2}, "cost": 15, "description": "整饬吏治，打击贪腐"},
    "祭天祈福": {"effects": {"威权": +6, "声望": +4}, "cost": 20, "description": "祭天祈福，宣称天命所归"},
    "军事演练": {"effects": {"威权": +4, "藩镇": -3}, "cost": 20, "description": "举行军事演练，展示武力"},
    "册封功臣": {"effects": {"威权": +5, "内库": -15}, "cost": 15, "description": "册封有功之臣，激励忠义"},
    "颁布罪己诏": {"effects": {"威权": -3, "声望": +8, "藩镇": -2}, "cost": 0, "description": "颁布罪己诏，挽回民心"},
    "大赦天下": {"effects": {"威权": +3, "声望": +6, "藩镇": -1}, "cost": 10, "description": "大赦天下，收揽人心"},
}


def execute_authority_recovery(state: GameState, action: str) -> Dict[str, int]:
    """执行威权恢复行动。返回指标变化 dict。"""
    from han_sim.models import get_authority_level

    action_info = AUTHORITY_RECOVERY_ACTIONS.get(action)
    if not action_info:
        return {}

    authority = state.metrics.get("威权", 0)
    auth_level = get_authority_level(authority)

    # 检查行动是否在当前威权等级的可用行动列表中
    if action not in auth_level.recovery_actions:
        state.log.append(f"【威权不足】当前威权等级「{auth_level.label}」无法执行「{action}」")
        return {}

    # 检查内库是否足够
    cost = action_info.get("cost", 0)
    if cost > 0 and state.metrics.get("内库", 0) < cost:
        state.log.append(f"【内库不足】执行「{action}」需要{cost}万两，当前内库{state.metrics.get('内库',0)}万两")
        return {}

    # 扣除内库
    if cost > 0:
        state.metrics["内库"] -= cost

    # 应用效果
    delta = {}
    for metric, change in action_info.get("effects", {}).items():
        old_val = state.metrics.get(metric, 0)
        new_val = old_val + change
        # 约束范围
        if metric in ("汉室库", "内库"):
            new_val = max(0, new_val)
        else:
            new_val = max(0, min(100, new_val))
        state.metrics[metric] = new_val
        delta[metric] = new_val - old_val

    state.log.append(f"【威权恢复】执行「{action}」，{'，'.join([f'{k}{v:+d}' for k,v in delta.items()])}")
    return delta


# ── 忠诚度恢复行动（Step5新增）──────────────────────────────────────

LOYALTY_RECOVERY_ACTIONS: Dict[str, Dict] = {
    "施恩": {"effects": {"忠诚度": +5}, "cost": 10, "description": "对大臣施恩，提升忠诚"},
    "嘉奖": {"effects": {"忠诚度": +8}, "cost": 15, "description": "嘉奖功臣，提升忠诚"},
    "笼络": {"effects": {"忠诚度": +6}, "cost": 8, "description": "笼络人心，提升忠诚"},
    "赦免": {"effects": {"忠诚度": +10, "声望": +2}, "cost": 5, "description": "赦免过失，提升忠诚"},
    "晋升": {"effects": {"忠诚度": +12}, "cost": 20, "description": "晋升官职，提升忠诚"},
}


def apply_loyalty_recovery(state: GameState, char_id: str, action: str) -> int:
    """对指定角色执行忠诚度恢复行动。返回忠诚度变化量。"""
    action_info = LOYALTY_RECOVERY_ACTIONS.get(action)
    if not action_info:
        return 0
    char = state.db.conn.execute(
        "SELECT * FROM characters WHERE id=?", (char_id,)
    ).fetchone()
    if not char:
        return 0
    cost = action_info.get("cost", 0)
    if cost > 0 and state.metrics.get("内库", 0) < cost:
        state.log.append(f"【内库不足】{action}需要{cost}万两")
        return 0
    if cost > 0:
        state.metrics["内库"] -= cost
    old_loyal = char["loyalty"]
    new_loyal = min(100, old_loyal + action_info["effects"].get("忠诚度", 0))
    new_loyal = max(0, new_loyal)
    state.db.upsert_character(dict(char, loyalty=new_loyal))
    state.log.append(f"【忠诚度恢复】{char['name']} {action}，忠诚度{old_loyal}→{new_loyal}")
    return new_loyal - old_loyal


def check_betrayal_events(state: GameState, db: GameDB) -> List[Dict]:
    """检测叛逃事件：
    - 忠诚度<30且威权<20的大臣，有概率叛逃
    - 藩镇>=80且威权<15的势力，有概率脱离
    返回触发的事件列表（每回合最多1个）。
    """
    events = []
    authority = state.metrics.get("威权", 0)
    fanzhen = state.metrics.get("藩镇", 0)

    # 检查大臣叛逃
    if authority < 20:
        for char in db.list_characters(status="active"):
            if char.get("loyalty", 50) < 30 and char.get("power_id") not in ("", None):
                # 威权低+忠诚度低+有势力归属 → 3%概率叛逃
                import random
                if random.random() < 0.03:
                    char["loyalty"] = max(0, char["loyalty"] - 10)
                    db.upsert_character(char)
                    events.append({
                        "title": f"{char['name']}叛逃",
                        "kind": "threshold_crisis",
                        "summary": f"{char['name']}见天子威权扫地，改投{char.get('power_id','权臣')}。",
                        "effects": {"威权": -2, "声望": -1}
                    })
                    state.log.append(f"【叛逃】{char['name']}见威权尽失，叛逃而去！")
                    break  # 每回合最多1个

    # 检查藩镇脱离（威权<15且藩镇>=80）
    if authority < 15 and fanzhen >= 80:
        import random
        if random.random() < 0.05:
            old_fz = state.metrics.get("藩镇", 0)
            state.metrics["藩镇"] = min(100, old_fz + 5)
            state.log.append("【藩镇脱离】藩镇见天子威权扫地，纷纷脱离！")
            events.append({
                "title": "藩镇脱离",
                "kind": "threshold_crisis",
                "summary": "威权扫地，藩镇纷纷脱离汉室控制。",
                "effects": {"藩镇": +5, "声望": -3}
            })

    return events


# ── 诸侯忠诚度衰减（Step5新增）────────────────────────────────────────

def apply_warlord_loyalty_decay(state: GameState, db: GameDB) -> List[Dict]:
    """诸侯忠诚度每月衰减：
    - 威权>=80：稳定，忠诚度几乎不衰减
    - 威权50-79：标准衰减（-2到-3）
    - 威权20-49：加速衰减（-4到-6）
    - 威权<20：最快衰减（-6到-10）
    衰减受 warlord_stability 修正（威权越高修正越大）。
    """
    from han_sim.models import get_authority_level

    authority = state.metrics.get("威权", 0)
    auth_level = get_authority_level(authority)
    stability = auth_level.warlord_stability

    powers = db.list_powers()
    decays = []
    for p in powers:
        if p.get("id") in ("han", ""):
            continue
        lid = p.get("id", "")
        loyalty = p.get("loyalty", 50)
        stance = p.get("stance", "neutral")

        # 敌对势力衰减更快
        decay_base = {"loyal": 1, "neutral": 2, "hostile": 3}.get(stance, 2)
        # 威权修正：stability 0-1，越高衰减越慢
        decay = int(decay_base * (1 - stability * 0.5))

        new_loyalty = max(0, min(100, loyalty - decay))
        p["loyalty"] = new_loyalty
        db.upsert_power(p)
        if decay > 0:
            decays.append({"power": p.get("name", lid), "from": loyalty, "to": new_loyalty, "decay": decay})

    return decays


def apply_authority_effects(state: GameState, db: GameDB) -> Dict[str, int]:
    """威权机制核心：每回合根据威权等级影响各项游戏数值。

    影响范围：
    1. 诸侯稳定性：威权高则诸侯不易叛，忠诚度衰减减半
    2. 派系事件强度：威权低则派系事件更频繁
    3. 诏书执行折扣：威权低则诏书效果打折
    4. 声望恢复：威权高则每回合声望自然+1
    5. 藩镇抑制：威权>=50时每回合藩镇-1

    返回本回合威权相关指标变化 dict。
    """
    from han_sim.models import get_authority_level

    authority = state.metrics.get("威权", 0)
    level = get_authority_level(authority)
    changes: Dict[str, int] = {}

    # 1. 威权>=50时，藩镇自然-1（抑制效果）
    if authority >= 50:
        old = state.metrics.get("藩镇", 0)
        state.metrics["藩镇"] = max(0, old - 1)
        changes["藩镇"] = state.metrics["藩镇"] - old

    # 2. 威权>=60时，声望自然+1（天子有底气则民心稳）
    if authority >= 60:
        old_rep = state.metrics.get("声望", 0)
        state.metrics["声望"] = min(100, old_rep + 1)
        changes["声望"] = state.metrics["声望"] - old_rep

    # 3. 威权<=10时，藩镇+2（天子形同虚设则诸侯坐大）
    if authority <= 10:
        old_fz = state.metrics.get("藩镇", 0)
        state.metrics["藩镇"] = min(100, old_fz + 2)
        changes["藩镇"] = state.metrics["藩镇"] - old_fz
        state.log.append("【威权危机】天子形同虚设，诸侯日益坐大！")

    # 4. 记录威权等级变化（威权跨越等级时触发提示）
    if state.turn > 1:
        prev_auth = state.metrics.get("_prev_authority", authority)
        prev_level = get_authority_level(prev_auth)
        if prev_level.label != level.label:
            state.log.append(f"【威权变化】从「{prev_level.label}」（{prev_auth}）变为「{level.label}」（{authority}）")
    state.metrics["_prev_authority"] = authority

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
    """每月忠诚度衰减：威权低则加速衰减，威权高则衰减减半（威权机制）。

    衰减规则：
    - 威权>=80：忠诚度几乎不衰减（warlord_stability=0.9，基础衰减极低）
    - 威权50-79：标准衰减
    - 威权20-49：衰减加速
    - 威权<20：衰减最快，权臣麾下角色衰减最严重

    威权对忠诚度衰减的影响通过 base_decay 的幂函数实现。
    """
    characters = db.list_characters()
    decays = []
    authority = state.metrics.get("威权", 0)

    # 威权驱动的基础衰减率（0-30区间，越高衰减越慢）
    # 威权0 → decay_base=3（最大衰减）
    # 威权30 → decay_base=0（无衰减）
    # 威权>30 → 额外惩罚，威权100时衰减最轻
    if authority >= 80:
        # 威权高时，忠诚度稳定，几乎不衰减
        base_decay = max(0, (30 - authority) // 10)  # 80→0, 90→0, 100→0
    elif authority >= 50:
        base_decay = max(0, (30 - authority) // 8)   # 50→0, 60→0, 70→0
    else:
        # 威权低时，衰减加速
        base_decay = max(1, (40 - authority) // 10)  # 40→0, 30→1, 20→2, 10→3, 0→4

    for char in characters:
        if char.get("status") != "active":
            continue
        lid = char["id"]
        power_id = char.get("power_id", "")
        loyalty = char.get("loyalty", 50)

        # 权臣麾下角色衰减更快
        decay = base_decay
        if power_id in ("dongzhuo", "caocao", "lvbu"):
            decay += 1

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


# ── 董卓伏诛系统（Step6新增）────────────────────────────────────────

DONGZHUO_BASE_MILITARY = 40   # 董卓基础军力（伏诛所需最低值）


def trigger_dongzhuo_trap(state: GameState) -> None:
    """触发董卓伏诛线：设置 trapped_turn，标志围困开始。"""
    if state.dong_zhuo_trapped_turn > 0:
        return  # 已触发，不再重复
    state.dong_zhuo_trapped_turn = state.turn
    state.log.append("【董卓伏诛线触发】董卓被围，诸侯攻守之势已成！")


def execute_dongzhuo_elimination(state: GameState, military_strength: int) -> Dict:
    """执行董卓伏诛判定：
    - 成功条件：军力 >= 董卓基础军力 + 威权修正
    - 威权修正：威权越高，所需军力越低（威权>=60时-10）
    返回结果 dict：{success, narrative, effects}
    """
    authority = state.metrics.get("威权", 0)
    required = DONGZHUO_BASE_MILITARY
    if authority >= 60:
        required -= 10  # 威权高则降低难度
    elif authority >= 40:
        required -= 5

    # 军力不足则失败
    success = military_strength >= required
    if success:
        state.dong_zhuo_killed_turn = state.turn
        state.dong_zhuo_trapped_turn = 0
        effects = {
            "威权": 30,
            "声望": 20,
            "藩镇": -15,
            "汉室库": 50,  # 抄没董卓家产
        }
        narrative = f"董卓伏诛！诸侯联军攻入长安，董卓死于乱军之中。汉室重光，威权大增！"
        state.log.append("【董卓伏诛】董卓已死，汉室重光！")
    else:
        effects = {
            "威权": -10,
            "声望": -5,
        }
        narrative = f"联军攻打长安未克（需军力{required}，实际{military_strength}），董卓依然坐镇，局势更加危急。"
        state.log.append(f"【董卓伏诛失败】联军未克，军力不足（需{required}，实际{military_strength}）")

    # 应用效果
    for k, v in effects.items():
        state.metrics[k] = max(0, min(100, state.metrics.get(k, 50) + v))

    return {
        "success": success,
        "narrative": narrative,
        "effects": effects,
        "required": required,
        "actual": military_strength,
    }


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


# ── 天子技能点系统 ────────────────────────────────────────────────────────

def apply_skill_points(state: GameState, db: GameDB) -> int:
    """根据威权发放天子技能点。威权≥40每回合+1，威权≥60每回合+2，上限10点。
    返回本回合新增的技能点数。
    """
    authority = state.metrics.get("威权", 0)
    if authority >= 60:
        gained = 2
    elif authority >= 40:
        gained = 1
    else:
        gained = 0

    if gained > 0:
        current = state.metrics.get("skill_points", 0)
        new_pts = min(10, current + gained)
        state.metrics["skill_points"] = new_pts
        state.log.append(f"【技能点】威权{authority}，本回合获得{gained}点（当前共{new_pts}点）")
    return gained


def execute_emperor_skill(
    state: GameState,
    db: GameDB,
    skill_id: str,
) -> Dict[str, object]:
    """执行已学习的天子技能效果。
    查找 skills.py 中的技能定义，执行其 effect，更新 metrics。
    返回执行结果描述。
    """
    from han_sim.skills import skill_display_name

    # 技能效果定义：skill_id → (指标变化dict, 描述)
    _SKILL_EFFECTS: Dict[str, tuple[Dict[str, int], str]] = {
        # 经略系
        "jinglve_1": ({"威权": +2}, "知己知彼：了解自身实力，威权+2"),
        "jinglve_2": ({"藩镇": -3}, "远交近攻：联合远敌，藩镇-3"),
        "jinglve_3": ({"威权": +3, "声望": +1}, "以夷制夷：分化外族，威权+3声望+1"),
        "jinglve_4": ({"藩镇": -5}, "先南后北：先平内乱，藩镇-5"),
        "jinglve_5": ({"威权": +5, "藩镇": -3}, "联袁抗董：联合袁绍讨董，威权+5藩镇-3"),
        "jinglve_6": ({"威权": +2, "声望": +2}, "以退为进：战略后撤保存实力，威权+2声望+2"),
        "jinglve_7": ({"藩镇": -5, "威权": +3}, "各个击破：逐一消灭，藩镇-5威权+3"),
        "jinglve_8": ({"威权": +3, "藩镇": -2}, "堡垒推进：稳扎稳打，威权+3藩镇-2"),
        "jinglve_9": ({"藩镇": -4, "威权": +2}, "诱敌深入：围歼敌军，藩镇-4威权+2"),
        "jinglve_10": ({"威权": +8, "藩镇": -5}, "天下围攻：号令诸侯共讨，藩镇-5威权+8"),
        "jinglve_11": ({"藩镇": -6, "汉室库": +20}, "经济绞杀：断敌补给，藩镇-6库+20"),
        "jinglve_12": ({"威权": +10, "声望": +5, "藩镇": -8}, "天命所归：天下归心，威权+10声望+5藩镇-8"),
        # 权谋系
        "zhengzhi_1": ({"威权": +2, "声望": +1}, "笼络人心：施恩收买，威权+2声望+1"),
        "zhengzhi_2": ({"威权": +2}, "分化制衡：派系相互牵制，威权+2"),
        "zhengzhi_3": ({"威权": +3, "声望": -1}, "清除异己：罢黜不臣，威权+3声望-1"),
        "zhengzhi_4": ({"威权": +3, "声望": +2}, "启用新人：破格提拔，威权+3声望+2"),
        "zhengzhi_5": ({"威权": +4, "声望": +3}, "整饬吏治：惩治贪腐，威权+4声望+3"),
        "zhengzhi_6": ({"汉室库": +30, "威权": +2}, "改革税制：清查隐田，威权+2库+30"),
        "zhengzhi_7": ({"威权": +8, "藩镇": -3}, "衣带密诏：串联忠臣诛贼，威权+8藩镇-3"),
        "zhengzhi_8": ({"威权": +5, "声望": +3}, "平衡朝局：三族制约，威权+5声望+3"),
        "zhengzhi_9": ({"威权": +4, "声望": +4}, "垂拱而治：无为而治，威权+4声望+4"),
        "zhengzhi_10": ({"威权": +6}, "乾纲独断：大权独揽，威权+6"),
        "zhengzhi_11": ({"声望": +5, "藩镇": +2}, "大赦天下：收拢民心，威望+5藩镇+2"),
        "zhengzhi_12": ({"威权": +10, "声望": +8, "藩镇": -8}, "万邦来朝：四方宾服，威权+10声望+8藩镇-8"),
        # 武功系
        "junlu_1": ({"威权": +3, "声望": +2}, "阅兵示威：展示军威，威权+3声望+2"),
        "junlu_2": ({"威权": +2, "声望": +1}, "粮草先行：保障补给，威权+2声望+1"),
        "junlu_3": ({"汉室库": +10, "威权": +1}, "精兵简政：裁撤老弱，库+10威权+1"),
        "junlu_4": ({"威权": +4, "声望": +2}, "甲兵精强：改良装备，威权+4声望+2"),
        "junlu_5": ({"威权": +3, "藩镇": -2}, "练兵自强：加强军训，藩镇-2威权+3"),
        "junlu_6": ({"威权": +3, "声望": +3, "汉室库": -10}, "重赏厚恤：激励士气，库-10威权+3声望+3"),
        "junlu_7": ({"威权": +2, "藩镇": -2}, "坚城要塞：修筑防御，威权+2藩镇-2"),
        "junlu_8": ({"威权": +6, "藩镇": -4}, "铁骑突袭：建立骑兵，威权+6藩镇-4"),
        "junlu_9": ({"威权": +4, "藩镇": -3}, "水师建设：发展水军，威权+4藩镇-3"),
        "junlu_10": ({"威权": +6, "声望": +4}, "军功爵位：以功授爵，威权+6声望+4"),
        "junlu_11": ({"汉室库": +20, "藩镇": -4}, "以战养战：取敌为己，库+20藩镇-4"),
        "junlu_12": ({"威权": +10, "声望": +6, "藩镇": -8}, "铁骑纵横：天下无敌，威权+10声望+6藩镇-8"),
        # 文治系
        "wenzhi_1": ({"威权": +2, "声望": +2}, "以史为鉴：汲取经验，威权+2声望+2"),
        "wenzhi_2": ({"威权": +3, "声望": +3}, "求贤若渴：招揽贤才，威权+3声望+3"),
        "wenzhi_3": ({"威权": +2, "声望": +3}, "兴学重教：发展教育，威权+2声望+3"),
        "wenzhi_4": ({"威权": +3, "声望": +2}, "举孝廉：选拔人才，威权+3声望+2"),
        "wenzhi_5": ({"威权": +3, "汉室库": +10}, "科技兴国：改进技术，威权+3库+10"),
        "wenzhi_6": ({"威权": +2, "声望": +4}, "广开言路：鼓励进谏，威权+2声望+4"),
        "wenzhi_7": ({"威权": +4, "声望": +4}, "修史立典：编纂典籍，威权+4声望+4"),
        "wenzhi_8": ({"威权": +3, "声望": +3}, "天文历法：改进历法，威权+3声望+3"),
        "wenzhi_9": ({"威权": +3, "声望": +3, "藩镇": -1}, "医学防疫：防治瘟疫，威权+3声望+3藩镇-1"),
        "wenzhi_10": ({"威权": +5, "声望": +5}, "印刷推广：普及知识，威权+5声望+5"),
        "wenzhi_11": ({"威权": +4, "汉室库": +20, "声望": +3}, "丝路通商：打通商路，威权+4库+20声望+3"),
        "wenzhi_12": ({"威权": +10, "声望": +8, "藩镇": -5}, "文治武功：文明昌盛，威权+10声望+8藩镇-5"),
    }

    effect = _SKILL_EFFECTS.get(skill_id)
    if not effect:
        return {"ok": False, "message": f"未找到技能效果：{skill_id}"}

    metric_delta, desc = effect
    for key, delta in metric_delta.items():
        state.metrics[key] = state.metrics.get(key, 0) + delta
    changes_str = ", ".join(f"{k}{'+' if v >= 0 else ''}{v}" for k, v in metric_delta.items())
    state.log.append(f"【技能生效】{desc}：{changes_str}")
    return {"ok": True, "message": desc, "delta": metric_delta}
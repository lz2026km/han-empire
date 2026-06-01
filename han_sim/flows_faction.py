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


# ════════════════════════════════════════════════════════════════
# v2.1.0 Phase 5.1: 派系密谋 (派系内政事件)
# ════════════════════════════════════════════════════════════════

def generate_faction_conspiracy(state: GameState, db: GameDB) -> List[Dict]:
    """每回合 30% 概率触发派系密谋 (4 派系各 1 个独特事件)

    返回: [ { faction, event_id, title, narrative, effects } ]
    """
    import random
    conspiracies = []
    faction_inf = state.metrics.get("faction_influence", {})

    for faction in ("忠汉派", "务实派", "离心派", "叛逆派"):
        inf = faction_inf.get(faction, 20)
        # 影响力 30+ 才可能密谋
        if inf < 30:
            continue
        if random.random() > 0.3:
            continue
        # 派系密谋事件池
        events = _FACTION_CONSPIRACIES.get(faction, [])
        if not events:
            continue
        ev = random.choice(events)
        conspiracies.append({
            "faction": faction,
            "event_id": ev["id"],
            "title": ev["title"],
            "narrative": ev["narrative"],
            "effects": ev["effects"],
            "authority_delta": ev.get("authority_delta", 0),
            "loyalty_delta": ev.get("loyalty_delta", 0),
        })
    return conspiracies


# ════════════════════════════════════════════════════════════════
# v2.1.0 Phase 5.2: 派系外交 (派系间关系: 结盟/敌对/和谈)
# ════════════════════════════════════════════════════════════════

def calc_faction_diplomacy(state: GameState) -> Dict[str, str]:
    """计算 4 派系相互关系 (盟友/敌对/中立)"""
    faction_inf = state.metrics.get("faction_influence", {})
    relations = {}

    # 忠汉派 vs 务实派: 共存
    relations[("忠汉派", "务实派")] = "共存"
    relations[("务实派", "忠汉派")] = "共存"

    # 忠汉派 vs 离心派: 紧张
    relations[("忠汉派", "离心派")] = "紧张"
    relations[("离心派", "忠汉派")] = "紧张"

    # 忠汉派 vs 叛逆派: 敌对
    relations[("忠汉派", "叛逆派")] = "敌对"
    relations[("叛逆派", "忠汉派")] = "敌对"

    # 务实派 vs 离心派: 暧昧
    relations[("务实派", "离心派")] = "暧昧"
    relations[("离心派", "务实派")] = "暧昧"

    # 务实派 vs 叛逆派: 利用
    relations[("务实派", "叛逆派")] = "利用"
    relations[("叛逆派", "务实派")] = "利用"

    # 离心派 vs 叛逆派: 暧昧
    relations[("离心派", "叛逆派")] = "暧昧"
    relations[("叛逆派", "离心派")] = "暧昧"

    return {f"{a}->{b}": v for (a, b), v in relations.items()}


# ════════════════════════════════════════════════════════════════
# v2.1.0 Phase 5.3: 派系目标链 (3 级: 短期/中期/长期)
# ════════════════════════════════════════════════════════════════

_FACTION_GOAL_CHAINS: Dict[str, List[Dict]] = {
    "忠汉派": [
        {"level": "短期", "goal": "扶持汉帝, 清理身边小人", "progress": 0},
        {"level": "中期", "goal": "联络天下忠义, 共扶社稷", "progress": 0},
        {"level": "长期", "goal": "兴复汉室, 还于旧都", "progress": 0},
    ],
    "务实派": [
        {"level": "短期", "goal": "保境安民, 积蓄粮草", "progress": 0},
        {"level": "中期", "goal": "左右逢源, 平衡四方", "progress": 0},
        {"level": "长期", "goal": "称霸一方, 问鼎天下", "progress": 0},
    ],
    "离心派": [
        {"level": "短期", "goal": "保存实力, 不动声色", "progress": 0},
        {"level": "中期", "goal": "联络诸侯, 静待时机", "progress": 0},
        {"level": "长期", "goal": "割据自立, 雄霸一方", "progress": 0},
    ],
    "叛逆派": [
        {"level": "短期", "goal": "铲除异己, 培养死士", "progress": 0},
        {"level": "中期", "goal": "废立天子, 另立新君", "progress": 0},
        {"level": "长期", "goal": "取汉室而代之, 称帝", "progress": 0},
    ],
}


def get_faction_goals(faction: str) -> List[Dict]:
    """获取派系 3 级目标链"""
    return _FACTION_GOAL_CHAINS.get(faction, [])


def advance_faction_goal(faction: str, level: str, amount: int) -> bool:
    """推进派系目标 (amount: 1-100)"""
    chain = _FACTION_GOAL_CHAINS.get(faction, [])
    for g in chain:
        if g["level"] == level:
            g["progress"] = min(100, g["progress"] + amount)
            return True
    return False


# ════════════════════════════════════════════════════════════════
# v2.1.0 Phase 5.4: 4 派系各自 3 个独特事件 (12 事件池)
# ════════════════════════════════════════════════════════════════

_FACTION_CONSPIRACIES: Dict[str, List[Dict]] = {
    "忠汉派": [
        {
            "id": "consp_zhonghan_1",
            "title": "衣带密诏再起",
            "narrative": "忠汉派密议: 陛下何不再修密诏, 号召天下忠义之士?",
            "effects": "威权+5, 忠诚+10",
            "authority_delta": 5,
            "loyalty_delta": 10,
        },
        {
            "id": "consp_zhonghan_2",
            "title": "宗亲联名上书",
            "narrative": "刘氏宗亲联名上书, 请求陛下重整朝纲, 惩治奸佞。",
            "effects": "威权+3, 忠汉派+10",
            "authority_delta": 3,
            "loyalty_delta": 5,
        },
        {
            "id": "consp_zhonghan_3",
            "title": "清君侧之议",
            "narrative": "忠汉派密谋清君侧, 欲铲除陛下身边的佞臣。",
            "effects": "威权+8, 风险: 若失败, 忠诚-15",
            "authority_delta": 8,
            "loyalty_delta": -5,
        },
    ],
    "务实派": [
        {
            "id": "consp_wushi_1",
            "title": "和谈之议",
            "narrative": "务实派建议与各方和谈, 保境安民, 积蓄实力。",
            "effects": "汉室库+200, 忠诚+5",
            "authority_delta": 0,
            "loyalty_delta": 5,
        },
        {
            "id": "consp_wushi_2",
            "title": "联姻之策",
            "narrative": "务实派提议与外藩联姻, 加强同盟。",
            "effects": "威权+2, 务实派+8",
            "authority_delta": 2,
            "loyalty_delta": 3,
        },
        {
            "id": "consp_wushi_3",
            "title": "屯田养兵",
            "narrative": "务实派主张大兴屯田, 以养精兵。",
            "effects": "汉室库-100, 兵力+500",
            "authority_delta": 1,
            "loyalty_delta": 2,
        },
    ],
    "离心派": [
        {
            "id": "consp_lixin_1",
            "title": "地方割据",
            "narrative": "离心派地方势力暗中扩充兵马, 离心倾向日益明显。",
            "effects": "藩镇+10, 离心派+15",
            "authority_delta": -2,
            "loyalty_delta": 0,
        },
        {
            "id": "consp_lixin_2",
            "title": "观望不前",
            "narrative": "离心派按兵不动, 静观天下大势。",
            "effects": "离心派+5, 忠诚-3",
            "authority_delta": 0,
            "loyalty_delta": -3,
        },
        {
            "id": "consp_lixin_3",
            "title": "暗通外藩",
            "narrative": "离心派暗中与外藩交通, 谋取私利。",
            "effects": "威权-5, 离心派+20",
            "authority_delta": -5,
            "loyalty_delta": -5,
        },
    ],
    "叛逆派": [
        {
            "id": "consp_panni_1",
            "title": "废立之议",
            "narrative": "叛逆派密议废立之事, 欲另立新君。",
            "effects": "威权-10, 风险极高",
            "authority_delta": -10,
            "loyalty_delta": -10,
        },
        {
            "id": "consp_panni_2",
            "title": "刺杀之谋",
            "narrative": "叛逆派密谋刺杀陛下, 风险极大。",
            "effects": "若失败, 叛逆派-30",
            "authority_delta": -5,
            "loyalty_delta": -8,
        },
        {
            "id": "consp_panni_3",
            "title": "公开反叛",
            "narrative": "叛逆派不再隐藏, 公开举起反旗。",
            "effects": "威权-20, 全面战争",
            "authority_delta": -20,
            "loyalty_delta": -15,
        },
    ],
}

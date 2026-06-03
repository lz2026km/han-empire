"""v2.1.0 Phase 4.1: 战役推演引擎

3 个东汉末年著名战役 (官渡 200 / 赤壁 208 / 夷陵 222)
- 每战役 2-3 阵营, 每阵营 3-5 部队
- 回合制推演: 士气/粮草/天气/将领加成
- AI 决策: 进攻/防守/撤退/突袭
- 战报生成: 文言文 + 战况变化

被 server.py /api/campaigns/{id}/battles/* 调用
"""
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum


class Side(str, Enum):
    """阵营"""
    HAN = "汉室"        # 献帝
    WEI = "曹魏"        # 曹操
    SHU = "蜀汉"        # 蜀汉
    WU = "东吴"        # 东吴
    YUAN = "袁绍"      # 群雄


class Weather(str, Enum):
    """天气 (影响战斗)"""
    SUN = "晴"
    RAIN = "雨"
    SNOW = "雪"
    FOG = "雾"
    WIND = "东风"  # 赤壁关键


class Action(str, Enum):
    """AI 决策"""
    ATTACK = "进攻"
    DEFEND = "防守"
    RETREAT = "撤退"
    FLANK = "突袭"


@dataclass
class Troop:
    """部队"""
    name: str             # 部队名 (例: 虎豹骑)
    commander: str        # 主将
    side: Side
    troops: int           # 兵力
    morale: int = 80      # 士气 0-100
    strength: int = 70    # 战力 0-100
    provisions: int = 50  # 粮草 0-100
    position: str = "前阵"  # 前阵/中军/后军/侧翼

    def is_alive(self) -> bool:
        return self.troops > 0 and self.morale > 0

    def __str__(self):
        return f"{self.commander}·{self.name}({self.side.value} {self.troops}兵 士气{self.morale})"


@dataclass
class BattleRound:
    """一回合战报"""
    round_num: int
    actions: List[str] = field(default_factory=list)  # 行动叙事
    casualties: Dict[str, int] = field(default_factory=dict)  # 部队→伤亡
    weather: Weather = Weather.SUN
    narrative: str = ""  # 文言战报

    def to_dict(self):
        return {
            "round": self.round_num,
            "actions": self.actions,
            "casualties": self.casualties,
            "weather": self.weather.value,
            "narrative": self.narrative,
        }


@dataclass
class BattleReport:
    """完整战报"""
    battle_id: str
    battle_name: str        # 战役名
    year: int
    location: str
    sides: List[Side]
    initial_troops: Dict[str, int]
    rounds: List[BattleRound]
    winner: Optional[Side]
    final_troops: Dict[str, int]
    casualties_total: Dict[str, int]
    loot: Dict[str, int]    # 战利品: 粮草/钱/将领
    summary: str            # 战后总结

    def to_dict(self):
        return {
            "battle_id": self.battle_id,
            "battle_name": self.battle_name,
            "year": self.year,
            "location": self.location,
            "sides": [s.value for s in self.sides],
            "initial_troops": self.initial_troops,
            "rounds": [r.to_dict() for r in self.rounds],
            "winner": self.winner.value if self.winner else None,
            "final_troops": self.final_troops,
            "casualties_total": self.casualties_total,
            "loot": self.loot,
            "summary": self.summary,
        }


# ════════════════════════════════════════════════════════════════
# 3 个历史战役数据 (源自《三国志》)
# ════════════════════════════════════════════════════════════════

BATTLE_GUANDU = {
    "battle_id": "battle_guandu_200",
    "battle_name": "官渡之战",
    "year": 200,
    "location": "官渡(今河南中牟)",
    "background": "袁绍据冀青幽并四州, 率众南伐。曹操以寡敌众, 屯官渡相拒。",
    "sides": [Side.HAN, Side.YUAN],  # 玩家代表汉室=曹魏
    "troops": [
        # 曹军
        Troop("虎豹骑", "曹操", Side.HAN, 8000, 90, 85, 80, "中军"),
        Troop("青州兵", "曹洪", Side.HAN, 15000, 75, 70, 60, "前阵"),
        Troop("骑兵", "张辽", Side.HAN, 5000, 85, 90, 70, "侧翼"),
        Troop("步兵", "于禁", Side.HAN, 12000, 70, 65, 50, "前阵"),
        Troop("屯田兵", "韩馥", Side.HAN, 6000, 60, 50, 40, "后军"),
        # 袁军
        Troop("冀州精兵", "颜良", Side.YUAN, 12000, 85, 85, 90, "前阵"),
        Troop("骑兵", "文丑", Side.YUAN, 10000, 85, 90, 90, "前阵"),
        Troop("弓弩手", "沮授", Side.YUAN, 15000, 70, 75, 95, "中军"),
        Troop("乌巢屯军", "韩馥", Side.YUAN, 8000, 60, 60, 100, "后军"),
    ],
}

BATTLE_CHIBI = {
    "battle_id": "battle_chibi_208",
    "battle_name": "赤壁之战",
    "year": 208,
    "location": "赤壁(今湖北赤壁)",
    "background": "曹操平定北方, 挥师南下, 欲一统天下。孙权刘备联军, 据江而守。",
    "sides": [Side.SHU, Side.WU, Side.WEI],  # 多方
    "troops": [
        # 蜀军
        Troop("白毦兵", "刘备", Side.SHU, 8000, 80, 75, 60, "后军"),
        Troop("荆州兵", "关羽", Side.SHU, 10000, 85, 85, 65, "前阵"),
        Troop("水军", "诸葛亮", Side.SHU, 5000, 70, 70, 55, "侧翼"),
        # 吴军
        Troop("江东子弟", "周瑜", Side.WU, 12000, 95, 90, 70, "前阵"),
        Troop("水军", "黄盖", Side.WU, 8000, 85, 80, 60, "侧翼"),
        Troop("弓弩手", "鲁肃", Side.WU, 6000, 75, 80, 65, "中军"),
        # 魏军
        Troop("青州兵", "曹操", Side.WEI, 20000, 70, 75, 40, "前阵"),
        Troop("虎豹骑", "曹仁", Side.WEI, 10000, 75, 80, 45, "中军"),
        Troop("荆州水军", "蔡瑁", Side.WEI, 12000, 60, 60, 50, "后军"),
    ],
}

BATTLE_YILING = {
    "battle_id": "battle_yiling_222",
    "battle_name": "夷陵之战",
    "year": 222,
    "location": "夷陵(今湖北宜昌)",
    "background": "关羽败走麦城, 蜀吴交恶。刘备伐吴, 欲为关羽复仇。吴将陆逊以逸待劳。",
    "sides": [Side.SHU, Side.WU],
    "troops": [
        # 蜀军
        Troop("益州兵", "刘备", Side.SHU, 15000, 85, 80, 50, "中军"),
        Troop("五溪蛮兵", "沙摩柯", Side.SHU, 6000, 75, 70, 40, "侧翼"),
        Troop("先锋", "冯习", Side.SHU, 10000, 80, 75, 45, "前阵"),
        Troop("后军", "黄权", Side.SHU, 8000, 70, 70, 50, "后军"),
        # 吴军
        Troop("江东精兵", "陆逊", Side.WU, 12000, 90, 85, 70, "后军"),
        Troop("朱然军", "朱然", Side.WU, 8000, 80, 80, 65, "前阵"),
        Troop("潘璋军", "潘璋", Side.WU, 6000, 75, 75, 60, "侧翼"),
        Troop("火攻队", "陆逊", Side.WU, 3000, 95, 90, 65, "中军"),
    ],
}

BATTLES = {
    "guandu": BATTLE_GUANDU,
    "chibi": BATTLE_CHIBI,
    "yiling": BATTLE_YILING,
}


# ════════════════════════════════════════════════════════════════
# AI 决策 (基于士气/粮草/兵力)
# ════════════════════════════════════════════════════════════════

def ai_decide(troop: Troop, weather: Weather) -> Action:
    """AI 决策, 基于当前状态"""
    if troop.provisions < 20 or troop.morale < 30:
        return Action.RETREAT
    if troop.troops < 3000:
        return Action.DEFEND
    if weather == Weather.FOG:
        return Action.FLANK
    if troop.morale > 80 and troop.troops > 8000:
        return Action.ATTACK
    return Action.DEFEND


# ════════════════════════════════════════════════════════════════
# 战报生成 (文言文)
# ════════════════════════════════════════════════════════════════

def gen_round_narrative(round_num: int, actions: List[str], weather: Weather) -> str:
    """生成文言战报"""
    weather_txt = f"时值{weather.value}。"
    if round_num == 1:
        return f"{weather_txt}两军对垒, 鼓声雷动。{('; '.join(actions))}"
    return f"{weather_txt}{'; '.join(actions)}"


# ════════════════════════════════════════════════════════════════
# 推演引擎
# ════════════════════════════════════════════════════════════════

def calc_damage(attacker: Troop, defender: Troop, weather: Weather) -> int:
    """单次攻击伤害"""
    base = random.randint(50, 150)
    # 士气/战力加成
    base += int(attacker.morale * 0.5)
    base += int(attacker.strength * 0.3)
    # 天气影响
    if weather == Weather.RAIN:
        base = int(base * 0.7)  # 雨削弱弓
    elif weather == Weather.WIND:
        base = int(base * 1.2)  # 顺风
    elif weather == Weather.FOG:
        base = int(base * 0.8)
    return max(0, base)


def simulate_battle(battle_key: str, player_side: Optional[Side] = None) -> BattleReport:
    """推演战役

    Args:
        battle_key: 战役 key (guandu/chibi/yiling)
        player_side: 玩家阵营 (None=纯AI)

    Returns:
        BattleReport
    """
    if battle_key not in BATTLES:
        raise ValueError(f"未知战役: {battle_key}")

    bdata = BATTLES[battle_key]
    battle_id = bdata["battle_id"]
    battle_name = bdata["battle_name"]
    year = bdata["year"]
    location = bdata["location"]
    background = bdata["background"]
    sides = bdata["sides"]

    # 复制 troops (避免修改原数据)
    troops = [
        Troop(
            name=t.name, commander=t.commander, side=t.side,
            troops=t.troops, morale=t.morale, strength=t.strength,
            provisions=t.provisions, position=t.position
        )
        for t in bdata["troops"]
    ]

    initial_troops = {f"{t.commander}·{t.name}": t.troops for t in troops}

    rounds: List[BattleRound] = []
    weather = random.choice([Weather.SUN, Weather.RAIN, Weather.WIND, Weather.FOG])

    max_rounds = 10
    for r in range(1, max_rounds + 1):
        # 天气变化
        if r in (3, 7):
            weather = random.choice([Weather.SUN, Weather.RAIN, Weather.WIND, Weather.FOG])

        round_actions = []
        round_casualties = {}

        # 粮草消耗
        for t in troops:
            t.provisions = max(0, t.provisions - 5)
            if t.provisions < 20:
                t.morale = max(0, t.morale - 5)

        # AI 决策 + 攻击
        attackers = [t for t in troops if t.is_alive()]
        random.shuffle(attackers)

        for att in attackers:
            action = ai_decide(att, weather)
            # 找敌对阵营
            enemies = [t for t in troops if t.is_alive() and t.side != att.side]
            if not enemies:
                break
            target = random.choice(enemies)

            if action == Action.ATTACK:
                dmg = calc_damage(att, target, weather)
                actual_dmg = min(dmg, target.troops)
                target.troops -= actual_dmg
                target.morale = max(0, target.morale - random.randint(5, 15))
                round_casualties[f"{target.commander}·{target.name}"] = round_casualties.get(f"{target.commander}·{target.name}", 0) + actual_dmg
                round_actions.append(f"{att.commander}攻{target.commander}, 斩首{actual_dmg}级")
            elif action == Action.FLANK:
                dmg = calc_damage(att, target, weather)
                actual_dmg = int(dmg * 1.5)
                actual_dmg = min(actual_dmg, target.troops)
                target.troops -= actual_dmg
                target.morale = max(0, target.morale - random.randint(8, 18))
                round_casualties[f"{target.commander}·{target.name}"] = round_casualties.get(f"{target.commander}·{target.name}", 0) + actual_dmg
                round_actions.append(f"{att.commander}绕击{target.commander}, 大破{actual_dmg}")
            elif action == Action.RETREAT:
                att.troops = int(att.troops * 0.8)  # 撤退损失 20%
                att.morale = max(0, att.morale - 20)
                round_actions.append(f"{att.commander}兵败, 退守")
            else:  # DEFEND
                round_actions.append(f"{att.commander}固守")

        narrative = gen_round_narrative(r, round_actions, weather)
        rounds.append(BattleRound(
            round_num=r,
            actions=round_actions,
            casualties=round_casualties,
            weather=weather,
            narrative=narrative,
        ))

        # 检查胜负
        alive_sides = {t.side for t in troops if t.is_alive()}
        if len(alive_sides) == 1:
            break
        # 双方都没兵力
        if all(not t.is_alive() for t in troops):
            break

    # 计算最终结果
    alive_sides = {t.side for t in troops if t.is_alive()}
    if len(alive_sides) == 1:
        winner = alive_sides.pop()
    else:
        # 按剩余兵力多者胜
        side_troops: Dict[Side, int] = {}
        for t in troops:
            if t.is_alive():
                side_troops[t.side] = side_troops.get(t.side, 0) + t.troops
        winner = max(side_troops, key=lambda s: side_troops[s]) if side_troops else None

    final_troops = {f"{t.commander}·{t.name}": max(0, t.troops) for t in troops}
    casualties_total = {
        k: initial_troops[k] - final_troops[k]
        for k in initial_troops
        if initial_troops[k] > final_troops[k]
    }

    # 战利品
    loot = {"粮草": random.randint(500, 2000), "金帛": random.randint(100, 1000)}
    if winner == player_side:
        loot["声望"] = 100

    # 战后总结 (文言)
    if winner == Side.HAN or winner == Side.SHU or winner == Side.WU:
        winner_name = winner.value
    elif winner == Side.WEI:
        winner_name = "曹魏"
    elif winner == Side.YUAN:
        winner_name = "袁军"
    else:
        winner_name = "无"
    summary = f"{background}{winner_name}大胜, 斩首{sum(casualties_total.values())}。"

    return BattleReport(
        battle_id=battle_id,
        battle_name=battle_name,
        year=year,
        location=location,
        sides=sides,
        initial_troops=initial_troops,
        rounds=rounds,
        winner=winner,
        final_troops=final_troops,
        casualties_total=casualties_total,
        loot=loot,
        summary=summary,
    )


def list_battles() -> List[Dict]:
    """列出所有战役 (供 API)"""
    return [
        {
            "battle_id": BATTLES[k]["battle_id"],
            "battle_name": BATTLES[k]["battle_name"],
            "year": BATTLES[k]["year"],
            "location": BATTLES[k]["location"],
            "background": BATTLES[k]["background"],
            "sides": [s.value for s in BATTLES[k]["sides"]],
            "troop_count": len(BATTLES[k]["troops"]),
            "total_troops": sum(t.troops for t in BATTLES[k]["troops"]),
        }
        for k in ("guandu", "chibi", "yiling")
    ]

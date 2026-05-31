"""数据类：游戏实体与状态容器。L0 叶子模块。"""



from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class AuthorityLevel:
    level: int          # 威权数值
    label: str          # 标签：如"诏书如山"
    decree_mult: float  # 诏书效果倍率
    summon_mult: float   # 召对效果倍率
    warlord_stability: float  # 诸侯稳定性加成（威权高则不易叛）
    faction_event_mod: float  # 派系事件强度修正
    recovery_actions: List[str]  # 可用恢复行动

# 威权等级表（0-100分5档）
AUTHORITY_LEVELS: Dict[int, AuthorityLevel] = {
    # 0-19：形同虚设
    0: AuthorityLevel(0, "形同虚设", 0.3, 0.3, 0.0, 1.5,
                      ["求情示弱", "笼络近臣"]),
    10: AuthorityLevel(10, "权臣操弄", 0.4, 0.4, 0.1, 1.4,
                       ["求情示弱", "笼络近臣", "施恩示好"]),
    # 20-49：阳奉阴违
    20: AuthorityLevel(20, "阳奉阴违", 0.6, 0.6, 0.3, 1.2,
                       ["施恩示好", "笼络近臣", "朝会演讲", "处理政务"]),
    30: AuthorityLevel(30, "勉强维持", 0.7, 0.7, 0.4, 1.1,
                       ["施恩示好", "笼络近臣", "朝会演讲", "处理政务", "颁布诏书"]),
    # 50-79：诏书有效
    40: AuthorityLevel(40, "诏书有效", 0.8, 0.8, 0.5, 1.0,
                       ["朝会演讲", "处理政务", "颁布诏书", "召见贤才"]),
    50: AuthorityLevel(50, "朝纲初振", 0.9, 0.9, 0.6, 0.9,
                       ["朝会演讲", "处理政务", "颁布诏书", "召见贤才", "整饬吏治"]),
    60: AuthorityLevel(60, "略有起色", 1.0, 1.0, 0.7, 0.8,
                       ["朝会演讲", "处理政务", "颁布诏书", "召见贤才", "整饬吏治", "军事演练"]),
    # 80-100：诏书如山
    70: AuthorityLevel(70, "威权渐张", 1.1, 1.1, 0.8, 0.7,
                       ["朝会演讲", "处理政务", "颁布诏书", "召见贤才", "整饬吏治", "军事演练", "祭天祈福"]),
    80: AuthorityLevel(80, "号令四方", 1.2, 1.2, 0.9, 0.6,
                       ["朝会演讲", "颁布诏书", "召见贤才", "整饬吏治", "军事演练", "祭天祈福", "册封功臣"]),
    90: AuthorityLevel(90, "天下归心", 1.3, 1.3, 1.0, 0.5,
                       ["朝会演讲", "颁布诏书", "召见贤才", "整饬吏治", "军事演练", "祭天祈福", "册封功臣", "颁布罪己诏"]),
    100: AuthorityLevel(100, "至高无上", 1.5, 1.5, 1.2, 0.3,
                        ["朝会演讲", "颁布诏书", "召见贤才", "整饬吏治", "军事演练", "祭天祈福", "册封功臣", "颁布罪己诏", "大赦天下"]),
}


def get_authority_level(authority: int) -> AuthorityLevel:
    """根据威权值返回对应等级信息。"""
    # 向下取整到最近的已知等级
    levels = sorted(AUTHORITY_LEVELS.keys())
    for lvl in reversed(levels):
        if authority >= lvl:
            return AUTHORITY_LEVELS[lvl]
    return AUTHORITY_LEVELS[0]


# ── 天子技能树（Step1新增）────────────────────────────────────────

@dataclass
class Skill:
    sid: str           # 唯一标识，如 "jx_03"
    name: str          # 技能名，如 "重农抑商"
    cost: int          # 激活消耗技能点
    effect: str        # 效果描述
    unlock_level: int  # 威权等级要求（威权>=此值才能激活）
    tier: int          # 层阶（1-3，层阶越高越强）
    branch: str         # 所属流派
    requires: List[str] = field(default_factory=list)  # 前置技能（需先激活）


# 四系技能树定义（每系12条，共48条）
SKILL_TREES: Dict[str, List[Skill]] = {
    "经略": [
        Skill("jx_01", "轻赋薄敛", 1, "田赋收入+15%", 0, 1, "经略"),
        Skill("jx_02", "重农抑商", 2, "农业税收+20%，商业税收-10%", 20, 1, "经略", requires=["jx_01"]),
        Skill("jx_03", "修养生息", 2, "人口增长+10%/年", 30, 1, "经略", requires=["jx_02"]),
        Skill("jx_04", "盐铁专营", 3, "盐铁专营收入+25%", 40, 2, "经略", requires=["jx_03"]),
        Skill("jx_05", "漕运畅通", 2, "各州联系紧密度+5%", 40, 2, "经略"),
        Skill("jx_06", "屯田制度", 3, "军粮自给+20%", 50, 2, "经略", requires=["jx_04"]),
        Skill("jx_07", "兴修水利", 3, "农业税收+额外10%", 50, 2, "经略", requires=["jx_03"]),
        Skill("jx_08", "均输平准", 3, "物价稳定，财政波动-30%", 60, 3, "经略", requires=["jx_05", "jx_07"]),
        Skill("jx_09", "调控粮价", 3, "荒年粮食充足，粮价稳定", 60, 3, "经略", requires=["jx_08"]),
        Skill("jx_10", "深耕细作", 4, "农业税收+30%", 70, 3, "经略", requires=["jx_09"]),
        Skill("jx_11", "工商并举", 4, "商税+20%且不影响农业", 80, 3, "经略", requires=["jx_10"]),
        Skill("jx_12", "民富国强", 5, "田赋+商税+30%，藩镇-5", 90, 3, "经略", requires=["jx_11"]),
    ],
    "权谋": [
        Skill("qm_01", "以退为进", 1, "示弱待变，诸侯警惕-10%", 0, 1, "权谋"),
        Skill("qm_02", "借刀杀人", 2, "唆使诸侯内斗，藩镇+5", 20, 1, "权谋", requires=["qm_01"]),
        Skill("qm_03", "离间计", 3, "指定诸侯忠诚度-15", 30, 1, "权谋", requires=["qm_02"]),
        Skill("qm_04", "缓兵之计", 2, "叛逃事件触发延迟1回合", 40, 2, "权谋", requires=["qm_01"]),
        Skill("qm_05", "纵横捭阖", 3, "联盟关系改善速度+50%", 40, 2, "权谋", requires=["qm_02"]),
        Skill("qm_06", "挟天子令诸侯", 4, "声望≥50时，诏书效果+0.3", 50, 2, "权谋", requires=["qm_03", "qm_05"]),
        Skill("qm_07", "暗度陈仓", 3, "秘密行动成功率+30%", 50, 2, "权谋", requires=["qm_04"]),
        Skill("qm_08", "联吴抗曹", 3, "联合孙权势力，抗曹联盟强度+20%", 60, 3, "权谋", requires=["qm_06"]),
        Skill("qm_09", "上屋抽梯", 4, "使某诸侯完全孤立", 60, 3, "权谋", requires=["qm_07"]),
        Skill("qm_10", "假途伐虢", 4, "借道伐敌，损耗-30%", 70, 3, "权谋", requires=["qm_08", "qm_09"]),
        Skill("qm_11", "草木皆兵", 4, "威吓敌军，敌军士气-20%", 80, 3, "权谋", requires=["qm_10"]),
        Skill("qm_12", "天下为棋", 5, "所有诸侯忠诚度+10，威权判定+0.2", 90, 3, "权谋", requires=["qm_11"]),
    ],
    "武功": [
        Skill("wg_01", "整军经武", 1, "军事演练效果+20%", 0, 1, "武功"),
        Skill("wg_02", "以寡敌众", 2, "以少胜多概率+15%", 20, 1, "武功", requires=["wg_01"]),
        Skill("wg_03", "精兵简政", 2, "军队维持成本-15%", 30, 1, "武功", requires=["wg_01"]),
        Skill("wg_04", "坚壁清野", 3, "城池防御+20%", 40, 2, "武功", requires=["wg_02"]),
        Skill("wg_05", "知己知彼", 2, "情报精确度+30%", 40, 2, "武功", requires=["wg_01"]),
        Skill("wg_06", "名将养成", 3, "武将能力培养速度+25%", 50, 2, "武功", requires=["wg_04"]),
        Skill("wg_07", "连环计", 3, "战术配合效果+30%", 50, 2, "武功", requires=["wg_04", "wg_05"]),
        Skill("wg_08", "火攻决", 4, "火攻战术伤害+50%", 60, 3, "武功", requires=["wg_06", "wg_07"]),
        Skill("wg_09", "谋定后动", 3, "先手必胜，战斗先手+1", 60, 3, "武功", requires=["wg_05"]),
        Skill("wg_10", "破釜沉舟", 4, "背水一战，危急时刻爆发+40%", 70, 3, "武功", requires=["wg_08", "wg_09"]),
        Skill("wg_11", "韩信点兵", 4, "军队指挥效率+25%", 80, 3, "武功", requires=["wg_10"]),
        Skill("wg_12", "威震华夏", 5, "威权+15，声望+10，藩镇-10", 90, 3, "武功", requires=["wg_11"]),
    ],
    "文治": [
        Skill("wz_01", "兴学育才", 1, "每回合+0.5技能点（威权≥40时）", 0, 1, "文治"),
        Skill("wz_02", "举孝廉", 2, "忠诚人才出现概率+20%", 20, 1, "文治", requires=["wz_01"]),
        Skill("wz_03", "太学立学", 2, "大臣能力上限+5", 30, 1, "文治", requires=["wz_01"]),
        Skill("wz_04", "科举取士", 3, "寒门人才出现概率+30%", 40, 2, "文治", requires=["wz_02"]),
        Skill("wz_05", "以德治国", 2, "声望+5，威权衰减减缓10%", 40, 2, "文治"),
        Skill("wz_06", "修律定刑", 3, "政务效率+20%，政务处理消耗-20%", 50, 2, "文治", requires=["wz_03"]),
        Skill("wz_07", "儒道传承", 3, "大臣忠诚度自然+1/季度", 50, 2, "文治", requires=["wz_05"]),
        Skill("wz_08", "文景之治", 4, "民望大增，声望+15", 60, 3, "文治", requires=["wz_06", "wz_07"]),
        Skill("wz_09", "开疆拓土", 4, "新州郡开发速度+40%", 60, 3, "文治", requires=["wz_06"]),
        Skill("wz_10", "光武中兴", 4, "汉室中兴，声望+20，威权+10", 70, 3, "文治", requires=["wz_08", "wz_09"]),
        Skill("wz_11", "万邦来朝", 5, "外交影响力大增，诸侯贡金+50%", 80, 3, "文治", requires=["wz_10"]),
        Skill("wz_12", "千古一帝", 5, "威权+20，声望+25，藩镇-15，所有技能效果+10%", 90, 3, "文治", requires=["wz_11"]),
    ],
}


def get_skill_by_id(sid: str) -> Optional[Skill]:
    """根据技能ID获取技能。"""
    for tree in SKILL_TREES.values():
        for skill in tree:
            if skill.sid == sid:
                return skill
    return None


def get_available_skills(authority: int, activated: List[str]) -> List[Skill]:
    """获取当前威权下可激活的技能（未激活且满足威权要求）。"""
    available = []
    for tree in SKILL_TREES.values():
        for skill in tree:
            if skill.sid in activated:
                continue
            if authority >= skill.unlock_level:
                # 检查前置技能
                if not skill.requires:
                    available.append(skill)
                elif all(r in activated for r in skill.requires):
                    available.append(skill)
    return available


def can_activate_skill(skill: Skill, authority: int, activated: List[str], skill_points: int) -> Tuple[bool, str]:
    """检查技能是否可以激活，返回(是否可激活, 原因)。"""
    if authority < skill.unlock_level:
        return False, f"威权不足（需{skill.unlock_level}，当前{authority}）"
    if not all(r in activated for r in skill.requires):
        missing = [r for r in skill.requires if r not in activated]
        return False, f"需先激活前置技能：{', '.join(missing)}"
    if skill_points < skill.cost:
        return False, f"技能点不足（需{skill.cost}，当前{skill_points}）"
    return True, "可激活"


# ── 建筑系统（Step2新增）────────────────────────────────────────

@dataclass
class Building:
    bid: str           # 唯一标识，如 "weiyang"
    name: str          # 建筑名，如 "未央宫"
    cost: int          # 建造费用（汉室库消耗）
    maintenance: int   # 每年维护费
    effect: str        # 效果描述
    effect_bonus: Dict[str, float]  # 效果加成dict（百分比）
    unlock_level: int  # 解锁威权要求
    location: str       # 建造地点
    condition: int = 100  # 建筑状态 0-100（借鉴大明condition）
    risk: int = 0         # 损毁风险 0-100
    output_metric: str = ""   # 产出指标
    output_amount: int = 0   # 产出量


BUILDING_CATALOG: Dict[str, Building] = {
    # 宫殿类
    "weiyang": Building("weiyang", "未央宫", 150, 20,
                        "威权+3/年",
                        {"威权": 3.0}, 40, "长安"),
    "xuchang_palace": Building("xuchang_palace", "许昌行宫", 100, 15,
                               "威权衰减减缓50%",
                               {"decay_reduce": 0.5}, 30, "许昌"),
    "luoyang_palace": Building("luoyang_palace", "洛阳宫殿", 120, 18,
                               "声望+2/年",
                               {"声望": 2.0}, 35, "洛阳"),
    # 军事类
    "luoyang_armory": Building("luoyang_armory", "洛阳武库", 100, 12,
                                "军事行动效果+15%",
                                {"military": 0.15}, 30, "洛阳"),
    "yanzhou_arsenal": Building("yanzhou_arsenal", "兖州武库", 90, 10,
                                "军事行动效果+10%",
                                {"military": 0.10}, 25, "兖州"),
    "jinzhou_arsenal": Building("jinzhou_arsenal", "荆州武库", 90, 10,
                                "军事行动效果+10%",
                                {"military": 0.10}, 25, "荆州"),
    "yangzhou_arsenal": Building("yangzhou_arsenal", "扬州武库", 80, 8,
                                "军事行动效果+8%",
                                {"military": 0.08}, 20, "扬州"),
    # 经济类
    "yanzhou_granary": Building("yanzhou_granary", "兖州粮仓", 60, 8,
                                "田赋收入+10%",
                                {"tax_land": 0.10}, 10, "兖州"),
    "jinzhou_granary": Building("jinzhou_granary", "荆州粮仓", 60, 8,
                                "田赋收入+10%",
                                {"tax_land": 0.10}, 10, "荆州"),
    "xuzhou_granary": Building("xuzhou_granary", "徐州粮仓", 50, 6,
                               "田赋收入+8%",
                               {"tax_land": 0.08}, 10, "徐州"),
    "guangzhou_granary": Building("guangzhou_granary", "广州粮仓", 50, 6,
                                  "田赋收入+8%",
                                  {"tax_land": 0.08}, 10, "广州"),
    # 特殊建筑
    "jiujiang_dock": Building("jiujiang_dock", "九江船坞", 70, 10,
                               "水军效果+20%",
                               {"naval": 0.20}, 30, "九江"),
    "tongguan_fort": Building("tongguan_fort", "潼关要塞", 80, 12,
                               "长安防御+25%",
                               {"defense": 0.25}, 35, "长安"),
    "hulao_pass": Building("hulao_pass", "虎牢关", 60, 8,
                            "洛阳防御+20%",
                            {"defense": 0.20}, 20, "洛阳"),
}


BUILDING_TYPES = {
    "宫殿": ["weiyang", "xuchang_palace", "luoyang_palace"],
    "军事": ["luoyang_armory", "yanzhou_arsenal", "jinzhou_arsenal", "yangzhou_arsenal"],
    "经济": ["yanzhou_granary", "jinzhou_granary", "xuzhou_granary", "guangzhou_granary"],
    "特殊": ["jiujiang_dock", "tongguan_fort", "hulao_pass"],
}


# ── 建筑状态与损耗（Step3新增）────────────────────────────────

def apply_building_deterioration(state: "GameState") -> List[str]:
    """每月建筑状态损耗：
    - 状态低于60：风险+5
    - 状态低于30：风险+10
    - 风险过高的建筑有概率损坏
    返回损坏建筑列表。
    """
    built = state.metrics.get("built_buildings", {})
    damaged = []
    for bid, bdata in built.items():
        cond = bdata.get("condition", 100)
        risk = bdata.get("risk", 0)
        # 自然损耗
        cond = max(0, cond - random.randint(0, 2))
        # 低状态加风险
        if cond < 30:
            risk += random.randint(5, 10)
        elif cond < 60:
            risk += random.randint(1, 5)
        # 随机损坏判定
        if risk >= 80 and random.random() < 0.15:
            cond = max(0, cond - random.randint(20, 40))
            damaged.append(bid)
        built[bid] = {"condition": cond, "risk": min(100, risk)}
    state.metrics["built_buildings"] = built
    if damaged:
        state.log.append(f"【建筑损坏】{', '.join(damaged)}受损！")
    return damaged


def repair_building(state: "GameState", bid: str, cost: int) -> Dict:
    """修缮建筑（消耗汉室库，恢复condition）。"""
    built = state.metrics.get("built_buildings", {})
    if bid not in built:
        return {"success": False, "narrative": f"建筑 {bid} 未建造"}
    han_ku = state.metrics.get("汉室库", 0)
    if han_ku < cost:
        return {"success": False, "narrative": f"汉室库不足（需{cost}，当前{han_ku}）"}
    bdata = built[bid]
    cond = min(100, bdata.get("condition", 50) + 30)
    built[bid] = {"condition": cond, "risk": max(0, bdata.get("risk", 0) - 20)}
    state.metrics["built_buildings"] = built
    state.metrics["汉室库"] = han_ku - cost
    state.log.append(f"【修缮完成】{bid}修缮完毕，状态恢复至{cond}")
    return {"success": True, "narrative": f"✅ {bid}修缮完成！费用-{cost}，状态{cond}/100"}


def get_building_status_detailed(state: "GameState") -> Dict[str, Dict]:
    """获取所有建筑详细状态（condition/risk）。"""
    built = state.metrics.get("built_buildings", {})
    result = {}
    for bid, bdata in built.items():
        b = get_building_by_id(bid)
        if b:
            result[bid] = {
                "name": b.name,
                "condition": bdata.get("condition", 100),
                "risk": bdata.get("risk", 0),
                "maintenance": b.maintenance,
                "effect": b.effect,
                "location": b.location,
            }
    return result


def get_building_by_id(bid: str) -> Optional[Building]:
    return BUILDING_CATALOG.get(bid)


def get_available_buildings(authority: int, built: List[str]) -> List[Building]:
    """获取当前可建造的建筑（未建造且满足威权要求）。"""
    available = []
    for bid, building in BUILDING_CATALOG.items():
        if bid in built:
            continue
        if authority >= building.unlock_level:
            available.append(building)
    return available


# ── 指令状态机（Step3新增）────────────────────────────────────────

@dataclass
class DecreeRecord:
    decree_id: str       # 诏书ID（如 "dec_001"）
    decree_type: str      # 诏书类型（衣带密诏/讨伐诏书/迁都诏书/嘉奖诏书）
    title: str           # 诏书标题
    content: str         # 诏书内容
    status: str          # 状态：draft / issued / expired / executed / cancelled
    issued_turn: int     # 发布回合（0表示未发布）
    expire_turn: int     # 过期回合（0表示未发布）
    execute_turn: int     # 执行回合（0表示未执行）
    target: str          # 目标（如"曹操"或"许昌"）
    authority_cost: int  # 发布所需威权
    effects: Dict        # 效果描述


DECREE_TYPE_META: Dict[str, Dict] = {
    "衣带密诏": {
        "authority_cost": 30,
        "valid_turns": 3,
        "can_cancel": True,
        "effect_desc": "串联忠臣诛贼",
    },
    "讨伐诏书": {
        "authority_cost": 40,
        "valid_turns": 4,
        "can_cancel": True,
        "effect_desc": "号召诸侯讨伐",
    },
    "迁都诏书": {
        "authority_cost": 50,
        "valid_turns": 6,
        "can_cancel": False,
        "effect_desc": "迁都改元",
    },
    "嘉奖诏书": {
        "authority_cost": 20,
        "valid_turns": 2,
        "can_cancel": True,
        "effect_desc": "嘉奖功臣",
    },
    "罪己诏": {
        "authority_cost": 60,
        "valid_turns": 5,
        "can_cancel": False,
        "effect_desc": "下诏罪己，收拢民心",
    },
    "大赦天下": {
        "authority_cost": 40,
        "valid_turns": 3,
        "can_cancel": False,
        "effect_desc": "大赦天下，安定民心",
    },
    "自由诏书": {
        "authority_cost": 25,
        "valid_turns": 4,
        "can_cancel": True,
        "effect_desc": "自主拟旨，特事特办",
    },
}


def get_decree_status(state: "GameState", decree_id: str) -> Optional[DecreeRecord]:
    """查询某诏书状态。"""
    active = state.metrics.get("active_decrees", [])
    for dec in active:
        if dec.decree_id == decree_id:
            return dec
    return None


def list_active_decrees(state: "GameState") -> List[DecreeRecord]:
    """列出所有有效诏书。"""
    return [dec for dec in state.metrics.get("active_decrees", [])
            if dec.status in ("issued", "draft")]


def issue_decree(state: "GameState", decree_type: str, title: str, content: str, target: str = "") -> Dict:
    """发布诏书（草稿→已发布）。返回结果dict。"""
    meta = DECREE_TYPE_META.get(decree_type)
    if not meta:
        return {"success": False, "narrative": f"未知诏书类型：{decree_type}"}
    authority = state.metrics.get("威权", 0)
    if authority < meta["authority_cost"]:
        return {"success": False, "narrative": f"威权不足（需{meta['authority_cost']}，当前{authority}）"}

    # 生成ID
    active = state.metrics.get("active_decrees", [])
    dec_id = f"dec_{len(active) + 1:03d}"

    decree = DecreeRecord(
        decree_id=dec_id,
        decree_type=decree_type,
        title=title,
        content=content,
        status="issued",
        issued_turn=state.turn,
        expire_turn=state.turn + meta["valid_turns"],
        execute_turn=0,
        target=target,
        authority_cost=meta["authority_cost"],
        effects={"effect_desc": meta["effect_desc"]},
    )
    state.metrics["active_decrees"] = active + [decree]
    state.log.append(f"【诏书发布】{title}（{decree_type}），有效期{meta['valid_turns']}回合")
    return {
        "success": True,
        "narrative": f"✅ {title}已发布！\n类型：{decree_type}\n有效期：{meta['valid_turns']}回合\n效果：{meta['effect_desc']}",
        "decree_id": dec_id,
    }


def execute_decree(state: "GameState", decree_id: str) -> Dict:
    """执行已发布的诏书（issued→executed）。"""
    active = state.metrics.get("active_decrees", [])
    for dec in active:
        if dec.decree_id == decree_id:
            if dec.status != "issued":
                return {"success": False, "narrative": f"诏书状态不是已发布（当前：{dec.status}）"}
            dec.status = "executed"
            dec.execute_turn = state.turn
            state.metrics["active_decrees"] = active
            state.log.append(f"【诏书执行】{dec.title}（{dec.decree_type}）")
            return {
                "success": True,
                "narrative": f"✅ {dec.title}已执行！",
                "decree": dec.decree_type,
            }
    return {"success": False, "narrative": f"未找到诏书：{decree_id}"}


def cancel_decree(state: "GameState", decree_id: str) -> Dict:
    """取消诏书（仅draft/issued且can_cancel=True）。"""
    meta = DECREE_TYPE_META.get(state.metrics.get("active_decrees", [DecreeRecord("","","","","",0,0,0,"","",{})])[0].decree_type if state.metrics.get("active_decrees") else {})
    active = state.metrics.get("active_decrees", [])
    for i, dec in enumerate(active):
        if dec.decree_id == decree_id:
            dec_meta = DECREE_TYPE_META.get(dec.decree_type, {})
            if not dec_meta.get("can_cancel", False):
                return {"success": False, "narrative": f"【{dec.decree_type}】不可取消"}
            if dec.status == "executed":
                return {"success": False, "narrative": "诏书已执行，无法取消"}
            dec.status = "cancelled"
            state.metrics["active_decrees"] = active
            state.log.append(f"【诏书取消】{dec.title}（{dec.decree_type}）")
            return {
                "success": True,
                "narrative": f"✅ {dec.title}已取消",
            }
    return {"success": False, "narrative": f"未找到诏书：{decree_id}"}


def tick_decree_expiry(state: "GameState") -> List[DecreeRecord]:
    """回合推进时检查诏书过期，返回过期列表。"""
    active = state.metrics.get("active_decrees", [])
    expired_list = []
    for dec in active:
        if dec.status == "issued" and dec.expire_turn > 0 and state.turn >= dec.expire_turn:
            dec.status = "expired"
            state.log.append(f"【诏书过期】{dec.title}（{dec.decree_type}）已过期")
            expired_list.append(dec)
    state.metrics["active_decrees"] = active
    return expired_list


def get_decree_dashboard(state: "GameState") -> Dict:
    """获取诏书状态总览。"""
    active = state.metrics.get("active_decrees", [])
    by_status = {}
    for dec in active:
        by_status.setdefault(dec.status, []).append({
            "id": dec.decree_id,
            "title": dec.title,
            "type": dec.decree_type,
            "target": dec.target,
            "issued_turn": dec.issued_turn,
            "expire_turn": dec.expire_turn,
            "remaining": max(0, dec.expire_turn - state.turn) if dec.status == "issued" else 0,
        })
    return {
        "total": len(active),
        "by_status": by_status,
        "available_types": [(k, v["effect_desc"], v["authority_cost"], v["valid_turns"])
                            for k, v in DECREE_TYPE_META.items()],
    }


# ── 派系系统（Step4新增）────────────────────────────────────────

@dataclass
class FactionInfluence:
    faction: str          # 派系名
    influence: int         # 影响力 0-100
    trend: str            # 趋势：rising / stable / declining
    key_members: List[str]  # 核心成员


FACTION_META: Dict[str, Dict] = {
    "忠汉派": {
        "color": "#22c55e",
        "description": "忠于汉室的大臣与诸侯",
        "goal": "兴复汉室，还政天子",
        "trigger_event": "衣带密诏",
    },
    "务实派": {
        "color": "#3b82f6",
        "description": "以实际利益为先的务实者",
        "goal": "保住实力，左右逢源",
        "trigger_event": "嘉奖诏书",
    },
    "离心派": {
        "color": "#f59e0b",
        "description": "有离心倾向但不公开叛逆",
        "goal": "积蓄实力，静观其变",
        "trigger_event": "威权低于30",
    },
    "叛逆派": {
        "color": "#ef4444",
        "description": "公开与汉室为敌",
        "goal": "取而代之",
        "trigger_event": "威权低于15",
    },
}


def get_faction_status(state: "GameState") -> Dict:
    """获取派系影响力状态。"""
    faction_data = state.metrics.get("faction_influence", {})
    result = {}
    for faction, meta in FACTION_META.items():
        inf = faction_data.get(faction, 20)
        trend = "stable"
        if inf > 40:
            trend = "rising"
        elif inf < 20:
            trend = "declining"
        result[faction] = {
            "influence": inf,
            "trend": trend,
            "color": meta["color"],
            "description": meta["description"],
        }
    return result


def init_faction_influence(state: "GameState") -> None:
    """初始化派系影响力（游戏开始时调用）。"""
    state.metrics["faction_influence"] = {
        "忠汉派": 25,
        "务实派": 30,
        "离心派": 30,
        "叛逆派": 15,
    }


def apply_faction_change(state: "GameState", faction: str, delta: int) -> None:
    """调整派系影响力。"""
    faction_data = state.metrics.get("faction_influence", {})
    if faction in faction_data:
        faction_data[faction] = max(0, min(100, faction_data[faction] + delta))
    else:
        faction_data[faction] = max(0, min(100, 20 + delta))
    state.metrics["faction_influence"] = faction_data


def apply_all_faction_dynamics(state: "GameState", db) -> Dict:
    """每回合应用派系动态：
    - 忠汉派：威权高则上升
    - 离心派：威权低则上升
    - 叛逆派：藩镇高则上升
    - 务实派：相对稳定
    """
    authority = state.metrics.get("威权", 0)
    fanzhen = state.metrics.get("藩镇", 80)
    faction_data = state.metrics.get("faction_influence", {})

    changes = {}
    if authority >= 50:
        changes["忠汉派"] = 3
        changes["离心派"] = -2
    elif authority <= 20:
        changes["忠汉派"] = -2
        changes["离心派"] = 3
    if fanzhen >= 80:
        changes["叛逆派"] = 2
    elif fanzhen <= 50:
        changes["叛逆派"] = -1
    # 务实派随稳定性变化
    changes["务实派"] = 0

    for faction, delta in changes.items():
        if faction in faction_data:
            faction_data[faction] = max(0, min(100, faction_data[faction] + delta))

    state.metrics["faction_influence"] = faction_data

    # 派系影响诏书效果
    decree_mult = 1.0
    if faction_data.get("忠汉派", 20) >= 50:
        decree_mult += 0.1
    if faction_data.get("离心派", 30) >= 50:
        decree_mult -= 0.1
    if faction_data.get("叛逆派", 15) >= 40:
        decree_mult -= 0.15

    return {"changes": changes, "decree_mult": decree_mult}


def get_dominant_faction(state: "GameState") -> str:
    """获取主导派系。"""
    faction_data = state.metrics.get("faction_influence", {})
    if not faction_data:
        return "务实派"
    return max(faction_data, key=lambda k: faction_data[k])


def adjust_faction_by_action(state: "GameState", action_type: str, target: str = "") -> None:
    """根据天子行动调整派系（行动反馈）。"""
    faction_data = state.metrics.get("faction_influence", {})
    if action_type == "issue_decree":
        # 发诏书：忠汉派+，离心派-
        apply_faction_change(state, "忠汉派", 2)
        apply_faction_change(state, "离心派", -1)
    elif action_type == "punish_loyal":
        # 惩罚忠臣：忠汉派-，离心派+
        apply_faction_change(state, "忠汉派", -3)
        apply_faction_change(state, "离心派", 2)
    elif action_type == "reward_loyal":
        # 嘉奖忠臣：忠汉派+
        apply_faction_change(state, "忠汉派", 2)
    elif action_type == "suppress_rebel":
        # 镇压叛逆：忠汉派+，叛逆派-
        apply_faction_change(state, "忠汉派", 2)
        apply_faction_change(state, "叛逆派", -2)
    state.metrics["faction_influence"] = faction_data


@dataclass
class ChatResult:
    action: str
    next_minister: str = ""
    refresh_ministers: List[str] = field(default_factory=list)


@dataclass
class LLMConfig:
    api_key: str
    base_url: str
    model: str
    max_tokens: int = 8000
    timeout_seconds: float = 180.0
    advanced_model: str = ""
    advanced_base_url: str = ""
    advanced_api_key: str = ""


@dataclass
class Character:
    name: str
    office: str
    office_type: str  # chancellor / general / minister / warlord / emperor
    faction: str
    aliases: List[str]
    personal_skills: List[str]
    loyalty: int
    ability: int
    integrity: int
    courage: int
    style: str
    power_id: str
    location: str = ""
    birth_year: int = 0
    historical_death_year: int = 0
    historical_death_month: int = 0
    debut_year: int = 0
    debut_month: int = 0
    status: str = "active"  # active | offstage | dismissed | imprisoned | exiled | retired | dead
    summary: str = ""
    portrait_id: str = ""


@dataclass
class Event:
    id: str
    title: str
    kind: str  # historical / threshold_crisis / random / emperor_action
    summary: str
    urgency: int
    severity: int
    credibility: int
    interests: List[str]
    audiences: List[str]
    resolve_condition: str = ""
    fail_condition: str = ""
    trigger_year: int = 0   # 历史锚定触发年（公历，0=非历史锚定）
    trigger_month: int = 0  # 1-12，0=年内任意月
    trigger_end_year: int = 0
    trigger_end_month: int = 0
    precondition: str = ""  # 触发前提人话说明
    event_type: str = "situation"  # situation / node / ending
    trigger_gate: Dict[str, str] = field(default_factory=dict)  # {metric: ">50"}
    trigger_condition: Dict[str, str] = field(default_factory=dict)  # 额外触发条件


@dataclass
class Faction:
    name: str
    satisfaction: int
    leverage: int
    agenda: str


@dataclass
class SocialClass:
    name: str            # 农民 / 士绅 / 官僚 / 军户 / 商人 / 匠户 / 宗藩
    region_id: str       # "" = 全国汇总
    population: int      # 万人
    satisfaction: int   # 0-100
    leverage: int       # 0-100
    agenda: str


@dataclass
class Region:
    id: str
    name: str
    kind: str  # capital / province / border
    population: int
    public_support: int
    unrest: int
    natural_disaster: str = ""
    human_disaster: str = ""
    registered_land: int = 0    # 万亩
    hidden_land: int = 0        # 万亩
    tax_per_turn: int = 0       # 万两/月
    grain_security: int = 0     # 0-100
    gentry_resistance: int = 0  # 0-100
    military_pressure: int = 0   # 0-100
    status: str = "ming"        # ming / warlord
    controlled_by: str = ""     # power_id
    fiscal: dict = field(default_factory=dict)  # 省级财政
    on_restore: dict = field(default_factory=dict)


@dataclass
class Army:
    id: str
    name: str
    station: str   # 驻扎地
    theater: str   # 战区
    commander: str
    controller: str  # power_id
    troop_type: str  # infantry / cavalry / navy / imperial
    manpower: int
    maintenance_per_turn: int  # 万两/月
    supply: int
    morale: int
    training: int
    equipment: int
    arrears: int
    mobility: int
    loyalty: int
    status: str  # active / garrison / destroyed
    owner_power: str


@dataclass
class Building:
    id: str
    region_id: str
    name: str
    category: str  # 财政 / 军事 / 民生 / 科技 / 交通 / 内廷
    level: int    # 1-5
    condition: int  # 完好 0-100
    maintenance: int  # 万两/月
    risk: int
    output_metric: str  # 汉室库 / 军备 / 声望
    output_amount: int
    status: str


@dataclass
class Power:
    id: str
    name: str
    kind: str  # empire / warlord / rebel
    leader: str
    stance: str  # loyal / neutral / hostile
    leverage: int
    satisfaction: int
    military_strength: int
    cohesion: int
    supply: int
    agenda: str
    status: str
    last_action: str = "尚无新动"
    aliases: str = ""


@dataclass
class GameState:
    year: int = 189
    period: int = 1
    turn: int = 1
    turn_phase: str = "summoning"  # summoning / reviewing / issued
    capital: str = "洛阳"          # 汉室当前都城
    metrics: Dict[str, int] = field(
        default_factory=lambda: {
            "汉室库": 200,    # 财政
            "内库": 100,     # 天子私房钱
            "声望": 30,      # 汉室民心
            "威权": 15,      # 天子威权（董卓入京后极低）
            "藩镇": 80,      # 藩镇割据程度
            "skill_points": 0,
        }
    )
    # 特殊历史线状态
    dong_zhuo_trapped_turn: int = 0   # 董卓被困回合（>0表示触发伏诛线）
    dong_zhuo_killed_turn: int = 0    # 董卓被诛回合（>0表示已伏诛）
    emperor_escaped_turn: int = 0     # 献帝出逃回合（>0表示触发东归线）
    emperor_safe_turn: int = 0        # 献帝抵达许昌回合（>0表示东归完成）
    log: List[str] = field(default_factory=list)

    def clamp(self) -> None:
        for key, value in list(self.metrics.items()):
            if key in ("汉室库", "内库"):
                self.metrics[key] = max(0, value)
            else:
                self.metrics[key] = max(0, min(100, value))

    def next_period(self) -> None:
        self.turn += 1
        self.period += 1
        if self.period > 12:
            self.period = 1
            self.year += 1


@dataclass
class CourtContext:
    state: GameState
    db: object
    previous_summary: str = ""


def period_label(year: int, month: int) -> str:
    return f"{year}年{month}月"


def monthly_amount(amount: int) -> int:
    return max(0, round(int(amount) / 3))


TURN_UNIT = "月"
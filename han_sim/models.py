"""数据类：游戏实体与状态容器。L0 叶子模块。"""



from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
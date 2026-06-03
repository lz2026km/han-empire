"""v2.1.0 Phase 6: 科举征辟 + 罢免流放系统

v2.0.0 已有 summon_minister (receive_minister API), 但缺:
- 月度科举 (5 题经义策论)
- 5 级官品 (从九品到正一品)
- 罢免/流放机制

被 server.py /api/campaigns/{id}/civil/* 调用
"""
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class Rank(str, Enum):
    """5 级官品 (从九品 → 正一品)"""
    RANK_9 = "从九品"   # 县丞
    RANK_8 = "正八品"   # 县令
    RANK_7 = "从七品"   # 州从事
    RANK_6 = "正六品"   # 郡守
    RANK_5 = "从五品"   # 太守
    RANK_4 = "正四品"   # 九卿
    RANK_3 = "从三品"   # 侍中
    RANK_2 = "正二品"   # 三公
    RANK_1 = "从一品"   # 大将军/丞相
    RANK_S = "正一品"   # 王/公


# 官品 → 俸禄 (汉制, 斛/月)
RANK_SALARY = {
    Rank.RANK_9: 30,
    Rank.RANK_8: 50,
    Rank.RANK_7: 80,
    Rank.RANK_6: 120,
    Rank.RANK_5: 180,
    Rank.RANK_4: 250,
    Rank.RANK_3: 350,
    Rank.RANK_2: 500,
    Rank.RANK_1: 700,
    Rank.RANK_S: 1000,
}

# 官品 → 月俸
RANK_AUTHORITY = {
    Rank.RANK_9: 5,
    Rank.RANK_8: 10,
    Rank.RANK_7: 20,
    Rank.RANK_6: 35,
    Rank.RANK_5: 50,
    Rank.RANK_4: 70,
    Rank.RANK_3: 90,
    Rank.RANK_2: 95,
    Rank.RANK_1: 99,
    Rank.RANK_S: 100,
}


# ════════════════════════════════════════════════════════════════
# 科举题库 (20 题, 5 科目)
# ════════════════════════════════════════════════════════════════

EXAM_QUESTIONS: List[Dict] = [
    # 尚书/经义
    {"subject": "尚书", "question": "何为'克明俊德'? 请阐述其义。", "answer": "克明俊德, 谓能明俊德之人, 任以官职。", "score": 10},
    {"subject": "尚书", "question": "'满招损, 谦受益' 出自何篇?", "answer": "《尚书·大禹谟》", "score": 10},
    {"subject": "尚书", "question": "何为'六府三事'?", "answer": "水火金木土谷 + 正德利用厚生。", "score": 15},
    # 诗经
    {"subject": "诗经", "question": "'关关雎鸠, 在河之洲' 出自何篇?", "answer": "《周南·关雎》", "score": 10},
    {"subject": "诗经", "question": "何为'风雅颂'?", "answer": "《国风》《小雅》《大雅》《颂》四类。", "score": 15},
    {"subject": "诗经", "question": "'窈窕淑女, 君子好逑' 何意?", "answer": "贤淑女子, 君子所求之佳偶。", "score": 10},
    # 春秋
    {"subject": "春秋", "question": "春秋三传为何?", "answer": "《左传》《公羊传》《谷梁传》", "score": 15},
    {"subject": "春秋", "question": "春秋笔法'微言大义' 何解?", "answer": "一字褒贬, 以言寓义。", "score": 20},
    {"subject": "春秋", "question": "何为'弑君三十六, 亡国五十二'?", "answer": "春秋 242 年间, 弑君事件统计, 言天下大乱。", "score": 20},
    # 论语
    {"subject": "论语", "question": "'学而时习之, 不亦说乎' 何解?", "answer": "学知识时常温习, 是很愉快的事。", "score": 10},
    {"subject": "论语", "question": "何为'己所不欲, 勿施于人'?", "answer": "自己不想要的事物, 不要强加于他人。", "score": 15},
    {"subject": "论语", "question": "'君子和而不同, 小人同而不和' 何意?", "answer": "君子讲和谐而不盲从, 小人盲从而不讲和谐。", "score": 20},
    # 策论
    {"subject": "策论", "question": "今黄巾四起, 何以安天下? 请策之。", "answer": "外修武备, 内施仁政, 任用贤良, 轻徭薄赋。", "score": 30},
    {"subject": "策论", "question": "今诸侯割据, 天子孱弱, 何以兴复汉室? 请策之。", "answer": "联结忠义, 罢黜奸佞, 收拢民心, 徐图恢复。", "score": 30},
    {"subject": "策论", "question": "今群臣结党, 派系纷争, 何以调和? 请策之。", "answer": "明赏罚, 严法度, 兼听则明, 偏信则暗。", "score": 30},
    {"subject": "策论", "question": "今百姓困苦, 赋役繁重, 何以苏息? 请策之。", "answer": "轻徭薄赋, 与民生息, 兴修水利, 鼓励农桑。", "score": 30},
    {"subject": "策论", "question": "今外戚专权, 后宫干政, 何以防之? 请策之。", "answer": "明君臣之义, 定内外之防, 选贤任能, 严内外官制。", "score": 30},
    {"subject": "策论", "question": "今宦官乱政, 何以清君侧? 请策之。", "answer": "徐图之, 不可操切, 待时而动, 一击必中。", "score": 30},
    {"subject": "策论", "question": "今边疆不宁, 匈奴寇边, 何以御之? 请策之。", "answer": "修武备, 屯田戍边, 羁縻并举, 和战兼用。", "score": 30},
    {"subject": "策论", "question": "今豪强兼并, 土地不均, 何以均之? 请策之。", "answer": "限田限奴, 抑制兼并, 鼓励垦荒, 轻徭薄赋。", "score": 30},
]


# ════════════════════════════════════════════════════════════════
# 科举
# ════════════════════════════════════════════════════════════════

@dataclass
class ExamResult:
    """科举结果"""
    candidate_name: str
    exam_year: int
    exam_month: int
    score: int            # 总分 0-100
    subject_scores: Dict[str, int]
    promoted: bool        # 是否录取
    narrative: str
    rank: Optional[Rank] = None   # 落第时为 None

    def to_dict(self):
        return {
            "candidate_name": self.candidate_name,
            "exam_year": self.exam_year,
            "exam_month": self.exam_month,
            "score": self.score,
            "subject_scores": self.subject_scores,
            "rank": self.rank.value if self.rank else None,
            "promoted": self.promoted,
            "narrative": self.narrative,
        }


def hold_exam(candidate_name: str, year: int, month: int, intelligence: int = 50) -> ExamResult:
    """举行科举 (5 题经义 + 1 题策论)

    Args:
        candidate_name: 应试者姓名
        year: 年份
        month: 月份
        intelligence: 应试者智力 0-100 (影响答题)

    Returns:
        ExamResult
    """
    # 抽 5 题 (4 经义 + 1 策论)
    jingyi = [q for q in EXAM_QUESTIONS if q["subject"] != "策论"]
    celun = [q for q in EXAM_QUESTIONS if q["subject"] == "策论"]

    chosen = random.sample(jingyi, 4) + random.sample(celun, 1)
    subject_scores = {}
    total = 0

    for q in chosen:
        # 智力 + 运气 决定得分
        base = random.randint(0, q["score"])
        intel_bonus = int((intelligence - 50) * 0.4)  # -20~+20
        score = max(0, min(q["score"], base + intel_bonus))
        subject_scores[q["subject"]] = score
        total += score

    # 总分 100 (5 题, 最高 10+10+10+10+30=70, 但平均 60, 满分 100 设计)
    # 实际: 经义 4 题 (40分) + 策论 1 题 (30分) = 70 满分
    # 调整为 100 满分: 每题 20 分
    total = min(100, int(total * 100 / 70))

    # 授官 (60分以下落第, 60-70 授从九品, 70-80 正八品, 80-90 从七品, 90+ 正六品以上)
    if total < 60:
        rank = None
        promoted = False
        narrative = f"{candidate_name} 科举落第, 未能中榜。"
    else:
        promoted = True
        if total < 70:
            rank = Rank.RANK_9
        elif total < 80:
            rank = Rank.RANK_8
        elif total < 90:
            rank = Rank.RANK_7
        elif total < 95:
            rank = Rank.RANK_6
        elif total < 98:
            rank = Rank.RANK_5
        else:
            rank = Rank.RANK_4
        narrative = f"{candidate_name} 高中第 {total} 分, 授{rank.value}!"

    return ExamResult(
        candidate_name=candidate_name,
        exam_year=year,
        exam_month=month,
        score=total,
        subject_scores=subject_scores,
        rank=rank,
        promoted=promoted,
        narrative=narrative,
    )


# ════════════════════════════════════════════════════════════════
# 5 级官品 + 征辟
# ════════════════════════════════════════════════════════════════

@dataclass
class Official:
    """官员 (含官品)"""
    name: str
    rank: Rank
    appointed_year: int
    appointed_month: int
    salary: int
    authority_bonus: int

    def to_dict(self):
        return {
            "name": self.name,
            "rank": self.rank.value,
            "appointed_year": self.appointed_year,
            "appointed_month": self.appointed_month,
            "salary": self.salary,
            "authority_bonus": self.authority_bonus,
        }


def appoint_minister(name: str, rank: Rank, year: int, month: int) -> Official:
    """征辟大臣 (授官)

    Args:
        name: 大臣名
        rank: 官品 (从九品到正一品)
        year: 任命年
        month: 任命月

    Returns:
        Official
    """
    return Official(
        name=name,
        rank=rank,
        appointed_year=year,
        appointed_month=month,
        salary=RANK_SALARY[rank],
        authority_bonus=RANK_AUTHORITY[rank],
    )


# ════════════════════════════════════════════════════════════════
# 罢免 / 流放
# ════════════════════════════════════════════════════════════════

@dataclass
class DismissResult:
    """罢免/流放结果"""
    name: str
    action: str            # "罢免" / "流放"
    year: int
    month: int
    location: str          # 流放地点
    reason: str
    faction_impact: Dict[str, int]   # 派系影响
    narrative: str

    def to_dict(self):
        return {
            "name": self.name,
            "action": self.action,
            "year": self.year,
            "month": self.month,
            "location": self.location,
            "reason": self.reason,
            "faction_impact": self.faction_impact,
            "narrative": self.narrative,
        }


EXILE_LOCATIONS = [
    "永昌郡(云南)", "交趾(越南)", "日南(越南中部)", "合浦(广西)",
    "南海(广东)", "苍梧(广西)", "九真(越南)", "郁林(广西)",
]


def dismiss_minister(name: str, reason: str, year: int, month: int, faction: str = "忠汉派") -> DismissResult:
    """罢免大臣 (不流放, 仅免职)"""
    impact = {faction: -10}
    narrative = f"{name} 因{reason}, 被罢免官职, 削为民。"
    return DismissResult(
        name=name,
        action="罢免",
        year=year,
        month=month,
        location="本乡",
        reason=reason,
        faction_impact=impact,
        narrative=narrative,
    )


def exile_minister(name: str, reason: str, year: int, month: int, faction: str = "叛逆派") -> DismissResult:
    """流放大臣"""
    location = random.choice(EXILE_LOCATIONS)
    impact = {faction: -30}
    narrative = f"{name} 因{reason}, 被流放至{location}, 永不录用。"
    return DismissResult(
        name=name,
        action="流放",
        year=year,
        month=month,
        location=location,
        reason=reason,
        faction_impact=impact,
        narrative=narrative,
    )


def list_exam_subjects() -> List[str]:
    """返回科举科目"""
    return ["尚书", "诗经", "春秋", "论语", "策论"]


def list_ranks() -> List[Dict]:
    """返回 5 级官品"""
    return [
        {"rank": r.value, "salary": RANK_SALARY[r], "authority": RANK_AUTHORITY[r]}
        for r in Rank
    ]

"""天子日记生成器。L4。

模板型日记生成器，调用 db.write_diary() 持久化。
结构：10岁月感慨 + 7威权评语 + 10大臣评语 + 10月度大事
"""

from dataclasses import dataclass
from typing import Dict, List, TYPE_CHECKING
import random

if TYPE_CHECKING:
    from han_sim.db import GameDB

AGE_REFLECTIONS = {
    "少年": [
        "朕自即位以来，深感天下之事千头万绪，非稚嫩之心所能独理。",
        "十年光阴，朕尚未及冠，却已肩负兆民之托。",
        "朕虽年幼，亦知祖宗基业不可轻弃，当效文景之治。",
    ],
    "青年": [
        "朕自亲政以来，朝乾夕惕，未敢有一日之懈。",
        "朕观朝堂之上，大臣各怀心思，朕当以威权驾驭之。",
        "朕值盛年，正当振作朝纲，使汉室再兴。",
    ],
    "中年": [
        "朕临天下愈久，知天命之不可违，人事之当尽。",
        "朕为政多年，深感权柄之重，威权不立则号令不行。",
        "朕中年思虑日深，深知汉室兴亡在此一举。",
    ],
    "老年": [
        "朕御极日久，白发渐生，深感时日无多，唯愿汉室长存。",
        "朕年迈体衰，然天下未定，不敢言退。",
        "朕风烛残年，唯望继任者能守成勿失。",
    ],
}

AUTHORITY_COMMENTS = {
    "形同虚设": [
        "朕诏令不出宫门，形同虚设，此朕最痛心之事。",
        "今日之局，朕虽有天子之名，实无天子之实，悲哉。",
    ],
    "权臣操弄": [
        "朕诏令受阻于权臣，进退两难，朕心忧惧。",
        "权臣把持朝政，朕欲兴复汉室而不可得。",
    ],
    "阳奉阴违": [
        "朕诏令虽下，然大臣多不奉行，朕深为焦虑。",
        "朕观群臣表面顺从，内心实有异志，朕心寒之。",
    ],
    "勉强维持": [
        "朕以有限之威权，勉强维持朝局，不敢懈怠。",
        "朕深感维持现状之难，日夜操劳不敢言功。",
    ],
    "诏书有效": [
        "朕之诏令渐能通达天下，威权日盛，朕心稍安。",
        "朕的威权稳步提升，诏书渐有效力，朕甚慰之。",
    ],
    "号令四方": [
        "朕威权日隆，四方诸侯渐知敬畏，朕心甚慰。",
        "朕号令所至，四方响应，此帝王之盛也。",
    ],
    "至高无上": [
        "朕今日威权至极，四海之内莫非王土，朕心澎湃。",
        "朕威权无上，然盛极必衰，朕当戒之。",
    ],
}

MINISTER_COMMENTS = {
    "忠诚耿介": ["卿忠诚耿介，朕心甚慰，当善加保全。", "卿为朕股肱，忠心可鉴。"],
    "干练有才": ["卿才干卓越，朕每有疑难，多赖卿决断。", "卿干练有为，朕当重用。"],
    "中正守法": ["卿中正守法，朕所素知，当使卿掌纠弹之任。", "卿守正不阿，朕深重之。"],
    "勇猛敢言": ["卿勇于任事，朕甚嘉之。", "卿胆略俱佳，朕深赖之。"],
    "首鼠两端": ["卿态度暧昧，首鼠两端，朕甚为忧之。", "卿立场不坚，朕深不取之。"],
    "贪婪无厌": ["卿贪婪无厌，朕深恶之，当加以惩诫。", "卿欲壑难填，朕深忧之。"],
    "结党营私": ["卿结党营私，朕深恶之，当察其朋党。", "卿树党自重，朕甚为忧虑。"],
    "老成谋国": ["卿老成谋国，朕深重之。", "卿阅世既深，谋议皆中，朕每倚之。"],
    "年富力强": ["卿年富力强，朕深期之。", "卿春秋正盛，当勉力报国。"],
    "平庸无奇": ["卿才具平平，朕当观其后效。", "卿能力中庸，朕不深望之。"],
}

MONTHLY_EVENTS = {
    "财政": ["汉室库出入相抵，朕深感开源节流之必要。", "财政紧张，朕思量对策，不敢轻启耗用。"],
    "军事": ["边关急报，朕已令将出兵讨伐。", "军备充实，朕心稍安，然不可大意。"],
    "政治": ["朕策试贤良，深感人才之重要。", "百官朝贺，朕恩赐有差，以励臣工。"],
    "外交": ["藩镇来使，朕以羁縻之术待之。", "朕闻藩镇有不臣之心，已密令察查。"],
    "民生": ["朕闻南阳郡有旱情，已令有司开仓赈济。", "朕亲耕籍田，以示重农之意。"],
    "宗室": ["朕宗室之中有人不安分，朕已切责之。", "朕感念宗室旧恩，已加赐封赏。"],
    "后妃": ["朕之后宫和睦，朕心甚慰。", "朕有感于后宫之事，深感为君之不易。"],
    "文化": ["朕令太学增补儒生，以振文教。", "朕感于斯文之将坠，深感责任重大。"],
    "天象": ["朕夜观天象，见荧惑守心，深感忧虑。", "近日甘露降于京畿，朕以为是祥瑞。"],
    "祭祀": ["朕今日祭祀天地，以祈国泰民安。", "朕亲祭祖庙，以尽孝道。"],
}


def age_bucket(age: int) -> str:
    if age < 15:
        return "少年"
    if age < 25:
        return "青年"
    if age < 40:
        return "中年"
    return "老年"


@dataclass
class DiaryEntry:
    year: int
    period: int
    turn: int
    age_reflection: str
    authority_comment: str
    minister_comments: List[str]
    monthly_events: List[str]


class EmperorDiaryGenerator:
    def __init__(self, db: "GameDB"):
        self.db = db

    def generate(self, year: int, period: int, turn: int, emperor_age: int) -> DiaryEntry:
        ab = age_bucket(emperor_age)
        ref = random.choice(AGE_REFLECTIONS.get(ab, AGE_REFLECTIONS["青年"]))
        auth = self._authority_bucket()
        auth_cmt = random.choice(AUTHORITY_COMMENTS[auth])
        m_comments = self._sample_ministers()
        events = self._sample_events()
        return DiaryEntry(year, period, turn, ref, auth_cmt, m_comments, events)

    def _authority_bucket(self) -> str:
        try:
            row = self.db.conn.execute("SELECT value FROM metrics WHERE key='威权'").fetchone()
            v = int(row["value"]) if row else 0
        except Exception:
            v = 0
        if v < 20:
            return "形同虚设"
        if v < 30:
            return "权臣操弄"
        if v < 50:
            return "阳奉阴违"
        if v < 60:
            return "勉强维持"
        if v < 75:
            return "诏书有效"
        if v < 90:
            return "号令四方"
        return "至高无上"

    def _sample_ministers(self) -> List[str]:
        try:
            rows = self.db.conn.execute(
                "SELECT name, loyalty, ability, integrity, courage, faction "
                "FROM characters WHERE status='active' LIMIT 9"
            ).fetchall()
            chars = [dict(r) for r in rows]
            random.shuffle(chars)
            return [f"【{c['name']}】{self._judge(c)}" for c in chars[:3]]
        except Exception:
            return []

    def _judge(self, ch: Dict) -> str:
        L, A, I, C, F = (ch.get(k, 50) for k in ("loyalty", "ability", "integrity", "courage", "faction"))
        if L >= 80 and I >= 70:
            b = "忠诚耿介"
        elif A >= 70 and L >= 60:
            b = "干练有才"
        elif I >= 70 and L >= 50:
            b = "中正守法"
        elif C >= 70 and L >= 40:
            b = "勇猛敢言"
        elif L < 30:
            b = "首鼠两端"
        elif A >= 60 and L < 40:
            b = "贪婪无厌"
        elif F not in ("中立", "") and L < 50:
            b = "结党营私"
        elif I >= 60 and L >= 70:
            b = "老成谋国"
        elif A >= 50 and L >= 50:
            b = "年富力强"
        else:
            b = "平庸无奇"
        return random.choice(MINISTER_COMMENTS[b])

    def _sample_events(self) -> List[str]:
        cats = list(MONTHLY_EVENTS.keys())
        return [random.choice(MONTHLY_EVENTS[random.choice(cats)]) for _ in range(3)]

    def format_diary(self, e: DiaryEntry) -> str:
        lines = [
            "",
            "═" * 52,
            f"  《天子日记》  {e.year}年{e.period}月  第{e.turn}回合",
            "═" * 52,
            "",
            "  ◆ 岁月感慨",
            f"  {e.age_reflection}",
            "",
            "  ◆ 威权评语",
            f"  {e.authority_comment}",
            "",
        ]
        if e.minister_comments:
            lines.append("  ◆ 大臣评语")
            lines.extend(f"  {mc}" for mc in e.minister_comments)
            lines.append("")
        if e.monthly_events:
            lines.append("  ◆ 月度大事")
            lines.extend(f"  {me}" for me in e.monthly_events)
            lines.append("")
        lines.append("─" * 52)
        return "\n".join(lines)

    def write_diary(self, e: DiaryEntry) -> None:
        text = self.format_diary(e)
        try:
            self.db.conn.execute(
                "INSERT OR REPLACE INTO turn_reports (turn, year, period, report, created_at) "
                "VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                (e.turn, e.year, e.period, text),
            )
            self.db.conn.commit()
        except Exception:
            self.db.conn.execute(
                "INSERT OR REPLACE INTO kv_store (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (f"diary_{e.turn}", text),
            )
            self.db.conn.commit()

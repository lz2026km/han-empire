"""v2.1.0 Phase 7: 春秋史册 + 时间轴系统

汉献帝视角的"史官实录":
- 时间轴: 公元前 184-280 年的黄巾之乱 → 晋朝统一
- 重大事件: 衣带诏/官渡/赤壁/夷陵/禅让
- 史官评语: 4 史官立场 (司马/班/范/陈)
- 月度/年度: 自动记录游戏事件

被 server.py /api/chronicle/* 调用
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
import random


# ════════════════════════════════════════════════════════════════
# 4 史官立场
# ════════════════════════════════════════════════════════════════

class Historian(str, Enum):
    """4 史官: 不同立场, 评语不同"""
    SIMA = "司马氏"          # 官方立场, 偏曹魏
    BAN = "班氏"            # 汉室立场, 偏忠汉
    FAN = "范氏"            # 道德立场, 中立
    CHEN = "陈氏"            # 百姓立场, 偏民生


HISTORIAN_STANCES: Dict[str, str] = {
    "司马氏": "以魏晋正统自居, 视汉为前朝。",
    "班氏": "以汉室忠臣自居, 视魏为篡逆。",
    "范氏": "以道德春秋为纲, 客观记述。",
    "陈氏": "以百姓疾苦为念, 关注民生。",
}


# ════════════════════════════════════════════════════════════════
# 重大历史事件 (公元 184-280)
# ════════════════════════════════════════════════════════════════

@dataclass
class HistoricalEvent:
    """重大历史事件"""
    year: int
    month: int
    title: str
    description: str
    significance: str     # 历史意义
    factions: List[str]   # 涉及派系
    tags: List[str]       # 标签: 战役/政变/天灾 等

    def to_dict(self):
        return {
            "year": self.year,
            "month": self.month,
            "title": self.title,
            "description": self.description,
            "significance": self.significance,
            "factions": self.factions,
            "tags": self.tags,
        }


HISTORICAL_EVENTS: List[HistoricalEvent] = [
    HistoricalEvent(184, 4, "黄巾起义", "张角率黄巾军起义, 天下大乱。", "东汉末年群雄并起之始", ["叛逆派"], ["民变", "起义"]),
    HistoricalEvent(189, 4, "少帝即位", "少帝刘辩即位, 何进掌权。", "外戚与宦官之争白热化", ["离心派"], ["政变"]),
    HistoricalEvent(189, 9, "董卓进京", "董卓率西凉军入洛阳, 废少帝立献帝。", "东汉政权名存实亡", ["叛逆派"], ["政变", "废立"]),
    HistoricalEvent(190, 1, "关东联军", "袁绍等 18 路诸侯讨伐董卓。", "群雄正式登场", ["忠汉派", "务实派"], ["军事"]),
    HistoricalEvent(196, 6, "迎献帝许都", "曹操迎献帝都许, 挟天子以令诸侯。", "汉室衰微的开端", ["务实派"], ["政变"]),
    HistoricalEvent(200, 10, "官渡之战", "曹操以寡敌众, 大破袁绍。", "北方一统奠基", ["务实派", "离心派"], ["战役"]),
    HistoricalEvent(208, 11, "赤壁之战", "孙刘联军火攻破曹, 三国鼎立。", "三分天下格局形成", ["忠汉派", "务实派", "离心派"], ["战役", "转折"]),
    HistoricalEvent(220, 10, "曹丕代汉", "曹丕篡汉称帝, 国号魏。", "东汉灭亡", ["叛逆派"], ["禅让", "篡逆"]),
    HistoricalEvent(221, 4, "刘备称帝", "刘备于成都称帝, 国号汉。", "蜀汉建立", ["忠汉派"], ["称帝"]),
    HistoricalEvent(222, 7, "夷陵之战", "刘备伐吴, 兵败夷陵。", "蜀汉国力大损", ["忠汉派", "务实派"], ["战役"]),
    HistoricalEvent(263, 11, "蜀汉灭亡", "邓艾钟会伐蜀, 刘禅降魏。", "三国归一", ["叛逆派"], ["灭国"]),
    HistoricalEvent(265, 12, "司马代魏", "司马炎篡魏, 国号晋。", "晋朝建立", ["叛逆派"], ["禅让"]),
    HistoricalEvent(280, 3, "晋灭东吴", "晋军南下, 孙皓降, 三国归晋。", "天下重归一统", ["叛逆派"], ["灭国", "统一"]),
]


def list_historical_events(year_min: int = 184, year_max: int = 280) -> List[Dict]:
    """列出历史事件 (按时间排序)"""
    return [e.to_dict() for e in HISTORICAL_EVENTS if year_min <= e.year <= year_max]


# ════════════════════════════════════════════════════════════════
# 时间轴
# ════════════════════════════════════════════════════════════════

def get_timeline(year_min: int = 184, year_max: int = 280) -> List[Dict]:
    """生成时间轴 (按年分组)"""
    by_year: Dict[int, List[Dict]] = {}
    for e in HISTORICAL_EVENTS:
        if year_min <= e.year <= year_max:
            by_year.setdefault(e.year, []).append(e.to_dict())

    timeline = []
    for year in sorted(by_year.keys()):
        events = sorted(by_year[year], key=lambda x: x["month"])
        timeline.append({
            "year": year,
            "events": events,
            "event_count": len(events),
        })
    return timeline


# ════════════════════════════════════════════════════════════════
# 史官评语
# ════════════════════════════════════════════════════════════════

def generate_historian_comment(event_year: int, event_title: str, historian: str) -> str:
    """史官评语: 4 史官对同一事件不同立场"""
    comments = {
        "司马氏": {
            "黄巾起义": "张角以妖术惑众, 罪在惑乱天下。",
            "曹丕代汉": "汉祚已衰, 魏承天受命, 理所当然。",
            "司马代魏": "魏祚已终, 晋受禅让, 顺天应人。",
            "蜀汉灭亡": "蜀汉偏安, 自取灭亡, 何足道哉。",
        },
        "班氏": {
            "黄巾起义": "张角举义, 实因朝廷昏聩, 百姓苦秦久矣。",
            "曹丕代汉": "曹丕篡汉, 天下共愤, 乱臣贼子人人得而诛之。",
            "司马代魏": "司马氏父子专权, 行篡逆之事, 天理不容。",
            "蜀汉灭亡": "汉室虽亡, 然血脉不断, 终有复兴之望。",
        },
        "范氏": {
            "黄巾起义": "黄巾之乱, 朝廷之过也, 非张角之罪。",
            "曹丕代汉": "曹氏三代经营, 至此收网, 虽曰篡逆, 实乃时势。",
            "司马代魏": "司马氏行篡逆, 虽成于一时, 必败于后世。",
            "蜀汉灭亡": "蜀汉以一州抗九州, 能延命四十余年, 诸葛孔明之力也。",
        },
        "陈氏": {
            "黄巾起义": "百姓何辜, 沦为沟壑? 苍生之苦, 始于黄巾。",
            "曹丕代汉": "改朝换代, 苦的是天下百姓, 兴亡皆是百姓苦。",
            "司马代魏": "司马氏内斗, 八王之乱, 百姓之祸始于此。",
            "蜀汉灭亡": "蜀中百姓得刘禅庇护, 终免屠城之灾, 幸甚。",
        },
    }

    historian_comments = comments.get(historian, {})
    return historian_comments.get(event_title, f"{historian} 史官评: {event_title} 于 {event_year} 年发生, 其意深远。")


# ════════════════════════════════════════════════════════════════
# 游戏事件记录
# ════════════════════════════════════════════════════════════════

@dataclass
class GameEvent:
    """游戏内事件记录"""
    year: int
    month: int
    event_type: str       # 诏书/战役/议事/科举
    title: str
    description: str
    impact: Dict[str, int]
    source: str = "player"   # player / npc / system

    def to_dict(self):
        return {
            "year": self.year,
            "month": self.month,
            "event_type": self.event_type,
            "title": self.title,
            "description": self.description,
            "impact": self.impact,
            "source": self.source,
        }


def record_event(year: int, month: int, event_type: str, title: str,
                  description: str, impact: Optional[Dict[str, int]] = None,
                  source: str = "player") -> GameEvent:
    """记录游戏事件到史记"""
    return GameEvent(
        year=year,
        month=month,
        event_type=event_type,
        title=title,
        description=description,
        impact=impact or {},
        source=source,
    )


# ════════════════════════════════════════════════════════════════
# 检索
# ════════════════════════════════════════════════════════════════

def search_chronicle(keyword: str, events: List[GameEvent]) -> List[Dict]:
    """检索史记"""
    if not keyword:
        return [e.to_dict() for e in events]
    keyword_lower = keyword.lower()
    results = []
    for e in events:
        if (keyword_lower in e.title.lower() or
            keyword_lower in e.description.lower() or
            keyword_lower in e.event_type.lower() or
            keyword_lower in str(e.year)):
            results.append(e.to_dict())
    return results

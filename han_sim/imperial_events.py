"""v2.2.0 终极版 P0-2: 事件 4 维+6 类模型 (借鉴明末 events.md)

设计: 每月 2-5 条关键事件, 每事件 4 维评分 (紧急/严重/可信/牵涉)
6 类: 朝政/财政/军事/地方/人物/科技

事件 → 触发奏报 → 主公决策 → 旨意 → 回奏
"""
import json
import random
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

# 6 类事件模板
EVENT_TEMPLATES = {
    "朝政": [
        {"title": "弹劾风波", "desc": "御史弹劾 {target} 徇私枉法, 主公应早做定夺", "urgency": 7, "severity": 6},
        {"title": "党争再起", "desc": "{faction_a} 与 {faction_b} 于朝堂争执, 互不相让", "urgency": 5, "severity": 7},
        {"title": "清算请奏", "desc": "{target} 旧案被翻, 请求主公复查", "urgency": 4, "severity": 8},
        {"title": "请辞入京", "desc": "{target} 以病请辞, 朝中震动", "urgency": 3, "severity": 5},
        {"title": "廷议之争", "desc": "关于 {topic}, 朝臣分为两派, 请主公裁决", "urgency": 6, "severity": 6},
    ],
    "财政": [
        {"title": "国库亏空", "desc": "国库告急, 较上月短 {amount} 万两, 急需拨付", "urgency": 9, "severity": 9},
        {"title": "加派奏请", "desc": "{region} 请加派辽饷, 民怨沸腾", "urgency": 6, "severity": 7},
        {"title": "抄没入官", "desc": "查抄 {target} 家产, 得银 {amount} 万两", "urgency": 4, "severity": 5},
        {"title": "借款外使", "desc": "与 {faction} 借款 {amount} 万两, 利息甚重", "urgency": 5, "severity": 6},
        {"title": "盐政腐败", "desc": "{region} 盐政崩坏, 私盐横行", "urgency": 5, "severity": 6},
    ],
    "军事": [
        {"title": "边警告急", "desc": "{region} 守将飞报: 敌兵压境, 请速发援军", "urgency": 10, "severity": 9},
        {"title": "欠饷哗变", "desc": "{army} 军士因欠饷哗变, 形势危急", "urgency": 9, "severity": 8},
        {"title": "战役报捷", "desc": "{general} 于 {region} 大破敌军, 斩首 {amount}", "urgency": 3, "severity": 3},
        {"title": "将帅争功", "desc": "{general_a} 与 {general_b} 互相争功, 请主公裁断", "urgency": 5, "severity": 5},
        {"title": "军需告急", "desc": "{army} 粮草仅余 {amount} 日, 急需补运", "urgency": 8, "severity": 8},
    ],
    "地方": [
        {"title": "灾荒告急", "desc": "{region} 大旱, 流民四起, 急需赈济", "urgency": 8, "severity": 9},
        {"title": "粮价飞涨", "desc": "{region} 粮价较上月涨 {amount}%, 民不聊生", "urgency": 6, "severity": 7},
        {"title": "逃户激增", "desc": "{region} 逃户激增 {amount} 户, 税基萎缩", "urgency": 5, "severity": 6},
        {"title": "盗匪蜂起", "desc": "{region} 山匪出没, 商旅断绝", "urgency": 6, "severity": 6},
        {"title": "士绅请愿", "desc": "{region} 士绅联名上书, 请减免税赋", "urgency": 4, "severity": 5},
    ],
    "人物": [
        {"title": "求见密奏", "desc": "{target} 求见主公, 密陈国事", "urgency": 5, "severity": 5},
        {"title": "请辞致仕", "desc": "{target} 年迈请辞, 请主公恩准", "urgency": 3, "severity": 4},
        {"title": "病亡噩耗", "desc": "{target} 因病亡故, 朝中失一柱石", "urgency": 4, "severity": 6},
        {"title": "密谋背叛", "desc": "据报 {target} 暗通 {faction}, 请主公明察", "urgency": 7, "severity": 9},
        {"title": "举荐贤才", "desc": "{target} 举荐 {candidate} 可任要职", "urgency": 4, "severity": 4},
    ],
    "科技": [
        {"title": "火器试验", "desc": "{expert} 试验新型火器, 成功/失败参半", "urgency": 3, "severity": 5},
        {"title": "保守派攻讦", "desc": "{faction} 攻讦新法异端, 朝中大哗", "urgency": 5, "severity": 6},
        {"title": "推广受阻", "desc": "新政于 {region} 推行受挫, 士绅阻挠", "urgency": 5, "severity": 6},
        {"title": "事故频发", "desc": "{project} 试验事故, 死伤 {amount} 人", "urgency": 7, "severity": 7},
        {"title": "西洋新知", "desc": "{missionary} 携西洋新知入京, 主公宜接见", "urgency": 3, "severity": 4},
    ],
}

# 上下文池 (用于占位)
FACTIONS = ["士族", "宦官", "外戚", "清流", "边将", "豪强", "豪商"]
REGIONS = ["冀州", "兖州", "豫州", "徐州", "青州", "荆州", "扬州", "益州", "并州", "凉州", "幽州", "司隶"]
TARGETS = ["王允", "蔡邕", "卢植", "郑玄", "何进", "张让", "袁绍", "袁术", "曹操", "刘表", "孙坚", "公孙瓒", "马腾", "韩遂"]
GENERALS = ["皇甫嵩", "朱儁", "卢植", "曹操", "袁绍", "孙坚", "刘表", "公孙瓒", "张纯", "张举"]
ARMIES = ["北军五校", "羽林军", "虎贲军", "西园军", "边军", "郡国兵"]


@dataclass
class ImperialEvent:
    id: int
    campaign_id: str
    category: str   # 6 类
    title: str
    description: str
    urgency: int     # 1-10
    severity: int    # 1-10
    credibility: int # 1-10
    stake: List[str] # 牵涉利益
    turn: int
    status: str      # 未处理/已读/已下旨/已回奏/逾期
    response_directive_id: int

    def to_dict(self) -> Dict:
        return asdict(self)

    @property
    def priority_score(self) -> float:
        """紧急+严重+可信 加权, 用于排序"""
        return self.urgency * 0.4 + self.severity * 0.4 + self.credibility * 0.2

    def to_memorial(self) -> Dict:
        """事件 → 奏报 (P0-3)"""
        urgency_to_memorial_type = {
            9: "紧急奏", 10: "紧急奏",
            7: "密奏", 8: "密奏",
        }
        m_type = "月奏"
        if self.urgency >= 7:
            m_type = "紧急奏" if self.urgency >= 9 else "密奏"
        return {
            "memorial_type": m_type,
            "from_official": "尚书" if self.category in ["财政", "军事"] else "御史",
            "title": f"【{self.category}】{self.title}",
            "content": self.description,
            "is_urgent": 1 if self.urgency >= 8 else 0,
            "is_secret": 1 if self.urgency >= 7 and self.urgency < 9 else 0,
            "event_id": self.id,
            "suggested_directive": self._suggest_directive(),
        }

    def _suggest_directive(self) -> Dict:
        """事件 → 建议旨意 9 维"""
        s = {
            "target": self.title,
            "executor": "",
            "scope": "全国" if self.severity >= 7 else "京畿",
            "resources": {},
            "deadline_turns": 2 if self.urgency >= 8 else 5,
            "authority_level": "圣旨" if self.severity >= 7 else "谕旨",
            "incentive": [],
            "constraints": ["不得扰民"] if self.category == "地方" else [],
            "publicity": "明发天下" if self.severity >= 6 else "只给部院",
            "interest_impact": self.stake,
        }
        if self.category == "财政":
            s["resources"] = {"silver": self.severity * 10}
        elif self.category == "军事":
            s["resources"] = {"troops": self.severity * 500, "grain": self.severity * 5}
        elif self.category == "地方":
            s["resources"] = {"silver": self.severity * 5, "grain": self.severity * 3}
        return s


def generate_monthly_events(
    db,
    campaign_id: str,
    turn: int,
    state: Optional[Dict] = None,
    rng: Optional[random.Random] = None,
) -> List[ImperialEvent]:
    """每月生成 2-5 条关键事件 (借鉴明末 events.md)"""
    rng = rng or random.Random()
    n = rng.randint(2, 5)
    events = []
    categories = list(EVENT_TEMPLATES.keys())
    state_d = state or {}

    # 抽取当前可用上下文
    factions = state_d.get("factions", FACTIONS)
    regions = state_d.get("regions", REGIONS)
    targets = state_d.get("targets", TARGETS)
    generals = state_d.get("generals", GENERALS)
    armies = state_d.get("armies", ARMIES)

    for _ in range(n):
        cat = rng.choice(categories)
        template = rng.choice(EVENT_TEMPLATES[cat])
        # 替换占位符
        title = template["title"]
        desc = template["desc"]
        for k, pool in [
            ("{target}", targets),
            ("{faction_a}", factions),
            ("{faction_b}", factions),
            ("{faction}", factions),
            ("{region}", regions),
            ("{general}", generals),
            ("{general_a}", generals),
            ("{general_b}", generals),
            ("{army}", armies),
            ("{expert}", targets),
            ("{missionary}", targets),
            ("{project}", ["新法", "火器", "水车", "历法"]),
            ("{candidate}", targets),
            ("{topic}", ["盐政", "军制", "田亩", "选举", "边防"]),
        ]:
            while k in title:
                title = title.replace(k, rng.choice(pool), 1)
            while k in desc:
                desc = desc.replace(k, rng.choice(pool), 1)
        # 替换 {amount}
        import re
        desc = re.sub(r'\{amount\}', str(rng.randint(5, 500)), desc)

        # 4 维评分: 紧急/严重 (从模板) + 可信随机 + 偏差
        urgency = max(1, min(10, template["urgency"] + rng.randint(-1, 1)))
        severity = max(1, min(10, template["severity"] + rng.randint(-1, 1)))
        credibility = rng.randint(4, 9)  # 奏报真实度随机

        # 牵涉利益
        stake = []
        if "{faction_a}" in template["desc"] or "{faction_b}" in template["desc"]:
            stake = rng.sample(factions, min(2, len(factions)))
        elif "{region}" in template["desc"]:
            stake = [rng.choice(regions)]
        elif "{target}" in template["desc"]:
            stake = [rng.choice(targets)]

        ev = ImperialEvent(
            id=0,  # INSERT 后回填
            campaign_id=campaign_id,
            category=cat,
            title=title,
            description=desc,
            urgency=urgency,
            severity=severity,
            credibility=credibility,
            stake=stake,
            turn=turn,
            status="未处理",
            response_directive_id=0,
        )
        # 写库
        cur = db.conn.execute(
            """INSERT INTO imperial_events
            (campaign_id, category, title, description, urgency, severity, credibility,
             stake, turn, status, response_directive_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (ev.campaign_id, ev.category, ev.title, ev.description,
             ev.urgency, ev.severity, ev.credibility,
             json.dumps(ev.stake, ensure_ascii=False),
             ev.turn, ev.status, ev.response_directive_id),
        )
        ev.id = cur.lastrowid
        events.append(ev)

    return events


def fetch_pending_events(db, campaign_id: str, limit: int = 20) -> List[ImperialEvent]:
    """获取待处理事件 (按 priority_score 排序)"""
    rows = db.conn.execute(
        """SELECT * FROM imperial_events
        WHERE campaign_id = ? AND status = '未处理'
        ORDER BY turn DESC, id DESC LIMIT ?""",
        (campaign_id, limit),
    ).fetchall()
    out = []
    for r in rows:
        out.append(ImperialEvent(
            id=r["id"], campaign_id=r["campaign_id"],
            category=r["category"], title=r["title"],
            description=r["description"],
            urgency=r["urgency"], severity=r["severity"],
            credibility=r["credibility"],
            stake=json.loads(r["stake"] or "[]"),
            turn=r["turn"], status=r["status"],
            response_directive_id=r["response_directive_id"],
        ))
    out.sort(key=lambda e: e.priority_score, reverse=True)
    return out


def mark_event_status(db, event_id: int, status: str, directive_id: int = 0):
    """标记事件状态: 已读/已下旨/已回奏/逾期"""
    if directive_id:
        db.conn.execute(
            """UPDATE imperial_events
            SET status = ?, response_directive_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?""",
            (status, directive_id, event_id),
        )
    else:
        db.conn.execute(
            """UPDATE imperial_events SET status = ? WHERE id = ?""",
            (status, event_id),
        )
    db.conn.commit()


# ============== 验证 ==============
if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/home/admin/.openclaw/workspace/han-empire")
    from han_sim.db import GameDB
    db = GameDB.new("/tmp/test_events.db")
    events = generate_monthly_events(db, "test_cid", turn=1)
    print(f"Generated {len(events)} events:")
    for e in events:
        print(f"  [{e.category}] P={e.priority_score:.1f} U={e.urgency} S={e.severity} C={e.credibility}")
        print(f"    {e.title}: {e.description[:60]}...")

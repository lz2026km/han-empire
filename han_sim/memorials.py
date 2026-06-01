"""v2.2.0 终极版 P0-3: 奏报系统 (月奏/紧急奏/密奏/奏报)

设计: 事件 → 自动生成奏报, 每月 2-5 条 (随事件)
- 月奏: 例行公事
- 紧急奏: 边警/灾荒/哗变 (urgency >= 8)
- 密奏: 党争/暗通/谋反 (urgency 7-8, 秘密上报)
- 奏报: 一般事件

主公批阅 → 拟旨 / 存档
"""
import json
import random
import sys
import re
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

if __name__ != "__main__":
    from .imperial_events import ImperialEvent, generate_monthly_events
else:
    sys.path.insert(0, "/home/admin/.openclaw/workspace/han-empire")
    from han_sim.imperial_events import ImperialEvent, generate_monthly_events


# 月奏模板 (不依赖事件, 每月自动追加)
MONTHLY_MEMORIAL_TEMPLATES = {
    "财政": [
        {"title": "户部月奏", "content": "本月国库收入 {silver} 万两, 支出 {cost} 万两, 较上月 {trend}。", "from": "户部尚书"},
        {"title": "盐铁月报", "content": "本月盐铁税入 {silver} 万两, 较上月 {trend}。", "from": "度支尚书"},
    ],
    "军事": [
        {"title": "兵部月奏", "content": "本月边镇调兵 {troops} 人, 军需消耗 {grain} 石。", "from": "兵部尚书"},
        {"title": "边镇战报", "content": "{region} 守将报: 本月小股敌军犯边 {n} 次, 均已击退。", "from": "边镇都督"},
    ],
    "地方": [
        {"title": "刺史月奏", "content": "{region} 本月流民 {refugee} 户, 较上月 {trend}。", "from": "刺史"},
        {"title": "太守报安", "content": "{region} 本月太平, 百姓乐业, 谨奏。", "from": "太守"},
    ],
    "朝政": [
        {"title": "吏部月奏", "content": "本月铨选 {n} 人, 罢免 {m} 人, 谨呈主公圣裁。", "from": "吏部尚书"},
    ],
    "人物": [
        {"title": "京兆尹奏", "content": "本月京中 {trend}, 谨奏报主公。", "from": "京兆尹"},
    ],
}


@dataclass
class Memorial:
    id: int
    campaign_id: str
    memorial_type: str  # 月奏/紧急奏/密奏/奏报
    from_official: str
    title: str
    content: str
    is_secret: int
    is_urgent: int
    suggested_directive: Dict
    event_id: int
    status: str         # 已呈/已批/已下旨/已存档
    emperor_remark: str
    turn: int

    def to_dict(self) -> Dict:
        return asdict(self)


def save_memorial(db, m: Memorial) -> int:
    """存奏报到库, 返回 id"""
    cur = db.conn.execute(
        """INSERT INTO memorials
        (campaign_id, memorial_type, from_official, title, content,
         is_secret, is_urgent, suggested_directive, event_id, status, emperor_remark, turn)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (m.campaign_id, m.memorial_type, m.from_official, m.title, m.content,
         m.is_secret, m.is_urgent,
         json.dumps(m.suggested_directive, ensure_ascii=False),
         m.event_id, m.status, m.emperor_remark, m.turn),
    )
    db.conn.commit()
    return cur.lastrowid


def event_to_memorial(event: ImperialEvent) -> Memorial:
    """事件 → 奏报"""
    m_data = event.to_memorial()
    return Memorial(
        id=0,
        campaign_id=event.campaign_id,
        memorial_type=m_data["memorial_type"],
        from_official=m_data["from_official"],
        title=m_data["title"],
        content=event.description,
        is_secret=m_data["is_secret"],
        is_urgent=m_data["is_urgent"],
        suggested_directive=m_data["suggested_directive"],
        event_id=event.id,
        status="已呈",
        emperor_remark="",
        turn=event.turn,
    )


def generate_monthly_memorials(
    db,
    campaign_id: str,
    turn: int,
    state: Optional[Dict] = None,
    rng: Optional[random.Random] = None,
) -> List[Memorial]:
    """每月生成奏报:
    1. 事件 → 紧急奏/密奏
    2. 月奏模板 → 月奏 (1-2 条)
    3. 随机奏报 → 奏报 (0-2 条)
    """
    rng = rng or random.Random()
    memorials = []

    # 1. 事件 → 奏报
    events = generate_monthly_events(db, campaign_id, turn, state, rng)
    for ev in events:
        m = event_to_memorial(ev)
        m.id = save_memorial(db, m)
        memorials.append(m)

    # 2. 月奏 1-2 条
    n_monthly = rng.randint(1, 2)
    for _ in range(n_monthly):
        cat = rng.choice(list(MONTHLY_MEMORIAL_TEMPLATES.keys()))
        tpl = rng.choice(MONTHLY_MEMORIAL_TEMPLATES[cat])
        title = tpl["title"]
        content = tpl["content"]
        # 替换占位
        content = re.sub(r'\{silver\}', str(rng.randint(50, 200)), content)
        content = re.sub(r'\{cost\}', str(rng.randint(30, 150)), content)
        content = re.sub(r'\{troops\}', str(rng.randint(1000, 5000)), content)
        content = re.sub(r'\{grain\}', str(rng.randint(500, 3000)), content)
        content = re.sub(r'\{refugee\}', str(rng.randint(100, 5000)), content)
        if state and "regions" in state:
            content = re.sub(r'\{region\}', rng.choice(state["regions"]), content)
        else:
            content = re.sub(r'\{region\}', "冀州", content)
        content = re.sub(r'\{trend\}', rng.choice(["增", "减", "持平"]), content)
        content = re.sub(r'\{n\}', str(rng.randint(1, 10)), content)
        content = re.sub(r'\{m\}', str(rng.randint(0, 5)), content)

        m = Memorial(
            id=0, campaign_id=campaign_id, memorial_type="月奏",
            from_official=tpl["from"], title=title, content=content,
            is_secret=0, is_urgent=0, suggested_directive={}, event_id=0,
            status="已呈", emperor_remark="", turn=turn,
        )
        m.id = save_memorial(db, m)
        memorials.append(m)

    return memorials


def fetch_pending_memorials(db, campaign_id: str, limit: int = 30) -> List[Memorial]:
    """获取待批阅奏报 (按紧急/密奏优先)"""
    rows = db.conn.execute(
        """SELECT * FROM memorials
        WHERE campaign_id = ? AND status IN ('已呈', '已批')
        ORDER BY is_urgent DESC, is_secret DESC, id DESC LIMIT ?""",
        (campaign_id, limit),
    ).fetchall()
    out = []
    for r in rows:
        out.append(Memorial(
            id=r["id"], campaign_id=r["campaign_id"],
            memorial_type=r["memorial_type"], from_official=r["from_official"],
            title=r["title"], content=r["content"],
            is_secret=r["is_secret"], is_urgent=r["is_urgent"],
            suggested_directive=json.loads(r["suggested_directive"] or "{}"),
            event_id=r["event_id"], status=r["status"],
            emperor_remark=r["emperor_remark"], turn=r["turn"],
        ))
    return out


def update_memorial_status(db, memorial_id: int, status: str, remark: str = ""):
    """批阅奏报: 已批/已下旨/已存档"""
    db.conn.execute(
        """UPDATE memorials SET status = ?, emperor_remark = ? WHERE id = ?""",
        (status, remark, memorial_id),
    )
    db.conn.commit()


# ============== 验证 ==============
if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/home/admin/.openclaw/workspace/han-empire")
    from han_sim.db import GameDB
    db = GameDB.new("/tmp/test_memorials.db")
    memorials = generate_monthly_memorials(db, "test_cid", turn=1)
    print(f"Generated {len(memorials)} memorials:")
    for m in memorials:
        flag = []
        if m.is_urgent: flag.append("🔥紧急")
        if m.is_secret: flag.append("🤫密奏")
        flag_str = " ".join(flag) or "📜月奏"
        print(f"  [{m.memorial_type}] {flag_str} {m.from_official}: {m.title}")
        print(f"    {m.content[:70]}...")

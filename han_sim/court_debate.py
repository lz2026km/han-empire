"""v2.2.0 终极版 P1-8: 议政廷推 (LLM 辩论)

设计: 主公拟旨前, 可召大臣廷议
- 3-5 大臣发表意见 (LLM 驱动)
- 立场: 赞成/反对/折衷
- 权重: 资历 + 派系 + 性格
- 结论: 多数派意见
- 主公裁断: 采纳/否决/修正

议政廷推 + 臣工辩论 (宫廷议事体系)
"""
import json
import random
import sys
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

if __name__ != "__main__":
    from .imperial_events import ImperialEvent
else:
    sys.path.insert(0, "/home/admin/.openclaw/workspace/han-empire")


# 历史东汉末年典型派系
DEBATANTS = {
    "士族": [
        {"name": "袁绍", "office": "渤海太守", "stance_weight": 0.9, "style": "刚愎"},
        {"name": "王允", "office": "司徒", "stance_weight": 0.85, "style": "忠直"},
        {"name": "蔡邕", "office": "左中郎将", "stance_weight": 0.7, "style": "博学"},
        {"name": "荀爽", "office": "尚书", "stance_weight": 0.75, "style": "谨慎"},
    ],
    "宦官": [
        {"name": "张让", "office": "中常侍", "stance_weight": 0.8, "style": "狡诈"},
        {"name": "赵忠", "office": "中常侍", "stance_weight": 0.75, "style": "贪婪"},
    ],
    "外戚": [
        {"name": "何进", "office": "大将军", "stance_weight": 0.9, "style": "优柔"},
        {"name": "窦武", "office": "太傅", "stance_weight": 0.85, "style": "刚正"},
    ],
    "清流": [
        {"name": "卢植", "office": "尚书", "stance_weight": 0.7, "style": "耿直"},
        {"name": "郑玄", "office": "徵士", "stance_weight": 0.65, "style": "淡泊"},
    ],
    "边将": [
        {"name": "皇甫嵩", "office": "左中郎将", "stance_weight": 0.85, "style": "刚勇"},
        {"name": "朱儁", "office": "右中郎将", "stance_weight": 0.8, "style": "持重"},
    ],
}


@dataclass
class DebateStatement:
    name: str
    office: str
    faction: str
    position: str      # 赞成/反对/折衷
    content: str
    weight: float      # 影响力 0-1


@dataclass
class CourtDebate:
    id: int
    campaign_id: str
    topic: str
    participants: List[str]
    statements: List[DebateStatement]
    outcome: str
    emperor_decision: str
    turn: int

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["statements"] = [asdict(s) for s in self.statements]
        return d


def save_debate(db, d: CourtDebate) -> int:
    cur = db.conn.execute(
        """INSERT INTO court_debates
        (campaign_id, topic, participants, statements, outcome, emperor_decision, turn)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (d.campaign_id, d.topic,
         json.dumps(d.participants, ensure_ascii=False),
         json.dumps([asdict(s) for s in d.statements], ensure_ascii=False),
         d.outcome, d.emperor_decision, d.turn),
    )
    db.conn.commit()
    return cur.lastrowid


def fetch_debates(db, campaign_id: str, limit: int = 10) -> List[CourtDebate]:
    rows = db.conn.execute(
        """SELECT * FROM court_debates WHERE campaign_id = ?
        ORDER BY id DESC LIMIT ?""",
        (campaign_id, limit),
    ).fetchall()
    out = []
    for r in rows:
        out.append(CourtDebate(
            id=r["id"], campaign_id=r["campaign_id"],
            topic=r["topic"],
            participants=json.loads(r["participants"] or "[]"),
            statements=[DebateStatement(**s) for s in json.loads(r["statements"] or "[]")],
            outcome=r["outcome"],
            emperor_decision=r["emperor_decision"],
            turn=r["turn"],
        ))
    return out


# ============== LLM 驱动辩论 (核心) ==============
def run_court_debate(
    db,
    campaign_id: str,
    topic: str,
    directives_context: Optional[Dict] = None,
    factions: Optional[List[str]] = None,
    rng: Optional[random.Random] = None,
    llm_call=None,  # LLM 调用函数 (可选, 缺则用模板)
) -> CourtDebate:
    """启动一次廷议

    1. 选取 3-5 大臣 (覆盖不同派系)
    2. 每大臣发表意见 (LLM 优先, 否则模板)
    3. 加权汇总 → 结论
    4. 主公裁断 (外部)
    """
    rng = rng or random.Random()
    factions = factions or ["士族", "宦官", "外戚", "清流", "边将"]

    # 1. 选 3-5 大臣 (各派系 1-2 人)
    n = rng.randint(3, 5)
    participants = []
    seen_names = set()
    for f in rng.sample(factions, min(n, len(factions))):
        pool = DEBATANTS.get(f, [])
        if not pool:
            continue
        person = rng.choice(pool)
        if person["name"] in seen_names:
            continue
        seen_names.add(person["name"])
        participants.append({
            "name": person["name"],
            "office": person["office"],
            "faction": f,
            "stance_weight": person["stance_weight"],
            "style": person["style"],
        })

    # 2. 发表意见
    statements = []
    support_score = 0.0
    oppose_score = 0.0
    compromise_score = 0.0

    for p in participants:
        # 尝试 LLM 调用, 失败则用模板
        position, content = _debate_statement(p, topic, directives_context, rng, llm_call)
        s = DebateStatement(
            name=p["name"], office=p["office"], faction=p["faction"],
            position=position, content=content, weight=p["stance_weight"],
        )
        statements.append(s)
        if position == "赞成":
            support_score += p["stance_weight"]
        elif position == "反对":
            oppose_score += p["stance_weight"]
        else:
            compromise_score += p["stance_weight"]

    # 3. 结论
    if support_score > oppose_score and support_score > compromise_score:
        outcome = f"主和派占优 ({support_score:.1f} vs 反对 {oppose_score:.1f})"
    elif oppose_score > support_score and oppose_score > compromise_score:
        outcome = f"主战派占优 (反对 {oppose_score:.1f} vs 赞成 {support_score:.1f})"
    else:
        outcome = f"意见分歧, 建议折衷 (支持 {support_score:.1f}/反对 {oppose_score:.1f}/折衷 {compromise_score:.1f})"

    d = CourtDebate(
        id=0, campaign_id=campaign_id, topic=topic,
        participants=[p["name"] for p in participants],
        statements=statements, outcome=outcome,
        emperor_decision="", turn=directives_context.get("turn", 0) if directives_context else 0,
    )
    d.id = save_debate(db, d)
    return d


def _debate_statement(
    person: Dict, topic: str, ctx: Optional[Dict],
    rng: random.Random, llm_call=None,
) -> Tuple[str, str]:
    """生成单大臣意见 (LLM 优先, 模板兜底)"""
    # LLM 调用
    if llm_call is not None:
        try:
            sys_prompt = (
                f"你是 {person['name']}, {person['office']}, 派系 {person['faction']}, 性格 {person['style']}。\n"
                "请就朝政议题发表意见, 给出立场 (赞成/反对/折衷) 与理由 (100字内)。\n"
                "格式: 立场: <赞成/反对/折衷>\n理由: <...>"
            )
            user_prompt = f"议题: {topic}"
            if ctx:
                user_prompt += f"\n背景: {ctx.get('background', '')}"
            response = llm_call(sys_prompt, user_prompt)
            if response:
                lines = response.strip().split("\n", 1)
                pos = "折衷"
                for p in ["赞成", "反对", "折衷"]:
                    if p in lines[0]:
                        pos = p
                        break
                content = lines[1] if len(lines) > 1 else response
                return pos, content.strip()[:200]
        except Exception:
            pass  # LLM 失败, 降级到模板

    # 模板兜底 (按派系+性格预置)
    pos_by_faction = {
        "士族": ("反对", "此事若行, 恐伤士族根本, 臣以为不可轻动。"),
        "宦官": ("赞成", "主公英明, 此事若成, 社稷之福也。"),
        "外戚": ("折衷", "此事或可徐徐图之, 不宜操之过急。"),
        "清流": ("反对", "于理有碍, 于民有怨, 臣不敢苟同。"),
        "边将": ("赞成", "机不可失, 臣请缨出战, 必不辱命。"),
    }
    pos, content = pos_by_faction.get(person["faction"], ("折衷", "臣细思之, 此事尚需三思。"))
    # 个性修饰
    if person["style"] == "刚愎":
        content = content + " 主公三思!"
    elif person["style"] == "狡诈":
        content = "依臣之见, " + content + " 然他人之议, 不足为训。"
    elif person["style"] == "耿直":
        content = "臣有一言, 不知当讲不当讲: " + content
    return pos, content


def record_emperor_decision(db, debate_id: int, decision: str):
    """主公裁断: 采纳/否决/修正"""
    db.conn.execute(
        "UPDATE court_debates SET emperor_decision = ? WHERE id = ?",
        (decision, debate_id),
    )
    db.conn.commit()


# ============== 验证 ==============
if __name__ == "__main__":
    sys.path.insert(0, "/home/admin/.openclaw/workspace/han-empire")
    from han_sim.db import GameDB
    db = GameDB.new("/tmp/test_debate.db")

    # 模拟 LLM 调用
    def fake_llm(sys_p, user_p):
        return None  # 强制走模板

    print("=== 廷议 1: 对羌用兵 ===")
    d1 = run_court_debate(
        db, "test", "主公欲对羌用兵, 诸卿以为如何?",
        directives_context={"background": "西凉羌人屡犯边", "turn": 5},
        llm_call=fake_llm,
    )
    print(f"  议题: {d1.topic}")
    for s in d1.statements:
        print(f"    [{s.faction}] {s.name} ({s.office}): {s.position}")
        print(f"      {s.content}")
    print(f"  结论: {d1.outcome}")

    print("\n=== 廷议 2: 加派辽饷 ===")
    d2 = run_court_debate(
        db, "test", "辽东军费不足, 户部请加派三饷, 是否可行?",
        directives_context={"background": "辽东战事吃紧", "turn": 8},
        llm_call=fake_llm,
    )
    for s in d2.statements:
        print(f"    [{s.faction}] {s.name}: {s.position}")
    print(f"  结论: {d2.outcome}")
    record_emperor_decision(db, d2.id, "采纳多数意见, 加派减半, 暂缓一年")
    print(f"  圣裁: 已记录")

    # 查库
    debates = fetch_debates(db, "test")
    print(f"\n库内 {len(debates)} 条廷议")

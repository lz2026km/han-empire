"""v2.2.0 终极版 P0-4 + P0-5 + P1-6 + P1-7: 回奏/权限/反弹/信息差

4 大功能:
P0-4 回奏机制 (结果/代价/隐患 3 段)
P0-5 L1 权限分级 (5 档)
P1-6 党派反弹 (拖延/曲解/反扑)
P1-7 执行延迟 + 信息差
"""
import json
import random
import sys
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

if __name__ != "__main__":
    from .imperial_events import ImperialEvent
else:
    sys.path.insert(0, "/home/admin/.openclaw/workspace/han-empire")
    from han_sim.imperial_events import ImperialEvent


# ============== P0-5 5 档权限 ==============
AUTHORITY_LEVELS = {
    "口谕": {
        "scope": "身边太监/亲信",
        "prestige_cost": 0,
        "visibility": "单独面授",
        "enforce_strength": 0.4,
        "description": "皇帝口信, 形式轻, 易被忽视",
    },
    "谕旨": {
        "scope": "六部/院",
        "prestige_cost": 1,
        "visibility": "只给部院",
        "enforce_strength": 0.6,
        "description": "正式但有限, 仅限京官",
    },
    "圣旨": {
        "scope": "全国/州郡",
        "prestige_cost": 3,
        "visibility": "明发天下",
        "enforce_strength": 1.0,
        "description": "正诏, 强力, 但可被曲解",
    },
    "密旨": {
        "scope": "暗中执行",
        "prestige_cost": 2,
        "visibility": "密发厂卫",
        "enforce_strength": 0.85,
        "description": "秘密行动, 易反扑",
    },
    "廷议": {
        "scope": "朝堂决议",
        "prestige_cost": 2,
        "visibility": "明发朝堂",
        "enforce_strength": 0.95,
        "description": "百官共议, 阻力小但需辩论",
    },
}


def get_authority(level: str) -> Dict:
    """获取权限档详情"""
    return AUTHORITY_LEVELS.get(level, AUTHORITY_LEVELS["圣旨"])


def list_authority_levels() -> List[Dict]:
    return [{"level": k, **v} for k, v in AUTHORITY_LEVELS.items()]


# ============== P0-4 回奏 (结果/代价/隐患 3 段) ==============
VERDICT_RESULT_TEMPLATES = {
    "成功": [
        "诸事顺遂, 百姓称颂, 朝野咸服。",
        "颁行月余, 州郡奉行, 成效初显。",
        "所请已行, 大小臣工皆无异议。",
    ],
    "部分成功": [
        "事成七分, 尚余三分未竟, 待后续督办。",
        "京畿已行, 外州尚需时日推行。",
        "首战告捷, 然边远州县多有推诿。",
    ],
    "失败": [
        "事未竟而中道崩殂, 臣罪该万死。",
        "推行受挫, 士绅阻挠, 暂难全功。",
        "所请虽善, 然限于时势, 难以施行。",
    ],
    "被曲解": [
        "臣等依旨奉行, 然地方阳奉阴违, 已逮问相关官吏。",
        "外州奏报与圣意有间, 谨呈主公明察。",
        "有人借机生事, 曲解圣意, 罪不容诛。",
    ],
}


@dataclass
class Verdict:
    id: int
    campaign_id: str
    directive_id: int
    result: str           # 结果
    cost: Dict            # 代价 {silver, grain, troops, casualties}
    hidden_risk: List[Dict]  # 隐患 [{risktype, desc, severity}]
    truthfulness: int     # 1-10 (信息差)
    reporter: str         # 回奏人
    turn: int

    def to_dict(self) -> Dict:
        return asdict(self)


def save_verdict(db, v: Verdict) -> int:
    cur = db.conn.execute(
        """INSERT INTO verdicts
        (campaign_id, directive_id, result, cost, hidden_risk, truthfulness, reporter, turn)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (v.campaign_id, v.directive_id, v.result,
         json.dumps(v.cost, ensure_ascii=False),
         json.dumps(v.hidden_risk, ensure_ascii=False),
         v.truthfulness, v.reporter, v.turn),
    )
    db.conn.commit()
    return cur.lastrowid


def fetch_verdicts(db, campaign_id: str, limit: int = 20) -> List[Verdict]:
    rows = db.conn.execute(
        """SELECT * FROM verdicts WHERE campaign_id = ?
        ORDER BY id DESC LIMIT ?""",
        (campaign_id, limit),
    ).fetchall()
    out = []
    for r in rows:
        out.append(Verdict(
            id=r["id"], campaign_id=r["campaign_id"],
            directive_id=r["directive_id"], result=r["result"],
            cost=json.loads(r["cost"] or "{}"),
            hidden_risk=json.loads(r["hidden_risk"] or "[]"),
            truthfulness=r["truthfulness"],
            reporter=r["reporter"], turn=r["turn"],
        ))
    return out


def generate_verdict(
    db,
    campaign_id: str,
    directive: Dict,  # 来自 directives 表
    rng: Optional[random.Random] = None,
) -> Verdict:
    """旨意执行完毕 → 生成回奏
    - 成功率: enforce_strength 权重
    - 代价: 资源消耗 + 人员死伤
    - 隐患: 1-3 条隐藏
    - 真实度: 主公认知偏差 (信息差)
    """
    rng = rng or random.Random()
    auth = get_authority(directive.get("authority_level", "圣旨"))
    enforce = auth["enforce_strength"]

    # 1. 结果 (成功 / 部分 / 失败 / 被曲解)
    r = rng.random()
    if r < enforce * 0.5:
        result_type = "成功"
    elif r < enforce * 0.8:
        result_type = "部分成功"
    elif r < enforce * 0.95:
        result_type = "失败"
    else:
        result_type = "被曲解"
    result_text = rng.choice(VERDICT_RESULT_TEMPLATES[result_type])

    # 2. 代价 (万两/万石/人)
    res = json.loads(directive.get("resources") or "{}")
    cost = {}
    if "silver" in res:
        # 实际花费: 计划 ± 20%
        cost["silver"] = int(res["silver"] * rng.uniform(0.8, 1.2))
    if "grain" in res:
        cost["grain"] = int(res["grain"] * rng.uniform(0.85, 1.15))
    if "troops" in res:
        # 死伤: 战损 0-15%
        cost["casualties"] = int(res["troops"] * rng.uniform(0, 0.15))

    # 3. 隐患 (1-3 条)
    n_risks = rng.randint(1, 3)
    risk_types = [
        {"risktype": "财政", "desc": "国库告急, 后续调度困难"},
        {"risktype": "军心", "desc": "部分将士心存怨望"},
        {"risktype": "党争", "desc": "有臣工暗中串联, 议论朝政"},
        {"risktype": "民怨", "desc": "民间流言四起, 民心浮动"},
        {"risktype": "边患", "desc": "边镇有异动, 需密切注视"},
        {"risktype": "人事", "desc": "有大臣称病请辞"},
    ]
    hidden_risk = rng.sample(risk_types, min(n_risks, len(risk_types)))
    for h in hidden_risk:
        h["severity"] = rng.randint(3, 8)

    # 4. 真实度 (P1-7 信息差): 大部分回奏粉饰, 真实度 5-9
    truthfulness = rng.randint(5, 9)
    # 失败/被曲解的回奏更可能隐瞒
    if result_type in ["失败", "被曲解"]:
        truthfulness = rng.randint(3, 7)

    v = Verdict(
        id=0, campaign_id=campaign_id, directive_id=directive["id"],
        result=result_text, cost=cost, hidden_risk=hidden_risk,
        truthfulness=truthfulness,
        reporter=directive.get("executor") or "尚书",
        turn=directive.get("issued_turn", 0),
    )
    v.id = save_verdict(db, v)
    return v


# ============== P1-6 党派反弹 ==============
BACKLASH_TYPES = ["无", "拖延", "曲解", "反扑"]


def save_backlash(db, campaign_id: str, directive_id: int,
                  faction_id: str, backlash_type: str,
                  delay_turns: int = 0,
                  distortion: str = "",
                  counter_action: str = "",
                  turn: int = 0) -> int:
    cur = db.conn.execute(
        """INSERT INTO faction_backlashes
        (campaign_id, directive_id, faction_id, backlash_type,
         delay_turns, distortion, counter_action, turn)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (campaign_id, directive_id, faction_id, backlash_type,
         delay_turns, distortion, counter_action, turn),
    )
    db.conn.commit()
    return cur.lastrowid


def check_faction_backlash(
    rng: random.Random,
    directive: Dict,
    faction_impact: List[str],   # 旨意触及的派系
) -> str:
    """根据旨意触及的利益 → 计算反弹类型
    - 无 60%
    - 拖延 20% (延迟 1-3 回合)
    - 曲解 12% (歪曲执行)
    - 反扑 8% (激烈反抗)
    """
    if not faction_impact:
        return "无"
    impact = directive.get("interest_impact", "[]")
    if isinstance(impact, str):
        impact = json.loads(impact)
    if not impact:
        return "无"
    r = rng.random()
    if r < 0.60:
        return "无"
    elif r < 0.80:
        return "拖延"
    elif r < 0.92:
        return "曲解"
    else:
        return "反扑"


# ============== P1-7 信息差 ==============
def create_info_gap(
    db, campaign_id: str, subject: str, truth: str, perceived: str = "",
    severity: int = 5, turn: int = 0,
) -> int:
    cur = db.conn.execute(
        """INSERT INTO info_gaps
        (campaign_id, subject, truth, perceived, severity, turn)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (campaign_id, subject, truth, perceived, severity, turn),
    )
    db.conn.commit()
    return cur.lastrowid


def fetch_unrevealed_gaps(db, campaign_id: str) -> List[Dict]:
    """主公未察觉的信息差"""
    rows = db.conn.execute(
        """SELECT * FROM info_gaps WHERE campaign_id = ? AND revealed = 0
        ORDER BY severity DESC, id DESC""",
        (campaign_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def reveal_info_gap(db, gap_id: int):
    """主公识破真相"""
    db.conn.execute(
        "UPDATE info_gaps SET revealed = 1 WHERE id = ?",
        (gap_id,),
    )
    db.conn.commit()


# ============== 验证 ==============
if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/home/admin/.openclaw/workspace/han-empire")
    from han_sim.db import GameDB
    db = GameDB.new("/tmp/test_v22u.db")

    print("=== 5 档权限 ===")
    for k, v in AUTHORITY_LEVELS.items():
        print(f"  {k}: enforce={v['enforce_strength']}, prestige={v['prestige_cost']}, {v['description']}")

    print("\n=== P1-6 反弹分布 ===")
    rng = random.Random(42)
    d = {"interest_impact": '["士族", "豪商"]'}
    counts = {"无": 0, "拖延": 0, "曲解": 0, "反扑": 0}
    for _ in range(1000):
        counts[check_faction_backlash(rng, d, ["士族"])] += 1
    print(f"  1000次: {counts}")

    print("\n=== P0-4 回奏生成 ===")
    directive = {
        "id": 1, "issued_turn": 5, "authority_level": "圣旨",
        "executor": "皇甫嵩",
        "resources": '{"silver": 50, "troops": 3000}',
    }
    v = generate_verdict(db, "test", directive, rng)
    print(f"  结果: {v.result}")
    print(f"  代价: {v.cost}")
    print(f"  隐患: {len(v.hidden_risk)} 条 (severity {min(r['severity'] for r in v.hidden_risk)}-{max(r['severity'] for r in v.hidden_risk)})")
    print(f"  真实度: {v.truthfulness}/10")

    print("\n=== P1-7 信息差 ===")
    gap_id = create_info_gap(db, "test", "边镇兵力", "实际 5000 人", "上报 8000 人", severity=7)
    gaps = fetch_unrevealed_gaps(db, "test")
    print(f"  未揭示 {len(gaps)} 条, 首条: {gaps[0]['subject']} (偏差={gaps[0]['severity']})")
    reveal_info_gap(db, gap_id)
    print(f"  揭示后剩余: {len(fetch_unrevealed_gaps(db, 'test'))} 条")

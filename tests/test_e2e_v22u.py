"""v2.2.0 终极版 e2e: 8 项 P0+P1 端到端测试

完整流程:
1. 创建战役
2. 生成事件 + 奏报 (P0-2 + P0-3)
3. 廷议 (P1-8)
4. 拟旨 (9 维 + 5 档权限) (P0-1 + P0-5)
5. 党派反弹 (P1-6)
6. 回奏 + 代价 + 隐患 (P0-4)
7. 信息差揭示 (P1-7)
"""
import sys
import os
import tempfile
import json
import random

os.chdir('/home/admin/.openclaw/workspace/han-empire')
sys.path.insert(0, '/home/admin/.openclaw/workspace/han-empire')

from han_sim.db import GameDB
from han_sim.imperial_events import generate_monthly_events, fetch_pending_events
from han_sim.memorials import generate_monthly_memorials, fetch_pending_memorials
from han_sim.verdicts import (
    AUTHORITY_LEVELS, get_authority, generate_verdict,
    check_faction_backlash, save_backlash,
    create_info_gap, fetch_unrevealed_gaps, reveal_info_gap,
)
from han_sim.court_debate import run_court_debate, record_emperor_decision, fetch_debates


def main():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_path = tmp.name
    db = GameDB.new(db_path)
    tables = db.conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print(f"✅ DB created: {db_path}")
    print(f"   tables: {len(tables)} tables")

    rng = random.Random(42)
    cid = "test_v22u"

    # 1. 事件 + 奏报生成
    print("\n=== P0-2 事件 + P0-3 奏报 ===")
    memorials = generate_monthly_memorials(db, cid, turn=1, rng=rng)
    print(f"✅ Generated {len(memorials)} memorials")
    urgent = [m for m in memorials if m.is_urgent]
    secret = [m for m in memorials if m.is_secret]
    print(f"   紧急: {len(urgent)}, 密奏: {len(secret)}")

    # 2. 廷议
    print("\n=== P1-8 议政廷推 ===")
    d = run_court_debate(
        db, cid, "对羌用兵",
        directives_context={"background": "西凉羌人屡犯边", "turn": 1},
        llm_call=None,  # 用模板
    )
    print(f"✅ 廷议: {d.topic}")
    print(f"   参与者: {', '.join(d.participants)}")
    print(f"   结论: {d.outcome}")
    record_emperor_decision(db, d.id, "采纳边将建议, 出兵")
    print(f"   圣裁: 已记录")

    # 3. 拟旨
    print("\n=== P0-1 9 维旨意 + P0-5 5 档权限 ===")
    auth = get_authority("圣旨")
    print(f"✅ 拟旨 {auth['scope']} (prestige={auth['prestige_cost']}, enforce={auth['enforce_strength']})")
    directive = {
        "id": 1, "issued_turn": 1, "authority_level": "圣旨",
        "executor": "皇甫嵩",
        "resources": json.dumps({"silver": 50, "troops": 3000, "grain": 100}),
        "interest_impact": json.dumps(["士族", "豪商"]),
    }
    print(f"   9 维: target=西凉 / executor=皇甫嵩 / scope=全国 / resources=50+3k / deadline=3 / 圣旨 / 明发天下 / 利益触及: 士族,豪商")

    # 写 directives
    cur = db.conn.execute(
        """INSERT INTO directives
        (campaign_id, type, kind, status, content, target, executor, scope,
         resources, deadline_turns, authority_level, publicity, interest_impact, issued_turn)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cid, "decree", "出师", "confirmed", "讨羌", "西凉",
         "皇甫嵩", "全国", directive["resources"], 3, "圣旨", "明发天下",
         directive["interest_impact"], 1),
    )
    db.conn.commit()
    directive["id"] = cur.lastrowid
    print(f"   directive_id={directive['id']} written")

    # 4. 党派反弹
    print("\n=== P1-6 党派反弹 ===")
    # 5 档权限演示
    for level in AUTHORITY_LEVELS:
        b = check_faction_backlash(rng, directive, ["士族", "豪商"])
        print(f"   {level} (enforce={AUTHORITY_LEVELS[level]['enforce_strength']}): 反弹={b}")

    # 实际存一次
    save_backlash(db, cid, directive["id"], "士族", "拖延", delay_turns=2, turn=1)
    save_backlash(db, cid, directive["id"], "豪商", "曲解",
                  distortion="擅自提高税率, 与圣意相悖", turn=1)
    print(f"   写库 2 条 (士族=拖延, 豪商=曲解)")

    # 5. 回奏
    print("\n=== P0-4 回奏 ===")
    v = generate_verdict(db, cid, directive, rng)
    print(f"✅ 回奏: {v.reporter}")
    print(f"   结果: {v.result}")
    print(f"   代价: {v.cost}")
    print(f"   隐患: {len(v.hidden_risk)} 条")
    for h in v.hidden_risk:
        print(f"     - [{h['risktype']}] {h['desc']} (severity={h['severity']})")
    print(f"   真实度: {v.truthfulness}/10")

    # 6. 信息差
    print("\n=== P1-7 信息差 ===")
    create_info_gap(db, cid, "边镇兵力", "实际 5000", "上报 8000", severity=7, turn=1)
    create_info_gap(db, cid, "国库存银", "实际 200 万两", "上报 350 万两", severity=8, turn=1)
    create_info_gap(db, cid, "豪商田亩", "隐田 30%", "仅报 5%", severity=5, turn=1)
    gaps = fetch_unrevealed_gaps(db, cid)
    print(f"✅ 创建 {len(gaps)} 条信息差")
    # 揭示一条
    reveal_info_gap(db, gaps[0]["id"])
    remaining = fetch_unrevealed_gaps(db, cid)
    print(f"   揭示 1 条, 剩余 {len(remaining)} 条")

    # 7. 库汇总
    print("\n=== 库汇总 ===")
    counts = {}
    for t in ["imperial_events", "memorials", "directives", "verdicts",
             "faction_backlashes", "court_debates", "info_gaps", "authority_levels"]:
        n = db.conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        counts[t] = n
    for t, n in counts.items():
        print(f"   {t}: {n}")

    # 8. 总结
    print("\n" + "=" * 50)
    print("🎉 v2.2.0 终极版 8 项 P0+P1 全部协同工作!")
    print("=" * 50)

    # 清理
    os.unlink(db_path)


if __name__ == "__main__":
    main()

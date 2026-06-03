"""v5.0 P1-2: 批量给 seed_events.json 关键 event 加 precondition 字段

不改 Event class 已有字段定义, 只填数据.
"""
import json
import sys
import os

# 让脚本可独立运行
sys.path.insert(0, "/home/admin/.openclaw/workspace/han-empire")

SEED_EVENTS_PATH = os.path.join(
    "/home/admin/.openclaw/workspace/han-empire/content/seed_events.json"
)


# 关键 12 个 event 的 precondition (前因 + 改写口子)
PRECONDITIONS = {
    "seed_dongzhuo_tyrant": (
        "前因: 189 年董卓进京 + 废少帝立献帝 + 自封相国;"
        "改写: 玩家可派密使阻何进召董入京 / 提前刺杀董卓于途中 / 派禁军围何进逼其退让 / 抢先迁都洛阳避祸."
    ),
    "seed_empire_collapsing": (
        "前因: 189 年外戚与宦官轮流专权 + 黄巾起义余波 + 董卓乱政;"
        "改写: 玩家可重振朝纲削平外戚 / 严整禁军威慑宦官 / 提前赈济黄巾流民 / 镇压董卓余党."
    ),
    "seed_liucheng_traitors": (
        "前因: 190 年十八路诸侯讨董卓 + 各怀鬼胎 + 只想借机扩充;"
        "改写: 玩家可分化瓦解诸侯联盟 / 提前罢免何进余党 / 命袁绍为盟主但加监视 / 暗中联络其中 1-2 路专讨董卓."
    ),
    "seed_liuguo_dongzhuo": (
        "前因: 192 年董卓伏诛 + 王允失势 + 李傕郭汜反攻长安;"
        "改写: 玩家可派密使说服李傕郭汜投降 / 提前派吕布镇守长安 / 暗中与马腾韩遂结盟牵制 / 派王允继续掌权前提前安插亲信."
    ),
    "seed_caocao_yield_emperor": (
        "前因: 196 年汉室威权 < 20 + 曹操已控制豫州;"
        "改写: 玩家可主动迁都至曹操控制外之地 (如刘备处) / 派密使先联络袁绍让袁迎帝 / 威权先恢复至 40+ 再考虑迎帝 / 提前削弱曹操军事."
    ),
    "seed_huangjin_heliu": (
        "前因: 多省 unrest > 50 + 皇甫嵩朱儁不在朝 + 黄巾余党流窜;"
        "改写: 玩家可提前起用皇甫嵩朱儁 / 派兵镇压主要流民区 / 赈济饥民恢复 unrest / 严防黄巾残党渗透."
    ),
    "seed_yuanshu_emperor": (
        "前因: 袁术势盛 military_strength > 70 + 需拉拢盟友;"
        "改写: 玩家可提前派兵削弱袁术军事 / 派密使挑拨袁术与孙策关系 / 命吕布袭击袁术后方 / 派刺客暗杀袁术."
    ),
    "seed_xuchang_harvest": (
        "前因: 兖州 grain_security > 60 + 玩家刚经历天灾;"
        "改写: 此为正面事件, 一般不必改写; 但若玩家不希望有丰收 (经济太好), 可继续推天灾."
    ),
    "seed_yidaizhou_emergency": (
        "前因: 200 年衣带诏事发 + 董贵被诛 + 伏完被擒;"
        "改写: 玩家可提前阻止密谋外泄 / 派亲信保护董贵 / 主动废衣带诏以保命 / 让伏完提前诈死脱身 / 威权先恢复以压制曹操."
    ),
    "seed_liubiao_pressure": (
        "前因: 刘表据荆州 + 不奉朝廷号令 + 暗中扩军;"
        "改写: 玩家可派宗亲 (如刘晔) 监视刘表 / 派密使拉拢荆州士族 / 命刘表入朝述职 / 提前派兵夺襄阳."
    ),
    "seed_sunquan_independent": (
        "前因: 200 年前孙权未立业 + 江东未定;"
        "改写: 玩家可命孙坚回朝任职 / 派密使监视孙策 / 扶持其他江东势力牵制 / 主动封赏孙家以换忠心."
    ),
    "seed_caowei_rising": (
        "前因: 曹操势力上升 + 威权日增 + 迎帝后挟天子以令诸侯;"
        "改写: 玩家可拒迎帝迁许 / 暗中联络袁绍刘表牵制 / 提前削弱曹操 / 派密使离间曹操谋士."
    ),
}


def main():
    if not os.path.exists(SEED_EVENTS_PATH):
        print(f"FAIL: {SEED_EVENTS_PATH} 不存在")
        return 1

    with open(SEED_EVENTS_PATH, "r", encoding="utf-8") as f:
        events = json.load(f)

    if not isinstance(events, list):
        print(f"FAIL: 顶层不是 list, 是 {type(events)}")
        return 1

    added = 0
    skipped = 0
    for ev in events:
        eid = ev.get("id", "")
        if eid in PRECONDITIONS:
            if not ev.get("precondition"):
                ev["precondition"] = PRECONDITIONS[eid]
                added += 1
            else:
                skipped += 1
        else:
            # 未在字典中的 event 也加个默认 precondition
            if not ev.get("precondition"):
                kind = ev.get("kind", "")
                title = ev.get("title", "")
                ev["precondition"] = (
                    f"前因: {title} (kind={kind}); "
                    f"改写: 玩家可凭密使 / 调兵 / 迁都 / 安插亲信等任一作为改写前因或免除."
                )
                added += 1

    # 写回
    with open(SEED_EVENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

    print(f"OK: 添加/补全 {added} 条 precondition; 跳过 {skipped} (已存在)")
    print(f"总计 {len(events)} 条 events")
    return 0


if __name__ == "__main__":
    sys.exit(main())

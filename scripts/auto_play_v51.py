"""v5.1.5 P5-3: auto_play 平衡性测试.

无 LLM 快速跑 N 局 (默认 20), 每局随机扰动 6 维 metrics, 调
han_sim.legacy_stats.detect_ending 判定结局, 记录到 run_history, 输出崩盘率
/ 平均回合数 / ending 分布.

用法:
    python scripts/auto_play_v51.py                # 20 局
    python scripts/auto_play_v51.py --runs 50     # 50 局
    python scripts/auto_play_v51.py --runs 10 --seed 42 --db data/test.db
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import time
from collections import Counter
from typing import Any, Dict, List

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)


def _load_db(db_path: str):
    from han_sim.db import GameDB
    db = GameDB(db_path)
    return db


def _play_one(db, seed: int, max_turn: int = 200) -> Dict[str, Any]:
    """无 LLM 跑 1 局, 返回 {ending, final_turn, final_score}.

    模拟"无主公" baseline 模式 + 25% 正面事件 (历史随机事件雏形):
    - 藩镇基线 0-2/turn
    - 威权 ±2 / 声望 ±3 漂移
    - 25% 概率 触发"好事件" (威权 +5, 藩镇 -3, 声望 +2, 库银 +50)
    - 10% 概率 触发"坏事件" (威权 -3, 藩镇 +4, 声望 -5, 库银 -30)
    - 跑满 max_turn, 终局由 detect_ending 判定 (不提前 break, 让 ending 分布有变化)
    """
    rng = random.Random(seed)
    from han_sim.models import GameState
    from han_sim.legacy_stats import (
        compute_final_score, record_run_completion,
    )
    state = GameState(turn=1, year=189, period=1, metrics={
        "汉室库": 200, "内库": 100, "声望": 30, "威权": 25,
        "藩镇": 60, "skill_points": 0,
    })
    for t in range(1, max_turn + 1):
        m = state.metrics
        m["藩镇"] = max(0, min(100, m["藩镇"] + rng.randint(0, 2)))
        m["威权"] = max(0, min(100, m["威权"] + rng.randint(-2, 2)))
        m["声望"] = max(0, min(100, m["声望"] + rng.randint(-3, 3)))
        m["汉室库"] = max(0, m["汉室库"] + rng.randint(-20, 10))
        m["内库"] = max(0, m["内库"] + rng.randint(-8, 4))
        # 随机事件
        roll = rng.random()
        if roll < 0.10:
            m["威权"] = max(0, m["威权"] - 3)
            m["藩镇"] = min(100, m["藩镇"] + 4)
            m["声望"] = max(0, m["声望"] - 5)
            m["汉室库"] = max(0, m["汉室库"] - 30)
        elif roll < 0.35:
            m["威权"] = min(100, m["威权"] + 5)
            m["藩镇"] = max(0, m["藩镇"] - 3)
            m["声望"] = min(100, m["声望"] + 2)
            m["汉室库"] += 50
        state.turn = t
        state.year = 189 + (t // 12)
        state.period = 1 + (t // 36)
    final_score = compute_final_score(state)
    cid = f"autoplay_{seed}"
    record_run_completion(db, cid, state)
    return {
        "seed": seed,
        "final_turn": state.turn,
        "final_score": final_score,
        "final_metrics": dict(state.metrics),
    }


def _report(db, runs: List[Dict[str, Any]], elapsed: float) -> Dict[str, Any]:
    from han_sim.legacy_stats import get_global_stats
    stats = get_global_stats(db)
    endings = Counter()
    final_turns = []
    for r in runs:
        cid = f"autoplay_{r['seed']}"
        from han_sim.db import GameDB as _DB
        row = db.conn.execute(
            "SELECT ending, final_turn FROM run_history WHERE campaign_id=?",
            (cid,),
        ).fetchone()
        if row:
            endings[row["ending"]] += 1
            final_turns.append(int(row["final_turn"] or 0))
    avg_turn = sum(final_turns) / max(1, len(final_turns))
    bengkui = endings.get("崩盘", 0)
    bengkui_rate = bengkui / max(1, len(runs))
    print("=" * 60)
    print("v5.1.5 P5-3 auto_play 平衡性测试报告")
    print("=" * 60)
    print(f"局数:        {len(runs)}")
    print(f"耗时:        {elapsed:.1f}s ({elapsed/max(1,len(runs)):.2f}s/局)")
    print(f"平均回合:    {avg_turn:.1f}")
    print(f"崩盘率:      {bengkui_rate*100:.1f}% ({bengkui}/{len(runs)})")
    print(f"总局累计:    {stats['total_runs']}")
    print(f"ending 分布: {dict(endings)}")
    print("=" * 60)
    return {
        "runs": len(runs),
        "elapsed": elapsed,
        "avg_turn": avg_turn,
        "bengkui_rate": bengkui_rate,
        "endings": dict(endings),
    }


def main():
    p = argparse.ArgumentParser(description="v5.1.5 P5-3 auto_play 平衡性测试")
    p.add_argument("--runs", type=int, default=20)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--max-turn", type=int, default=200)
    p.add_argument("--db", type=str, default=os.path.join(ROOT, "data", "auto_play.db"))
    args = p.parse_args()
    os.makedirs(os.path.dirname(args.db) or ".", exist_ok=True)
    db = _load_db(args.db)
    t0 = time.time()
    runs = []
    for i in range(args.runs):
        runs.append(_play_one(db, seed=args.seed + i, max_turn=args.max_turn))
    elapsed = time.time() - t0
    _report(db, runs, elapsed)
    db.close()


if __name__ == "__main__":
    main()

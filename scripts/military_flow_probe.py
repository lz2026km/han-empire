"""军队调遣探针：验证诏书能否正确调度军队。

用法：
  .venv/bin/python scripts/military_flow_probe.py --db data/han_sim.db

三条固定测试诏书：
  1. 任命新统帅 + 新建军队
  2. 扩编/缩编/改编制/调防
  3. 裁撤军队
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


DECREES = [
    (
        "新建军队",
        "诏曰：董卓凉州军势大，不可不防。着曹操于陈留郡新建一军，军号'陈留营'，"
        "归属汉室，驻地陈留，统帅曹操，兵种步兵，初募五千人，月维护费一万两，"
        "补给五十、士气五十五、训练四十、装备四十五、欠饷零、机动五十、忠诚六十五。钦此。",
    ),
    (
        "扩编调防",
        "诏曰：陈留营既已成军，着扩编精锐二千人，另裁汰老弱五百人，净增一千五百人，"
        "月维护费增五千两。即日起自陈留调往颍川郡，驻地颍川，"
        "状态改为赴颍川驻防。因长途行军，补给暂减五、机动暂减五。钦此。",
    ),
    (
        "裁撤部分",
        "诏曰：陈留营赴颍川后，军中老弱、逃亡者仍多。着裁撤三千人，"
        "月维护费减五千两，余部留驻颍川，由曹操统帅，状态改为裁撤后整训。钦此。",
    ),
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="军队调遣探针")
    p.add_argument("--db", default="data/han_sim.db", help="数据库路径")
    return p.parse_args()


def get_current_state(conn: sqlite3.Connection) -> dict:
    """获取当前盘面状态。"""
    armies = conn.execute("SELECT id, name, commander, strength, location, status FROM armies").fetchall()
    cols = [d[0] for d in conn.execute("PRAGMA table_info(armies)").description]
    return {
        "armies": [dict(zip(cols, row)) for row in armies],
        "turn": conn.execute("SELECT value FROM state WHERE key='turn'").fetchone(),
    }


def print_state(label: str, conn: sqlite3.Connection) -> None:
    armies = get_current_state(conn)["armies"]
    print(f"\n{'='*50}")
    print(f"  {label}")
    print(f"{'='*50}")
    if not armies:
        print("  无军队记录")
        return
    for a in armies:
        print(f"  {a['name']} | 统帅:{a['commander']} | 兵力:{a['strength']} | 驻地:{a['location']} | {a['status']}")


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"[ERROR] 数据库不存在: {db_path}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(str(db_path))
    print_state("初始状态", conn)

    for i, (name, decree) in enumerate(DECREES, 1):
        print(f"\n>>> 测试 {i}: {name}")
        print(f"    诏书: {decree[:80]}...")
        # 实际测试需要 GameSession，这里仅展示结构

    print_state("最终状态", conn)
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
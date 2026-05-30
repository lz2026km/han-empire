"""记忆召回探针：验证过回合后还能否召回旧事。

用法：
  .venv/bin/python scripts/memory_recall_probe.py --db data/han_sim.db --jump-turns 2

原理：
  1. 读取现有 DB 中的 memories 表
  2. 模拟皇帝提问，检索相关记忆
  3. 输出检索命中结果
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="记忆召回探针")
    p.add_argument("--db", default="data/han_sim.db", help="数据库路径")
    p.add_argument("--jump-turns", type=int, default=0, help="把当前 turn 往后推 N 月（仅展示，不实际改 DB）")
    p.add_argument("--keywords", default="", help="逗号分隔关键词，不填则用 LLM 抽词")
    return p.parse_args()


def get_recent_memories(conn: sqlite3.Connection, window: int = 5) -> list:
    """取最近 N 回合的记忆。"""
    cur = conn.execute(
        "SELECT id, subject_type, subject_id, event_type, title, cause, outcome, sentiment, importance "
        "FROM memories ORDER BY created_turn DESC, id DESC LIMIT ?",
        (window,),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def search_memories(conn: sqlite3.Connection, keywords: list) -> list:
    """按关键词搜索记忆。"""
    placeholders = " OR ".join(["title LIKE ? OR cause LIKE ? OR outcome LIKE ?" for _ in keywords])
    vals = [f"%{k}%" for k in keywords for _ in range(3)]
    cur = conn.execute(
        f"SELECT id, subject_type, subject_id, event_type, title, sentiment, importance "
        f"FROM memories WHERE {placeholders} ORDER BY importance DESC, id DESC LIMIT 20",
        vals,
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"[ERROR] 数据库不存在: {db_path}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(str(db_path))
    current_turn = conn.execute("PRAGMA table_info(memories)").fetchall()
    if not current_turn:
        print("[WARN] memories 表不存在或为空，跳过")
        conn.close()
        return 0

    jump = args.jump_turns
    if jump > 0:
        print(f"[INFO] 模拟跳转 {jump} 回合后检索")

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()] if args.keywords else []

    print("\n=== 最近5回合记忆 ===")
    recent = get_recent_memories(conn, window=5)
    if not recent:
        print("  无记忆记录")
    for m in recent:
        print(f"  [{m['subject_type']}/{m['event_type']}] {m['title']} ({m['subject_id']})")
        print(f"    起因：{m['cause'][:60]}...")
        print(f"    结果：{m['outcome'][:60]}...")

    if keywords:
        print(f"\n=== 关键词检索: {keywords} ===")
        results = search_memories(conn, keywords)
        if not results:
            print("  无命中")
        for m in results:
            print(f"  [{m['subject_type']}/{m['event_type']}] {m['title']} | 情感:{m['sentiment']} | 重要:{m['importance']}")

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
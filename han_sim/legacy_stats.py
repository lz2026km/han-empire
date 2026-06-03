"""v5.1.5 P5-1: 多周目统计 (run_history 表 + record_run_completion + /api/stats/*)"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from han_sim.db import GameDB
from han_sim.models import GameState


# 结局枚举 (ming_sim README TODO 仿)
# 中兴 / 南迁 / 议和 / 禅让 / 衣带诏 / 流亡 / 崩盘
ENDINGS = (
    "中兴", "南迁", "议和", "禅让", "衣带诏", "流亡", "崩盘",
)


def detect_ending(state: GameState) -> str:
    """根据 state 自动检测结局. 简化规则:
    - turn > 240 (超过 20 年) → 流亡
    - 威权 >= 80 且 藩镇 < 30 → 中兴
    - 威权 >= 50 且 藩镇 < 50 → 议和
    - 威权 < 10 或 藩镇 >= 90 → 崩盘
    - 其余 → 禅让 (玩家投降)
    """
    turn = int(state.turn or 0)
    authority = int(state.metrics.get("威权", 0) or 0)
    fanzhen = int(state.metrics.get("藩镇", 0) or 0)
    if turn > 240:
        return "流亡"
    if authority >= 80 and fanzhen < 30:
        return "中兴"
    if authority >= 50 and fanzhen < 50:
        return "议和"
    if authority < 10 or fanzhen >= 90:
        return "崩盘"
    return "禅让"


def compute_final_score(state: GameState) -> int:
    """根据 state 计算最终得分 (满分 100).
    公式: 威权 * 0.4 + 声望 * 0.3 + (100 - 藩镇) * 0.3
    """
    authority = int(state.metrics.get("威权", 0) or 0)
    reputation = int(state.metrics.get("声望", 0) or 0)
    fanzhen = int(state.metrics.get("藩镇", 0) or 0)
    return int(authority * 0.4 + reputation * 0.3 + (100 - fanzhen) * 0.3)


def record_run_completion(
    db: GameDB,
    campaign_id: str,
    state: GameState,
    ending: Optional[str] = None,
) -> int:
    """v5.1.5 P5-1: 记录一局完成 (含 ending + final_score).

    Returns: run_history.id
    """
    final_ending = ending or detect_ending(state)
    final_score = compute_final_score(state)
    # 计算局数据
    row = db.conn.execute(
        "SELECT turn, year, period FROM game_state WHERE id=1"
    ).fetchone()
    final_turn = int(row["turn"]) if row else int(state.turn or 0)
    final_year = int(row["year"]) if row else int(state.year or 189)
    final_period = int(row["period"]) if row else int(state.period or 1)
    started_at = datetime.now().isoformat(timespec="seconds")
    decisions_count = 0
    try:
        for _ in db.conn.execute("SELECT COUNT(*) AS c FROM turn_directives WHERE status='issued'"):
            pass
        decisions_count = int(_["c"]) if _ else 0
    except Exception:
        pass

    db.conn.execute(
        """INSERT INTO run_history
           (campaign_id, started_at, ended_at, ending, final_turn,
            final_year, final_period, final_score, decisions_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (campaign_id, started_at, started_at, final_ending, final_turn,
         final_year, final_period, final_score, decisions_count),
    )
    db.conn.commit()
    rid = db.conn.execute(
        "SELECT last_insert_rowid() AS id"
    ).fetchone()["id"]
    return int(rid)


def get_global_stats(db: GameDB) -> Dict[str, Any]:
    """v5.1.5 P5-1: 全局统计 (仿 ming_sim README TODO '多周目统计').

    返:
      total_runs, wins, losses, total_turns, max_authority,
      max_legacy, endings_unlocked
    """
    rows = db.conn.execute("SELECT * FROM run_history").fetchall()
    if not rows:
        return {
            "total_runs": 0,
            "wins": 0,
            "losses": 0,
            "total_turns": 0,
            "max_authority": 0,
            "max_legacy": "",
            "endings_unlocked": [],
        }
    total_runs = len(rows)
    wins = sum(1 for r in rows if r["ending"] in ("中兴", "议和"))
    losses = sum(1 for r in rows if r["ending"] in ("崩盘", "流亡"))
    total_turns = sum(int(r["final_turn"] or 0) for r in rows)
    max_authority = max((int(r["final_score"] or 0) for r in rows), default=0)
    endings = sorted({r["ending"] for r in rows if r["ending"]})
    return {
        "total_runs": total_runs,
        "wins": wins,
        "losses": losses,
        "total_turns": total_turns,
        "max_authority": max_authority,
        "max_legacy": "",
        "endings_unlocked": list(endings),
    }


def get_run_history(db: GameDB, limit: int = 20) -> List[Dict[str, Any]]:
    """v5.1.5 P5-1: 历史列表 (倒序按 id)."""
    rows = db.conn.execute(
        "SELECT * FROM run_history ORDER BY id DESC LIMIT ?",
        (int(limit),),
    ).fetchall()
    return [dict(r) for r in rows]


def format_legacy_for_display(ending: str) -> str:
    """ending 中文化显示."""
    if ending == "中兴":
        return "汉室中兴"
    if ending == "南迁":
        return "迁都续命"
    if ending == "议和":
        return "割据议和"
    if ending == "禅让":
        return "禅让曹魏"
    if ending == "衣带诏":
        return "衣带密谋"
    if ending == "流亡":
        return "流亡山林"
    if ending == "崩盘":
        return "天下崩盘"
    return ending

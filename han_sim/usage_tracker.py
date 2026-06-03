"""
v3.0-AP-3: Token 用量统计透明化 (调研 P1-3)
==============================================

设计依据: 36氪《崇祯模拟器》差评集中
  "玩家吐槽'积分是负数, 倒欠功德值'" → 青干按量计费不透明
  我们的解法: 公开 + 累计 + 估算

实现:
  1. 每次 LLM 调用记录 token 数 (prompt/completion/total)
  2. 按 (今日/本周/本月) 累计
  3. 估算成本 (按 0.11 美元/百万 token, GLM-4.x 价)
  4. SQLite 持久化, 跨进程
"""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


COST_PER_MILLION_TOKENS_USD = 0.11
DB_PATH = Path("/home/admin/.openclaw/workspace/han-empire/data/usage.db")

_LOCK = threading.Lock()


def _ensure_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usage_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER NOT NULL,
                purpose TEXT,
                provider TEXT,
                model TEXT,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_ts ON usage_records(ts)")


def record_usage(
    purpose: str,
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> None:
    """记录一次 LLM 调用的 token 用量."""
    with _LOCK:
        _ensure_db()
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                """INSERT INTO usage_records
                   (ts, purpose, provider, model, prompt_tokens, completion_tokens, total_tokens)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (int(time.time()), purpose, provider, model,
                 prompt_tokens, completion_tokens, prompt_tokens + completion_tokens),
            )


def get_stats() -> Dict[str, Any]:
    """返回今日/本周/本月的 token 用量统计.

    v5.0 P0-3 增强: 增加按 model/purpose 拆分 + cache 命中率
    """
    with _LOCK:
        _ensure_db()
        now = int(time.time())
        one_day = 86400
        one_week = 7 * one_day
        one_month = 30 * one_day

        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            # 总计
            cur.execute(
                "SELECT COALESCE(SUM(total_tokens),0) FROM usage_records WHERE ts > ?",
                (now - one_day,),
            )
            today = cur.fetchone()[0]
            cur.execute(
                "SELECT COALESCE(SUM(total_tokens),0) FROM usage_records WHERE ts > ?",
                (now - one_week,),
            )
            week = cur.fetchone()[0]
            cur.execute(
                "SELECT COALESCE(SUM(total_tokens),0) FROM usage_records WHERE ts > ?",
                (now - one_month,),
            )
            month = cur.fetchone()[0]

            # v5.0 P0-3: 按 model 拆分 (本月)
            cur.execute(
                """SELECT model, COALESCE(SUM(total_tokens),0) AS total,
                          COALESCE(SUM(prompt_tokens),0) AS pt,
                          COALESCE(SUM(completion_tokens),0) AS ct,
                          COUNT(*) AS calls
                   FROM usage_records
                   WHERE ts > ?
                   GROUP BY model
                   ORDER BY total DESC""",
                (now - one_month,),
            )
            by_model = [
                {
                    "model": r[0] or "(unknown)",
                    "total_tokens": r[1],
                    "prompt_tokens": r[2],
                    "completion_tokens": r[3],
                    "calls": r[4],
                }
                for r in cur.fetchall()
            ]

            # v5.0 P0-3: 按 purpose 拆分 (本月)
            cur.execute(
                """SELECT purpose, COALESCE(SUM(total_tokens),0) AS total, COUNT(*) AS calls
                   FROM usage_records
                   WHERE ts > ?
                   GROUP BY purpose
                   ORDER BY total DESC""",
                (now - one_month,),
            )
            by_purpose = [
                {"purpose": r[0] or "(unknown)", "total_tokens": r[1], "calls": r[2]}
                for r in cur.fetchall()
            ]

            # v5.0 P0-3: 调用总数
            cur.execute("SELECT COUNT(*) FROM usage_records")
            total_calls = cur.fetchone()[0]

        cost = month * COST_PER_MILLION_TOKENS_USD / 1_000_000
        return {
            "today": today,
            "week": week,
            "month": month,
            "cost": round(cost, 4),
            "currency": "USD",
            "rate_per_million": COST_PER_MILLION_TOKENS_USD,
            # v5.0 P0-3 新增
            "by_model": by_model,
            "by_purpose": by_purpose,
            "total_calls": total_calls,
        }


def get_recent(limit: int = 20) -> List[Dict[str, Any]]:
    """返回最近 limit 条记录."""
    with _LOCK:
        _ensure_db()
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM usage_records ORDER BY ts DESC LIMIT ?",
                (limit,),
            )
            return [dict(r) for r in cur.fetchall()]

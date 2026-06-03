"""v5.1.5 P5-1: 多周目统计 (run_history 表 + record_run_completion + get_global_stats + get_run_history)"""
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from han_sim.db import GameDB
from han_sim.models import GameState
from han_sim.legacy_stats import (
    detect_ending, compute_final_score,
    record_run_completion, get_global_stats, get_run_history,
    ENDINGS,
)


def _new_state(metrics: dict, turn: int = 50, year: int = 200, period: int = 1) -> GameState:
    return GameState(
        turn=turn,
        year=year,
        period=period,
        metrics=dict(metrics),
    )


def test_legacy_stats_detect_ending_zhongxing():
    state = _new_state({"威权": 85, "藩镇": 20})
    assert detect_ending(state) == "中兴"


def test_legacy_stats_detect_ending_yihe():
    state = _new_state({"威权": 60, "藩镇": 40})
    assert detect_ending(state) == "议和"


def test_legacy_stats_detect_ending_bengpan():
    state = _new_state({"威权": 5, "藩镇": 95})
    assert detect_ending(state) == "崩盘"


def test_legacy_stats_record_and_query(tmp_path):
    db_path = tmp_path / "stats.db"
    db = GameDB(str(db_path))
    # 3 局不同 ending
    for cid, metrics, ending, turn in [
        ("c1", {"威权": 85, "声望": 70, "藩镇": 20}, "中兴", 100),
        ("c2", {"威权": 55, "声望": 50, "藩镇": 40}, "议和", 80),
        ("c3", {"威权": 5, "声望": 10, "藩镇": 95}, "崩盘", 60),
    ]:
        state = _new_state(metrics, turn=turn)
        rid = record_run_completion(db, cid, state, ending=ending)
        assert rid > 0
    stats = get_global_stats(db)
    assert stats["total_runs"] == 3
    assert stats["wins"] == 2  # 中兴 + 议和
    assert stats["losses"] == 1  # 崩盘
    assert stats["total_turns"] == 100 + 80 + 60
    assert "中兴" in stats["endings_unlocked"]
    assert "议和" in stats["endings_unlocked"]
    assert "崩盘" in stats["endings_unlocked"]
    runs = get_run_history(db, limit=10)
    assert len(runs) == 3
    # 倒序
    assert runs[0]["campaign_id"] == "c3"
    assert runs[2]["campaign_id"] == "c1"
    # 得分计算
    assert runs[2]["final_score"] > runs[1]["final_score"] > runs[0]["final_score"]
    db.close()

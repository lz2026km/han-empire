"""v5.2.0 P6-16: /api/campaigns/<id>/end (record_run_completion 触发)"""
import os
import sys
import tempfile
import json

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def _make_state(metrics: dict, turn: int = 50, year: int = 200, period: int = 1):
    from han_sim.models import GameState
    return GameState(turn=turn, year=year, period=period, metrics=dict(metrics))


def test_end_campaign_zhongxing(tmp_path, monkeypatch):
    """v5.2.0 P6-16: 威权高 藩镇低 → 中兴."""
    from han_sim.db import GameDB
    from han_sim.legacy_stats import record_run_completion, get_global_stats
    db = GameDB(str(tmp_path / "test.db"))
    state = _make_state({"威权": 85, "声望": 70, "藩镇": 20})
    rid = record_run_completion(db, "c-zhongxing", state)
    assert rid > 0
    stats = get_global_stats(db)
    assert stats["total_runs"] == 1
    assert "中兴" in stats["endings_unlocked"]
    db.close()


def test_end_campaign_bengpan(tmp_path, monkeypatch):
    """v5.2.0 P6-16: 威权低 藩镇高 → 崩盘."""
    from han_sim.db import GameDB
    from han_sim.legacy_stats import record_run_completion, get_global_stats
    db = GameDB(str(tmp_path / "test.db"))
    state = _make_state({"威权": 5, "声望": 10, "藩镇": 95})
    rid = record_run_completion(db, "c-bengpan", state)
    assert rid > 0
    stats = get_global_stats(db)
    assert "崩盘" in stats["endings_unlocked"]
    assert stats["losses"] == 1
    db.close()


def test_end_campaign_manual_ending(tmp_path):
    """v5.2.0 P6-16: 手动传 ending (覆盖 auto-detect)."""
    from han_sim.db import GameDB
    from han_sim.legacy_stats import record_run_completion, get_global_stats
    db = GameDB(str(tmp_path / "test.db"))
    state = _make_state({"威权": 5, "声望": 10, "藩镇": 95})  # auto 是崩盘
    rid = record_run_completion(db, "c-manual", state, ending="禅让")
    assert rid > 0
    stats = get_global_stats(db)
    # 即使 auto-detect 是崩盘, 手动传禅让覆盖
    assert "禅让" in stats["endings_unlocked"]
    db.close()

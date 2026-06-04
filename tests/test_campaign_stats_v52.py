"""v5.2.0 P6-17: /api/campaigns/<id>/stats (单局统计快照)"""
import os
import sys
import tempfile
import json

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_stats_endpoint_basic_fields(tmp_path, monkeypatch):
    """v5.2.0 P6-17: /api/campaigns/<id>/stats 返 turn/year/period/metrics/decisions_count."""
    import server as srv
    from han_sim.db import GameDB
    from han_sim.models import GameState
    from han_sim.session import GameSession
    from han_sim.content import GameContent

    db_path = str(tmp_path / "stats_campaign.db")
    monkeypatch.setattr(srv, "GAMES", {})

    # 用 GameSession.new 创建完整 session
    content = GameContent()
    session = GameSession.new(campaign_id="c1", content=content)
    # 改 state
    session.state = GameState(
        turn=42, year=192, period=1, metrics={
            "汉室库": 180, "内库": 90, "威权": 25, "藩镇": 70, "声望": 35,
        },
    )
    session.save()
    srv.GAMES["c1"] = session

    # 调端点
    client = srv.app.test_client()
    resp = client.get("/api/campaigns/c1/stats")
    assert resp.status_code == 200, resp.get_data(as_text=True)
    data = resp.get_json()
    assert data["turn"] == 42
    assert data["year"] == 192
    assert data["period"] == 1
    assert data["metrics"]["威权"] == 25
    assert data["metrics"]["汉室库"] == 180
    assert data["decisions_count"] == 0
    assert data["budget"] is None  # 无 budget 字段


def test_stats_endpoint_404_unknown(tmp_path, monkeypatch):
    """v5.2.0 P6-17: 未知 campaign_id 返 404."""
    import server as srv
    monkeypatch.setattr(srv, "GAMES", {})
    client = srv.app.test_client()
    resp = client.get("/api/campaigns/c-nonexistent-xyz/stats")
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["error"] == "load_failed"

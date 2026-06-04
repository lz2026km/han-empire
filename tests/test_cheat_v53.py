"""v5.3.0 P7-2: Cheat 控制台加强 (5 新命令)"""
import os
import sys
import json
import tempfile

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_cheat_season_valid(monkeypatch, tmp_path):
    """v5.3.0 P7-2: season <valid> 写入 kv_store."""
    import server as srv
    from han_sim.db import GameDB
    from han_sim.models import GameState
    from han_sim.session import GameSession
    from han_sim.content import GameContent

    db_path = str(tmp_path / "test_season.db")
    monkeypatch.setattr(srv, "GAMES", {})

    session = GameSession.new(campaign_id="c1", content=GameContent())
    session.state = GameState(turn=1, year=189, period=1)
    session.db = GameDB(db_path)
    session.save()
    srv.GAMES["c1"] = session

    client = srv.app.test_client()
    resp = client.post("/api/campaigns/c1/cheat",
                       json={"command": "season spring"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "spring" in data["output"]


def test_cheat_season_invalid(monkeypatch, tmp_path):
    """v5.3.0 P7-2: season <invalid> 报错."""
    import server as srv
    from han_sim.db import GameDB
    from han_sim.models import GameState
    from han_sim.session import GameSession
    from han_sim.content import GameContent

    db_path = str(tmp_path / "test_season2.db")
    monkeypatch.setattr(srv, "GAMES", {})
    session = GameSession.new(campaign_id="c1", content=GameContent())
    session.state = GameState(turn=1, year=189, period=1)
    session.db = GameDB(db_path)
    session.save()
    srv.GAMES["c1"] = session

    client = srv.app.test_client()
    resp = client.post("/api/campaigns/c1/cheat",
                       json={"command": "season invalid_name"})
    data = resp.get_json()
    assert data["success"] is False
    assert "无效" in data["output"]


def test_cheat_volume_valid(monkeypatch, tmp_path):
    """v5.3.0 P7-2: volume 50 写入 kv_store."""
    import server as srv
    from han_sim.db import GameDB
    from han_sim.models import GameState
    from han_sim.session import GameSession
    from han_sim.content import GameContent

    db_path = str(tmp_path / "test_vol.db")
    monkeypatch.setattr(srv, "GAMES", {})
    session = GameSession.new(campaign_id="c1", content=GameContent())
    session.state = GameState(turn=1, year=189, period=1)
    session.db = GameDB(db_path)
    session.save()
    srv.GAMES["c1"] = session

    client = srv.app.test_client()
    resp = client.post("/api/campaigns/c1/cheat",
                       json={"command": "volume 50"})
    data = resp.get_json()
    assert data["success"] is True
    assert "50%" in data["output"]


def test_cheat_snapshot_export(monkeypatch, tmp_path):
    """v5.3.0 P7-2: snapshot-export 写 JSON 到 data/snapshots/."""
    import server as srv
    from han_sim.db import GameDB
    from han_sim.models import GameState
    from han_sim.session import GameSession
    from han_sim.content import GameContent

    db_path = str(tmp_path / "test_snap.db")
    monkeypatch.setattr(srv, "GAMES", {})
    # 临时改 ROOT 让 snapshot 落 tmp_path
    monkeypatch.setattr(srv, "ROOT", str(tmp_path))
    session = GameSession.new(campaign_id="c-snap", content=GameContent())
    session.state = GameState(turn=42, year=192, period=6,
                              metrics={"威权": 30, "汉室库": 200})
    session.db = GameDB(db_path)
    session.save()
    srv.GAMES["c-snap"] = session

    client = srv.app.test_client()
    resp = client.post("/api/campaigns/c-snap/cheat",
                       json={"command": "snapshot-export"})
    data = resp.get_json()
    assert data["success"] is True
    # 找 snapshot 文件
    snap_dir = tmp_path / "data" / "snapshots"
    snaps = list(snap_dir.glob("c-snap_*.json"))
    assert len(snaps) == 1
    snap = json.loads(snaps[0].read_text(encoding="utf-8"))
    assert snap["turn"] == 42
    assert snap["metrics"]["威权"] == 30

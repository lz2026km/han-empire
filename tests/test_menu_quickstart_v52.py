"""v5.2.0 P6-18: /api/menu/quick-start (一站式建新朝)"""
import os
import sys
import json

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_quick_start_default_emperor(monkeypatch):
    """v5.2.0 P6-18: 无 body → 默认刘协, 返 campaign_id + 初始 state."""
    import server as srv
    monkeypatch.setattr(srv, "GAMES", {})
    client = srv.app.test_client()
    resp = client.post("/api/menu/quick-start", json={})
    assert resp.status_code == 200, resp.get_data(as_text=True)
    data = resp.get_json()
    assert data["campaign_id"].startswith("c")
    assert len(data["campaign_id"]) >= 9  # c + 8 hex
    assert data["emperor_name"] == "刘协"
    assert data["version"] == "5.3.0"
    assert "威权" in data["metrics"]
    # 验证 session 已注册到 GAMES
    assert data["campaign_id"] in srv.GAMES


def test_quick_start_custom_name(monkeypatch):
    """v5.2.0 P6-18: 自定义 emperor_name 透传."""
    import server as srv
    monkeypatch.setattr(srv, "GAMES", {})
    client = srv.app.test_client()
    resp = client.post(
        "/api/menu/quick-start", json={"emperor_name": "汉献帝v5"}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["emperor_name"] == "汉献帝v5"

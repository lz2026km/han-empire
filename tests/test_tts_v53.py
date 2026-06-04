"""v5.3.0 P7-3: /api/tts 端点 (edge-tts 集成)"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_tts_empty_text_rejected(monkeypatch):
    """v5.3.0 P7-3: text 空 → 400 (即使 edge_tts 缺失也走 400)."""
    import server as srv
    # 模拟 tts 模块可用 (避免 edge_tts 缺失的 500)
    from han_sim import tts as tts_mod
    monkeypatch.setattr(tts_mod, "text_to_audio_base64",
                        lambda text, **kw: "ZmFrZS1hdWRpbw==", raising=False)
    client = srv.app.test_client()
    resp = client.post("/api/tts", json={"text": ""})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["error"] == "empty_text"


def test_tts_too_long_rejected(monkeypatch):
    """v5.3.0 P7-3: text > 2000 字 → 400."""
    import server as srv
    from han_sim import tts as tts_mod
    monkeypatch.setattr(tts_mod, "text_to_audio_base64",
                        lambda text, **kw: "ZmFrZS1hdWRpbw==", raising=False)
    client = srv.app.test_client()
    resp = client.post("/api/tts", json={"text": "x" * 2001})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["error"] == "text_too_long"


def test_tts_invalid_voice_falls_back(monkeypatch):
    """v5.3.0 P7-3: 非法 voice → fallback 默认."""
    from han_sim import tts as tts_mod
    monkeypatch.setattr(tts_mod, "text_to_audio_base64",
                        lambda text, **kw: "ZmFrZS1hdWRpbw==", raising=False)
    import server as srv
    client = srv.app.test_client()
    resp = client.post("/api/tts", json={
        "text": "献帝初平元年", "voice": "fake_voice_xyz",
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["voice"] == "zh-CN-YunjianNeural"  # fallback 默认
    assert "audio" in data
    assert data["size_kb"] >= 0

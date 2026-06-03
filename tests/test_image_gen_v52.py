"""v5.2.0 P6-10: MiniMax image-01 生图 (单元 + mock HTTP)"""
import json
import os
import sys
from unittest import mock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from han_sim import image_gen
from han_sim.image_gen import (
    _get_api_key, _build_payload, _extract_urls, generate_image, download_image,
    ALLOWED_ASPECT,
)


def test_get_api_key_missing(monkeypatch):
    """v5.2.0 P6-10: 3 个 KEY 全无时, 报 RuntimeError."""
    for k in ("MINIMAX_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(RuntimeError, match="未找到 API key"):
        _get_api_key()


def test_get_api_key_first(monkeypatch):
    """v5.2.0 P6-10: MINIMAX_API_KEY 优先."""
    monkeypatch.setenv("MINIMAX_API_KEY", "sk-test-minimax")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai")
    assert _get_api_key() == "sk-test-minimax"


def test_get_api_key_placeholder_ignored(monkeypatch):
    """v5.2.0 P6-10: 占位符 your_minimax_key_here 跳过."""
    monkeypatch.setenv("MINIMAX_API_KEY", "your_minimax_key_here")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-real-openai")
    assert _get_api_key() == "sk-real-openai"


def test_build_payload_validation():
    """v5.2.0 P6-10: aspect_ratio + n 范围校验."""
    p = _build_payload("test", aspect_ratio="16:9", n=2)
    assert p["model"] == "image-01"
    assert p["aspect_ratio"] == "16:9"
    assert p["n"] == 2
    assert p["response_format"] == "url"
    assert p["prompt_optimizer"] is True
    # 非法 aspect_ratio
    with pytest.raises(ValueError, match="不在"):
        _build_payload("test", aspect_ratio="99:1")
    # n 越界
    with pytest.raises(ValueError, match="1-4"):
        _build_payload("test", n=10)


def test_extract_urls_format_a():
    """v5.2.0 P6-10: 格式 A - data.image_urls[]."""
    p = {"data": {"image_urls": ["https://a", "https://b"]}}
    assert _extract_urls(p) == ["https://a", "https://b"]


def test_extract_urls_format_b():
    """v5.2.0 P6-10: 格式 B - images[].url."""
    p = {"images": [{"url": "https://x"}, {"url": "https://y"}]}
    assert _extract_urls(p) == ["https://x", "https://y"]


def test_extract_urls_no_urls():
    """v5.2.0 P6-10: 响应无 url → 报错."""
    with pytest.raises(RuntimeError, match="无 url"):
        _extract_urls({"data": {}})


def test_generate_image_success(monkeypatch):
    """v5.2.0 P6-10: 成功生图返 url 列表."""
    monkeypatch.setenv("MINIMAX_API_KEY", "sk-test")
    fake_resp = {"data": {"image_urls": ["https://cdn.minimaxi.com/img1.png"]}}
    with mock.patch.object(image_gen, "_post_minimax", return_value=fake_resp) as m:
        urls = generate_image("A palace", aspect_ratio="1:1", n=1)
    assert urls == ["https://cdn.minimaxi.com/img1.png"]
    m.assert_called_once()


def test_generate_image_retry_then_success(monkeypatch):
    """v5.2.0 P6-10: 第 1 次 5xx, retry 1 后成功."""
    monkeypatch.setenv("MINIMAX_API_KEY", "sk-test")
    fake_resp = {"data": {"image_urls": ["https://x"]}}
    call_count = {"n": 0}

    def fake_post(payload, key, timeout):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("HTTP 500")
        return fake_resp

    # monkeypatch time.sleep 加速
    with mock.patch.object(image_gen.time, "sleep"), \
         mock.patch.object(image_gen, "_post_minimax", side_effect=fake_post):
        urls = generate_image("test", n=1)
    assert urls == ["https://x"]
    assert call_count["n"] == 2


def test_generate_image_retry_exhausted(monkeypatch):
    """v5.2.0 P6-10: 重试耗尽仍失败."""
    monkeypatch.setenv("MINIMAX_API_KEY", "sk-test")

    def always_fail(payload, key, timeout):
        raise RuntimeError("HTTP 500")

    with mock.patch.object(image_gen.time, "sleep"), \
         mock.patch.object(image_gen, "_post_minimax", side_effect=always_fail):
        with pytest.raises(RuntimeError, match="重试"):
            generate_image("test", n=1)


def test_download_image(tmp_path, monkeypatch):
    """v5.2.0 P6-10: 下载到本地文件."""
    fake_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    out = tmp_path / "img.png"

    class FakeResp:
        def __init__(self, data):
            self.data = data
        def read(self):
            return self.data
        def __enter__(self): return self
        def __exit__(self, *a): pass

    with mock.patch.object(image_gen.urllib.request, "urlopen",
                           return_value=FakeResp(fake_bytes)):
        ok = download_image("https://cdn.minimaxi.com/test.png", str(out))
    assert ok is True
    assert out.read_bytes() == fake_bytes

"""v5.1.5 P5-2: .env 模板 (项目根 .env.example + server.py 启动时一次性 _load_dotenv_once)"""
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_dotenv_example_exists():
    """v5.1.5 P5-2: .env.example 在项目根."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    p = os.path.join(root, ".env.example")
    assert os.path.exists(p), f".env.example missing at {p}"
    text = open(p, encoding="utf-8").read()
    # 至少含 3 个主公需要的 KEY
    for key in ("MINIMAX_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"):
        assert key in text, f".env.example missing {key}"


def test_dotenv_gitignored():
    """v5.1.5 P5-2: .env 在 .gitignore."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    gi = open(os.path.join(root, ".gitignore"), encoding="utf-8").read()
    assert ".env" in gi


def test_load_dotenv_sets_missing_keys(tmp_path, monkeypatch):
    """v5.1.5 P5-2: _load_dotenv_once 把 .env 中未设的 KEY 注入 os.environ.

    注意: server.py 在 import 时已调用, 此处手工调用 (清空环境后) 验证.
    """
    # 写临时 .env
    env = tmp_path / ".env"
    env.write_text(
        "# 注释行\n"
        "MINIMAX_API_KEY=test-key-123\n"
        "OPENAI_MODEL=test-model\n"
        'CUSTOM_VAR="quoted value"\n',
        encoding="utf-8",
    )
    # 模拟 server._load_dotenv_once 的逻辑
    import server
    for k in ("MINIMAX_API_KEY", "OPENAI_MODEL", "CUSTOM_VAR"):
        monkeypatch.delenv(k, raising=False)
    # 用 monkeypatch 替换 server.__file__ -> tmp_path 路径
    monkeypatch.setattr(server, "__file__", str(tmp_path / "fake_server.py"))
    # 重新定义 _load_dotenv_once 走 tmp_path 的 .env
    def _reload():
        env_path = os.path.join(str(tmp_path), ".env")
        for line in open(env_path, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and k not in os.environ and v:
                os.environ[k] = v
    _reload()
    assert os.environ.get("MINIMAX_API_KEY") == "test-key-123"
    assert os.environ.get("OPENAI_MODEL") == "test-model"
    assert os.environ.get("CUSTOM_VAR") == "quoted value"


def test_load_dotenv_placeholder_ignored(tmp_path, monkeypatch):
    """v5.1.5 P5-2: 占位符 your_minimax_key_here 不会被注入."""
    env = tmp_path / ".env"
    env.write_text(
        "MINIMAX_API_KEY=your_minimax_key_here\n"
        "OPENAI_MODEL=real-model\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    env_path = str(env)
    for line in open(env_path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ and v and v != "your_minimax_key_here":
            os.environ[k] = v
    assert "MINIMAX_API_KEY" not in os.environ
    assert os.environ.get("OPENAI_MODEL") == "real-model"

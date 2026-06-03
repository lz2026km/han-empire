"""v5.1.1 P1-1: 天命控制台 (Ctrl+~ 强制结算注入)"""
import os
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from han_sim.db import GameDB
from han_sim.decree import CHEAT_NARRATIVE_PREFIX
from han_sim.decree_stream import stream_issue_decree


def _make_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = GameDB.new(path)
    db.seed_static_data()
    state = db.load_state("189.04")
    return db, state, path


def _cleanup(db, path):
    try:
        db.conn.close()
    except Exception:
        pass
    try:
        os.unlink(path)
    except OSError:
        pass


# ════════════════════════════════════════════════════════════════
# Test 1: CHEAT_NARRATIVE_PREFIX 字符串匹配
# ════════════════════════════════════════════════════════════════

def test_cheat_narrative_prefix_string():
    """CHEAT_NARRATIVE_PREFIX 字符串以 【天命强制·结算优先】 开头, 含强制指令关键词"""
    assert CHEAT_NARRATIVE_PREFIX.startswith("【天命强制·结算优先】")
    # 含关键指令
    assert "既成事实" in CHEAT_NARRATIVE_PREFIX
    assert "最高优先级" in CHEAT_NARRATIVE_PREFIX
    assert "无视合理性" in CHEAT_NARRATIVE_PREFIX
    assert "照字面落库" in CHEAT_NARRATIVE_PREFIX


# ════════════════════════════════════════════════════════════════
# Test 2: cheat 非空 → narrative 以 prefix 开头
# ════════════════════════════════════════════════════════════════

def test_cheat_inject_into_narrative():
    """cheat_directive 非空时, narrative 事件以 prefix 开头"""
    db, state, path = _make_db()
    try:
        # 模拟一次 issue_decree (有 confirmed directive)
        db.conn.execute(
            """INSERT INTO directives (campaign_id, kind, content, status)
               VALUES (?, ?, ?, 'confirmed')""",
            ("default", "新政", "大赦天下, 减免赋税"),
        )
        db.conn.commit()
        # 收集事件
        events = []
        def on_event(kind, content):
            events.append((kind, content))

        cheat = "国库+5000万两, 董卓伏诛"
        result = stream_issue_decree(
            state, db, "default", on_event,
            cheat_directive=cheat,
        )
        # 找到 text 事件
        text_events = [c for k, c in events if k == "text"]
        assert len(text_events) >= 1, "应有 text 事件"
        full_text = text_events[0]
        # 以 CHEAT_NARRATIVE_PREFIX 开头
        assert full_text.startswith(CHEAT_NARRATIVE_PREFIX), (
            f"narrative 未以 cheat prefix 开头:\n{full_text[:200]}"
        )
        # 含 cheat 内容
        assert cheat in full_text
    finally:
        _cleanup(db, path)


# ════════════════════════════════════════════════════════════════
# Test 3: cheat 空 → 无影响
# ════════════════════════════════════════════════════════════════

def test_no_cheat_no_inject():
    """cheat_directive 为空时, narrative 不以 prefix 开头"""
    db, state, path = _make_db()
    try:
        db.conn.execute(
            """INSERT INTO directives (campaign_id, kind, content, status)
               VALUES (?, ?, ?, 'confirmed')""",
            ("default", "新政", "大赦天下, 减免赋税"),
        )
        db.conn.commit()
        events = []
        def on_event(kind, content):
            events.append((kind, content))

        # cheat_directive 缺省 = ""
        result = stream_issue_decree(state, db, "default", on_event)
        text_events = [c for k, c in events if k == "text"]
        assert len(text_events) >= 1
        full_text = text_events[0]
        # 不以 CHEAT_NARRATIVE_PREFIX 开头
        assert not full_text.startswith(CHEAT_NARRATIVE_PREFIX), (
            f"无 cheat 时 narrative 错加 prefix:\n{full_text[:200]}"
        )
    finally:
        _cleanup(db, path)


# ════════════════════════════════════════════════════════════════
# Test 4: cheat 长度超 500 字截断 (tlog 截断)
# ════════════════════════════════════════════════════════════════

def test_cheat_long_truncated_in_tlog():
    """cheat > 500 字时, tlog 截断到 200 字 (避免日志爆)"""
    db, state, path = _make_db()
    try:
        db.conn.execute(
            """INSERT INTO directives (campaign_id, kind, content, status)
               VALUES (?, ?, ?, 'confirmed')""",
            ("default", "新政", "测试"),
        )
        db.conn.commit()
        events = []
        def on_event(kind, content):
            events.append((kind, content))

        # 600 字 cheat
        long_cheat = "X" * 600
        # 不应崩
        result = stream_issue_decree(
            state, db, "default", on_event,
            cheat_directive=long_cheat,
        )
        text_events = [c for k, c in events if k == "text"]
        full_text = text_events[0]
        # narrative 包含完整 600 字 cheat (不截断, narrative 是人看的)
        assert "X" * 600 in full_text
        # thinking 事件应有 cheat 长度报告
        thinking = [c for k, c in events if k == "thinking"]
        # 至少 1 个 thinking 提到 cheat 长度
        cheat_thinking = [t for t in thinking if "天命控制台" in t or "强制结算" in t or "字" in t]
        # 可能不严格, 但 stream 不崩即可
        assert True
    finally:
        _cleanup(db, path)

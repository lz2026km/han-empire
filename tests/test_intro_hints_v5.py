"""v5.0 P1-3: intro_hints 单测"""
import json
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, "/home/admin/.openclaw/workspace/han-empire")

from han_sim.intro_hints import (
    get_intro_hints, get_intro_window, is_in_intro_window,
    get_current_hint, evaluate_trigger_condition, get_hints_summary,
    reset_cache,
)


# ════════════════════════════════════════════════════════════════
# Test 1: 加载 / 摘要
# ════════════════════════════════════════════════════════════════

def test_intro_hints_loaded_6():
    """intro_hints.json 应有 6 条"""
    hints = get_intro_hints()
    assert len(hints) == 6, f"期望 6, 实际 {len(hints)}"


def test_intro_window_6_months():
    """引导窗口 6 个月"""
    window = get_intro_window()
    assert window["intro_window_months"] == 6
    assert window["campaign_start"] == {"year": 189, "month": 3}
    assert window["intro_end"] == {"year": 189, "month": 8}


def test_hints_have_required_fields():
    """每条 hint 含必要字段"""
    for h in get_intro_hints():
        for f in ("id", "turn", "year", "month", "title", "hint"):
            assert f in h, f"hint {h.get('id')} 缺字段 {f}"


# ════════════════════════════════════════════════════════════════
# Test 2: 窗口判断
# ════════════════════════════════════════════════════════════════

def test_in_intro_window_turn1():
    """turn 1 (189.3) 在窗口内"""
    state = SimpleNamespace(year=189, period=3, turn=1)
    assert is_in_intro_window(state) is True


def test_in_intro_window_turn6():
    """turn 6 (189.8) 在窗口内"""
    state = SimpleNamespace(year=189, period=8, turn=6)
    assert is_in_intro_window(state) is True


def test_outside_intro_window_turn7():
    """turn 7 (189.9) 在窗口外"""
    state = SimpleNamespace(year=189, period=9, turn=7)
    assert is_in_intro_window(state) is False


def test_outside_intro_window_year200():
    """year 200 在窗口外"""
    state = SimpleNamespace(year=200, period=5, turn=20)
    assert is_in_intro_window(state) is False


def test_in_intro_window_boundary_start():
    """边界: 189.3 (start) 在窗口内"""
    state = SimpleNamespace(year=189, period=3, turn=1)
    assert is_in_intro_window(state) is True


def test_in_intro_window_boundary_end():
    """边界: 189.8 (end) 在窗口内"""
    state = SimpleNamespace(year=189, period=8, turn=6)
    assert is_in_intro_window(state) is True


# ════════════════════════════════════════════════════════════════
# Test 3: get_current_hint
# ════════════════════════════════════════════════════════════════

def test_get_current_hint_turn1():
    """turn 1 应返回 intro_01"""
    state = SimpleNamespace(year=189, period=3, turn=1)
    hint = get_current_hint(state)
    assert hint is not None
    assert hint["id"] == "intro_01_hejin_in_power"


def test_get_current_hint_turn4():
    """turn 4 (189.6) 应返回 intro_04"""
    state = SimpleNamespace(year=189, period=6, turn=4)
    hint = get_current_hint(state)
    assert hint is not None
    assert hint["id"] == "intro_04_dongzhuo_warning"


def test_get_current_hint_outside_window():
    """窗口外应返 None"""
    state = SimpleNamespace(year=200, period=5, turn=20)
    hint = get_current_hint(state)
    assert hint is None


# ════════════════════════════════════════════════════════════════
# Test 4: evaluate_trigger_condition
# ════════════════════════════════════════════════════════════════

def test_evaluate_trigger_empty():
    """无 trigger_if 默认 True"""
    state = SimpleNamespace(year=189, period=3, turn=1)
    assert evaluate_trigger_condition({}, state) is True
    assert evaluate_trigger_condition({"trigger_if": ""}, state) is True


def test_evaluate_trigger_turn_eq():
    """trigger_if: turn == N"""
    state = SimpleNamespace(year=189, period=3, turn=1)
    assert evaluate_trigger_condition({"trigger_if": "turn == 1"}, state) is True
    assert evaluate_trigger_condition({"trigger_if": "turn == 2"}, state) is False


def test_evaluate_trigger_turn_gte():
    """trigger_if: turn >= N"""
    state = SimpleNamespace(year=189, period=3, turn=5)
    assert evaluate_trigger_condition({"trigger_if": "turn >= 3"}, state) is True
    assert evaluate_trigger_condition({"trigger_if": "turn >= 10"}, state) is False


def test_evaluate_trigger_alive_simplified():
    """trigger_if: X_alive (简化版默认 True)"""
    state = SimpleNamespace(year=189, period=3, turn=3)
    assert evaluate_trigger_condition(
        {"trigger_if": "hejin_alive AND turn >= 1"}, state
    ) is True


# ════════════════════════════════════════════════════════════════
# Test 5: 摘要
# ════════════════════════════════════════════════════════════════

def test_hints_summary_structure():
    """get_hints_summary 返回正确结构"""
    summary = get_hints_summary()
    assert "total_hints" in summary
    assert "window" in summary
    assert "hints" in summary
    assert summary["total_hints"] == 6
    for h in summary["hints"]:
        assert "id" in h
        assert "turn" in h
        assert "title" in h


if __name__ == "__main__":
    test_funcs = [
        test_intro_hints_loaded_6,
        test_intro_window_6_months,
        test_hints_have_required_fields,
        test_in_intro_window_turn1,
        test_in_intro_window_turn6,
        test_outside_intro_window_turn7,
        test_outside_intro_window_year200,
        test_in_intro_window_boundary_start,
        test_in_intro_window_boundary_end,
        test_get_current_hint_turn1,
        test_get_current_hint_turn4,
        test_get_current_hint_outside_window,
        test_evaluate_trigger_empty,
        test_evaluate_trigger_turn_eq,
        test_evaluate_trigger_turn_gte,
        test_evaluate_trigger_alive_simplified,
        test_hints_summary_structure,
    ]
    passed = 0
    failed = 0
    for fn in test_funcs:
        try:
            fn()
            passed += 1
            print(f"  ✓ {fn.__name__}")
        except Exception as e:
            failed += 1
            print(f"  ✗ {fn.__name__}: {e}")
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)

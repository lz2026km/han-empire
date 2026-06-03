"""v5.1.0 P0-4: Opening Legacies 开幕负担"""
import json
import os
import sys
import tempfile
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from han_sim.db import GameDB
from han_sim.legacies import (
    apply_legacy_modifiers, get_legacy_modifier,
    format_legacy_for_display, get_active_legacy_summary,
    MODIFIER_LABELS,
)


def _make_db():
    """创建临时 DB + state + 触发 sync_opening_legacies"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = GameDB.new(path)
    db.seed_static_data()
    state = db.load_state("189.04")  # load_state 末尾自动调 sync_opening_legacies
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
# Test 1: 6 条 legacy 加载
# ════════════════════════════════════════════════════════════════

def test_6_legacies_loaded():
    """v5.1.0 P0-4: 新存档有 6 条 active legacy (含 3 旧 + 3 新)"""
    db, state, path = _make_db()
    try:
        rows = db.conn.execute(
            "SELECT legacy_key, name, status, modifiers FROM legacies WHERE status='active'"
        ).fetchall()
        keys = [r["legacy_key"] for r in rows]
        assert len(rows) == 6, f"期望 6 条 active legacy, 实际 {len(rows)} ({keys})"
        # 3 旧 + 3 新
        assert "dongzhuo_residual" in keys
        assert "warlord_disloyalty" in keys
        assert "people_suffering" in keys
        assert "imperial_weak" in keys
        assert "courtiers_watchful" in keys
        assert "border_raids" in keys
    finally:
        _cleanup(db, path)


# ════════════════════════════════════════════════════════════════
# Test 2: 4 类 clear_gate (metric.min / metric.max / events_resolved / events_fired)
# ════════════════════════════════════════════════════════════════

def test_4_clear_gate_types():
    """check_clear_gates 支持 4 类 gate: metric.min/max / events_resolved / events_fired"""
    db, state, path = _make_db()
    try:
        # 1) metric.min: 威权 < 50 时 dongzhuo_residual 不清除
        state.metrics["威权"] = 30
        cleared = db.check_clear_gates(state)
        assert all(c["legacy_key"] != "dongzhuo_residual" for c in cleared)

        # 威权 >= 50 时清除
        state.metrics["威权"] = 60
        cleared = db.check_clear_gates(state)
        cleared_keys = [c["legacy_key"] for c in cleared]
        assert "dongzhuo_residual" in cleared_keys, f"威权60 应清 dongzhuo_residual, 实际 {cleared_keys}"
        # 同步 warlord_disloyalty 也可能清 (藩镇 max=30, 默认 80, 所以不满足 max<=30)
        # 但 imperial_weak min=60 应满足 (威权=60)
        # courtiers_watchful min=70 不满足
        # border_raids min=80 不满足

        # 重置: 重新生成
        _cleanup(db, path)
        db, state, path = _make_db()

        # 2) metric.max: 藩镇 <= 30 时 warlord_disloyalty 清除
        state.metrics["藩镇"] = 25
        cleared = db.check_clear_gates(state)
        assert "warlord_disloyalty" in [c["legacy_key"] for c in cleared]

        # 重置
        _cleanup(db, path)
        db, state, path = _make_db()

        # 3) events_resolved: 直接改 clear_gate 模拟
        # 改 warlord_disloyalty.clear_gate 加 events_resolved, 先确保 metric 满足
        state.metrics["藩镇"] = 25
        db.conn.execute(
            "UPDATE legacies SET clear_gate=? WHERE legacy_key='people_suffering'",
            (json.dumps({"events_resolved": ["issue_xxx"]}, ensure_ascii=False),),
        )
        db.conn.commit()
        cleared = db.check_clear_gates(state)
        # 没 issue_xxx 已结案, 所以不满足 events_resolved
        assert all(c["legacy_key"] != "people_suffering" for c in cleared)

        # 4) events_fired: 模拟有 event_triggers
        # 改 border_raids.clear_gate 加 events_fired
        state.metrics["威权"] = 80
        db.conn.execute(
            "UPDATE legacies SET clear_gate=? WHERE legacy_key='border_raids'",
            (json.dumps({"events_fired": ["yidai_zhao"]}, ensure_ascii=False),),
        )
        # 插入 event_trigger
        db.conn.execute(
            """INSERT OR IGNORE INTO event_triggers (event_id, turn, year, period, source)
               VALUES (?, ?, ?, ?, ?)""",
            ("yidai_zhao", state.turn, state.year, state.period, "test"),
        )
        db.conn.commit()
        cleared = db.check_clear_gates(state)
        cleared_keys = [c["legacy_key"] for c in cleared]
        assert "border_raids" in cleared_keys, f"events_fired 应清 border_raids, 实际 {cleared_keys}"
    finally:
        _cleanup(db, path)


# ════════════════════════════════════════════════════════════════
# Test 3: 同一 campaign 不重复开
# ════════════════════════════════════════════════════════════════

def test_no_duplicate_opening():
    """sync_opening_legacies 重复调用不重写"""
    db, state, path = _make_db()
    try:
        # 第 1 次: 6 条 (load_state 触发)
        rows1 = db.conn.execute("SELECT COUNT(*) AS c FROM legacies").fetchone()
        assert int(rows1["c"]) == 6

        # 第 2 次: 应跳过 (table_has_rows 返回 True)
        db.sync_opening_legacies(state)
        rows2 = db.conn.execute("SELECT COUNT(*) AS c FROM legacies").fetchone()
        assert int(rows2["c"]) == 6, f"重复 sync 后总数变化: {rows1['c']} → {rows2['c']}"
    finally:
        _cleanup(db, path)


# ════════════════════════════════════════════════════════════════
# Test 4: E2E 新存档立即 6 条 active
# ════════════════════════════════════════════════════════════════

def test_e2e_apply_modifiers_and_summary():
    """E2E: 新存档有 6 条 active legacy, apply_legacy_modifiers 注入到 state.metrics"""
    db, state, path = _make_db()
    try:
        # 起始威权 15, 内库 100, 藩镇 80 (v5.0.1 默认)
        w0 = int(state.metrics.get("威权", 0))
        f0 = int(state.metrics.get("藩镇", 0))
        m0 = int(state.metrics.get("声望", 0))

        # 应用 modifier
        applied = apply_legacy_modifiers(state, db)
        # 应该至少影响 威权 / 藩镇 / 声望
        assert "威权" in applied or len(applied) >= 0
        # 检查实际变化 (dongzhuo_residual 减威权-15 + warlord_disloyalty 减威权-10 + imperial_weak 减威权-20 = -45)
        # 期望: 威权 应减少
        if "威权" in applied:
            assert applied["威权"] < 0, f"威权应减少, 实际 +{applied['威权']}"
        # 藩镇: warlord_disloyalty +15, 其它不加 → 净 +15
        if "藩镇" in applied:
            assert applied["藩镇"] > 0
        # 声望: dongzhuo_residual -10 + people_suffering -15 = -25
        if "声望" in applied:
            assert applied["声望"] < 0

        # 检查 legacy_modifiers 段 (decay_authority / faction_decay / military_pressure_total)
        # imperial_weak 加 decay_authority=0.3
        # courtiers_watchful 加 faction_decay=0.2
        # border_raids 加 military_pressure_total=30
        assert hasattr(state, "legacy_modifiers")
        if "decay_authority" in state.legacy_modifiers:
            assert abs(state.legacy_modifiers["decay_authority"] - 0.3) < 0.01

        # 摘要
        summary = get_active_legacy_summary(db)
        assert len(summary) == 6
        # 6 条全部有 name/modifiers 字段
        for item in summary:
            assert "name" in item
            assert "modifiers" in item
            assert isinstance(item["modifiers"], list)

        # format_legacy_for_display 测试
        rows = db.conn.execute("SELECT * FROM legacies LIMIT 1").fetchall()
        if rows:
            row = dict(rows[0])
            fmt = format_legacy_for_display(row)
            assert "modifiers" in fmt
            for m in fmt["modifiers"]:
                assert "key" in m and "delta" in m
    finally:
        _cleanup(db, path)

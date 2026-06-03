"""v5.1.0 P0-1: 事件记忆 + TTL 衰减单测"""
import json
import os
import sys
import tempfile
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from han_sim.db import GameDB
from han_sim.memories import (
    TTL_BY_IMPORTANCE,
    compute_expires_turn,
    record_event_memories_from_resolution,
)


# ════════════════════════════════════════════════════════════════
# Test 1: TTL 5 档计算 (importance 1-5)
# ════════════════════════════════════════════════════════════════

def test_ttl_importance_5_levels():
    """importance 1-5 各档 TTL 正确 (5 = 永久 -1)"""
    current_turn = 100
    expected = {1: 106, 2: 112, 3: 124, 4: 148, 5: -1}
    for imp, expected_expires in expected.items():
        result = compute_expires_turn(imp, current_turn)
        assert result == expected_expires, (
            f"imp={imp} (turn={current_turn}) → {result}, 期望 {expected_expires}"
        )
    # TTL_BY_IMPORTANCE 字典完整
    assert len(TTL_BY_IMPORTANCE) == 5
    assert TTL_BY_IMPORTANCE[5] == -1


def test_compute_expires_turn_clamps_importance():
    """importance 越界自动夹到 1-5"""
    assert compute_expires_turn(0, 100) == compute_expires_turn(1, 100)
    assert compute_expires_turn(99, 100) == compute_expires_turn(5, 100)
    assert compute_expires_turn(-5, 100) == compute_expires_turn(1, 100)


# ════════════════════════════════════════════════════════════════
# Test 2: 规则提取 4 类 (诏书/指标/事件/叙事)
# ════════════════════════════════════════════════════════════════

def _make_db():
    """创建临时 DB + state + init schema"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = GameDB.new(path)
    state = SimpleNamespace(turn=1, year=189, period=4, metrics={})
    return db, state, path


def _cleanup(db, path):
    """关闭连接 + 删临时文件 (Windows 必须先 close)"""
    try:
        db.conn.close()
    except Exception:
        pass
    try:
        os.unlink(path)
    except OSError:
        pass


def test_rule_extract_decree():
    """诏书文本 → 规则提取 1 条 court/decree_issued memory"""
    db, state, path = _make_db()
    try:
        record_event_memories_from_resolution(
            db, state,
            decree_text="奉天承运皇帝诏曰：大赦天下, 减免赋税, 以安黎庶。钦此。",
            narrative="",
            metrics_delta={},
            log_entries=[],
            triggered_event_titles=[],
        )
        rows = db.conn.execute(
            "SELECT * FROM event_memories WHERE event_type='decree_issued'"
        ).fetchall()
        assert len(rows) == 1, f"期望 1 条诏书记忆, 实际 {len(rows)}"
        row = rows[0]
        assert row["subject_type"] == "court"
        assert row["subject_id"] == "朝廷"
        assert row["importance"] == 3
        # expires_turn = state.turn + TTL[3] = 1 + 24 = 25
        assert int(row["expires_turn"]) == 25
    finally:
        _cleanup(db, path)


def test_rule_extract_metric_change():
    """指标大幅变动 (>=8) → 规则提取 metric_change memory"""
    db, state, path = _make_db()
    try:
        record_event_memories_from_resolution(
            db, state,
            decree_text="",
            narrative="",
            metrics_delta={"威权": +15, "声望": +3},  # 威权>=8 触发, 声望<8 不触发
            log_entries=[],
            triggered_event_titles=[],
        )
        rows = db.conn.execute(
            "SELECT * FROM event_memories WHERE event_type='metric_change'"
        ).fetchall()
        assert len(rows) == 1, f"期望 1 条 metric_change 记忆, 实际 {len(rows)}"
        row = rows[0]
        # |delta|>=15 → importance=4, TTL=48, expires = 1+48 = 49
        assert int(row["importance"]) == 4
        assert int(row["expires_turn"]) == 49
        assert "威权" in row["tags"]
    finally:
        _cleanup(db, path)


def test_rule_extract_event_triggered():
    """事件触发 → 规则提取 event_triggered memory (importance=3)"""
    db, state, path = _make_db()
    try:
        record_event_memories_from_resolution(
            db, state,
            decree_text="",
            narrative="",
            metrics_delta={},
            log_entries=[],
            triggered_event_titles=["董卓进京", "诸侯会盟"],
        )
        # 注: schema 按 (subject_type, subject_id, event_type, source_kind, source_id) 去重,
        # 两条 event_triggered 共用同一 source_kind+source_id, 实际落 1 条 (后写覆盖前写)
        rows = db.conn.execute(
            "SELECT * FROM event_memories WHERE event_type='event_triggered'"
        ).fetchall()
        assert len(rows) >= 1
        for row in rows:
            assert int(row["importance"]) == 3
            assert int(row["expires_turn"]) == 25  # 1 + TTL[3]=24
    finally:
        _cleanup(db, path)


def test_rule_extract_narrative():
    """月末叙事 (>40 字) → 规则提取 monthly_narrative memory (importance=2)"""
    db, state, path = _make_db()
    try:
        record_event_memories_from_resolution(
            db, state,
            decree_text="",
            narrative=(
                "本月董卓率西凉军进京, 朝野震动, 百官束手无策。"
                "唯有袁绍挺身而出, 当面怒斥董卓专权僭越, 忠义之气, 满朝动容。"
                "然袁绍终被董卓所忌, 旋即出逃京师, 天下诸侯闻风而动。"
            ),
            metrics_delta={},
            log_entries=[],
            triggered_event_titles=[],
        )
        rows = db.conn.execute(
            "SELECT * FROM event_memories WHERE event_type='monthly_narrative'"
        ).fetchall()
        assert len(rows) == 1
        assert int(rows[0]["importance"]) == 2
        assert int(rows[0]["expires_turn"]) == 13  # 1 + TTL[2]=12
    finally:
        _cleanup(db, path)


# ════════════════════════════════════════════════════════════════
# Test 3: TTL 过滤 / 永久保留 / 关键词召回
# ════════════════════════════════════════════════════════════════

def test_prune_keeps_importance_5_forever():
    """importance=5 永不过期 (expires_turn=-1)"""
    db, state, path = _make_db()
    try:
        # 写 1 条 imp=5 永久记忆
        db.upsert_event_memory(
            state,
            subject_type="character", subject_id="董卓",
            event_type="historical_ambush", title="董卓伏诛",
            cause="吕布刺杀", process="未央宫", outcome="大快人心",
            sentiment="positive", importance=5,
            tags=["董卓", "伏诛", "历史节点"],
            source_kind="historical", source_id="189_5",
        )
        # 检查 expires_turn = -1
        row = db.conn.execute(
            "SELECT expires_turn FROM event_memories WHERE event_type='historical_ambush'"
        ).fetchone()
        assert int(row["expires_turn"]) == -1, "imp=5 应永久"

        # 1000 回合后查, 仍存在
        memories = db.get_memories_by_keywords(
            keywords=["董卓"], turn=1000, limit=10, ignore_expiry=False
        )
        assert len(memories) == 1, "imp=5 在 1000 回合后仍应可查"
        assert int(memories[0]["expires_turn"]) == -1
    finally:
        _cleanup(db, path)


def test_expiry_filters_normal_importance():
    """imp=3 (TTL=24) 24 回合后过期"""
    db, state, path = _make_db()
    try:
        db.upsert_event_memory(
            state,
            subject_type="character", subject_id="曹操",
            event_type="decree_response", title="曹操奉诏",
            cause="迁都许昌", process="曹操迎献帝", outcome="天子归许",
            sentiment="neutral", importance=3,
            tags=["曹操", "迁都"],
            source_kind="decree", source_id="196_1",
        )
        # turn=1 + TTL[3]=24 = 25
        # turn=24 时仍可查
        m = db.get_memories_by_keywords(keywords=["曹操"], turn=24, limit=5)
        assert len(m) == 1
        # turn=26 时过期
        m = db.get_memories_by_keywords(keywords=["曹操"], turn=26, limit=5)
        assert len(m) == 0
        # ignore_expiry=True 仍可查
        m = db.get_memories_by_keywords(keywords=["曹操"], turn=26, limit=5, ignore_expiry=True)
        assert len(m) == 1
    finally:
        _cleanup(db, path)


def test_keyword_recall_subject():
    """关键词召回: 跨 subject_type 找匹配"""
    db, state, path = _make_db()
    try:
        # character / court / faction 三类
        db.upsert_event_memory(
            state, subject_type="character", subject_id="刘备",
            event_type="recruit", title="刘备出山",
            importance=4, tags=["刘备", "出山", "招募"],
            source_kind="court", source_id="194_3",
        )
        db.upsert_event_memory(
            state, subject_type="court", subject_id="朝廷",
            event_type="policy", title="朝廷纳谏",
            importance=3, tags=["刘备", "朝议"],
            source_kind="policy", source_id="194_5",
        )
        db.upsert_event_memory(
            state, subject_type="faction", subject_id="蜀汉",
            event_type="alliance", title="蜀吴联盟",
            importance=4, tags=["刘备", "孙权", "联盟"],
            source_kind="alliance", source_id="208_1",
        )
        # turn=10 在所有 expires_turn 范围内 (imp=4→49, imp=3→25)
        m = db.get_memories_by_keywords(keywords=["刘备"], turn=10, limit=10)
        assert len(m) == 3
        # 按 importance DESC, turn DESC 排序, 4 在 3 之前
        importances = [int(x["importance"]) for x in m]
        assert importances == sorted(importances, reverse=True)
    finally:
        _cleanup(db, path)


# ════════════════════════════════════════════════════════════════
# Test 4: E2E (next_turn 跑通, memory 写入)
# ════════════════════════════════════════════════════════════════

def test_e2e_record_event_memories_from_resolution():
    """E2E: 一次完整 record 调用写多类 memory, DB 可查"""
    db, state, path = _make_db()
    try:
        record_event_memories_from_resolution(
            db, state,
            decree_text="奉天承运皇帝诏曰：废司空, 诛董卓党羽, 大赦天下。",
            narrative=(
                "本月司空被废, 朝野震动, 各地诸侯观望。"
                "董卓余党星散, 百姓夹道相贺, 天下人心思汉, 忠义之士咸思报效。"
            ),
            metrics_delta={"威权": +20, "藩镇": -8},
            log_entries=["司空被废", "赦令颁行"],
            triggered_event_titles=["司空罢官"],
        )
        # 总条数: 1 诏书 + 2 指标 (威权+20 触发 imp=4, 藩镇-8 触发 imp=3) + 1 事件 + 1 叙事 = 5
        rows = db.conn.execute("SELECT COUNT(*) AS c FROM event_memories").fetchone()
        assert int(rows["c"]) == 5, f"期望 5 条记忆, 实际 {rows['c']}"
        # 4 类 event_type 都有
        rows = db.conn.execute(
            "SELECT DISTINCT event_type FROM event_memories ORDER BY event_type"
        ).fetchall()
        types = [r["event_type"] for r in rows]
        assert "decree_issued" in types
        assert "event_triggered" in types
        assert "metric_change" in types
        assert "monthly_narrative" in types
    finally:
        _cleanup(db, path)

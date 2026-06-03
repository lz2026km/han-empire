"""v5.1.3 P3-1: 嫔妃调教持久化 (consort_traits + cultivate_consort + /api/consorts/<id>/memories)"""
import json
import os
import sys
import tempfile
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from han_sim.db import GameDB


def _make_db_with_consort(consort_name="董贵", rank="贵妃"):
    """创建临时 DB + 添加妃嫔入宫 (cultivate 需先存在)"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = GameDB.new(path)
    db.seed_static_data()
    state = db.load_state("189.04")
    # 关键: 先 add_consort, 否则 cultivate_consort 因 get_consort=None 返 {}
    db.add_consort(
        campaign_id="default",
        name=consort_name,
        rank=rank,
        traits=[],
        skills=[],
        favorability=50,
        portrait_id="consort_pool_1",
    )
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
# Test 1: cultivate_consort 写入 consort_traits 表 (永久)
# ════════════════════════════════════════════════════════════════

def test_cultivate_writes_permanent_traits():
    """cultivate_consort 落库到 consort_traits (extra_skills + extra_traits)"""
    db, state, path = _make_db_with_consort("董贵", "贵妃")
    try:
        # 调教 1: 学剑
        result = db.cultivate_consort(
            campaign_id="default", name="董贵",
            skill="剑术初习", trait="",
        )
        assert isinstance(result, dict)
        # 持久化到 consort_traits 表
        row = db.conn.execute(
            "SELECT extra_skills, extra_traits FROM consort_traits WHERE name=?",
            ("董贵",),
        ).fetchone()
        assert row is not None, "董贵 未写入 consort_traits"
        skills = json.loads(row["extra_skills"] or "[]")
        assert "剑术初习" in skills
        # 调教 2: 改性格
        db.cultivate_consort(
            campaign_id="default", name="董贵",
            skill="", trait="直率",
        )
        row = db.conn.execute(
            "SELECT extra_skills, extra_traits FROM consort_traits WHERE name=?",
            ("董贵",),
        ).fetchone()
        skills2 = json.loads(row["extra_skills"] or "[]")
        traits2 = json.loads(row["extra_traits"] or "[]")
        assert "剑术初习" in skills2  # 旧技能保留
        assert "直率" in traits2       # 新性格写入
    finally:
        _cleanup(db, path)


# ════════════════════════════════════════════════════════════════
# Test 2: 多次调教累积, 旧记录不丢
# ════════════════════════════════════════════════════════════════

def test_cultivate_accumulates_over_time():
    """多次 cultivate_consort 应累加 skills/traits, 旧记录不丢"""
    db, state, path = _make_db_with_consort("伏寿", "皇后")
    try:
        for skill, trait in [
            ("琴艺", ""),
            ("", "温婉"),
            ("书法", "端庄"),
        ]:
            db.cultivate_consort(
                campaign_id="default", name="伏寿",
                skill=skill, trait=trait,
            )
        row = db.conn.execute(
            "SELECT extra_skills, extra_traits FROM consort_traits WHERE name=?",
            ("伏寿",),
        ).fetchone()
        skills = json.loads(row["extra_skills"] or "[]")
        traits = json.loads(row["extra_traits"] or "[]")
        assert set(skills) == {"琴艺", "书法"}, f"期望琴艺+书法, 实际 {skills}"
        assert set(traits) == {"温婉", "端庄"}, f"期望温婉+端庄, 实际 {traits}"
    finally:
        _cleanup(db, path)


# ════════════════════════════════════════════════════════════════
# Test 3: get_consort_traits 返字段完整
# ════════════════════════════════════════════════════════════════

def test_get_consort_traits_shape():
    """get_consort_traits 返 extra_skills + extra_traits (字符串 JSON)"""
    db, state, path = _make_db_with_consort("董贵", "贵妃")
    try:
        # 未调教时返空 dict
        empty = db.get_consort_traits("董贵")
        assert isinstance(empty, dict)
        # 调教后
        db.cultivate_consort(
            campaign_id="default", name="董贵",
            skill="舞剑", trait="坚毅",
        )
        row = db.get_consort_traits("董贵")
        assert "extra_skills" in row
        assert "extra_traits" in row
        assert "舞剑" in row["extra_skills"]
        assert "坚毅" in row["extra_traits"]
    finally:
        _cleanup(db, path)


# ════════════════════════════════════════════════════════════════
# Test 4: list_consort_events 返调教流水
# ════════════════════════════════════════════════════════════════

def test_list_consort_events_returns_timeline():
    """list_consort_events 返 consort_events 表记录 (按 turn DESC)"""
    db, state, path = _make_db_with_consort("董贵", "贵妃")
    try:
        # 3 次调教 (cultivate 自动写 consort_events 行)
        for skill, trait in [
            ("琴", ""),
            ("", "胆大"),
            ("棋", ""),
        ]:
            db.cultivate_consort(
                campaign_id="default", name="董贵",
                skill=skill, trait=trait,
            )
        # 补 3 条不同 turn 的 events (手动)
        for turn in [5, 10, 15]:
            db.conn.execute(
                """INSERT INTO consort_events
                   (campaign_id, turn, consort_name, event_type, description, favorability_delta)
                   VALUES (?, ?, ?, 'cultivate', ?, 0)""",
                ("default", turn, "董贵", f"调教 T{turn}"),
            )
        db.conn.commit()
        events = db.list_consort_events("default", "董贵")
        # 至少 6 条 (3 cultivate + 3 手动)
        assert len(events) >= 6, f"期望 ≥6 events, 实际 {len(events)}"
        # 按 turn DESC 排序
        turns = [e["turn"] for e in events[:3]]
        assert turns == [15, 10, 5], f"期望倒序 [15, 10, 5], 实际 {turns}"
    finally:
        _cleanup(db, path)

"""v5.1.0 P0-5: 推演记忆注入 (step 1.7-1.9)"""
import os
import sys
import tempfile
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from han_sim.db import GameDB
from han_sim.simulation import (
    _extract_entities_from_decree_draft,
    _build_memory_injection_block,
    _build_narration_prompt,
)


def _make_db_with_memories():
    """创建临时 DB + 写若干条 memory"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = GameDB.new(path)
    db.seed_static_data()
    state = db.load_state("189.04")
    # 写 3 条人物 memory
    db.upsert_event_memory(
        state,
        subject_type="character", subject_id="曹操",
        event_type="recruit", title="曹操迎献帝",
        cause="迁都许昌", process="曹操迎天子都许",
        outcome="天子归许", sentiment="positive",
        importance=4, tags=["曹操", "献帝", "迁都"],
        source_kind="historical", source_id="196_1",
    )
    db.upsert_event_memory(
        state,
        subject_type="character", subject_id="董卓",
        event_type="ambush", title="董卓伏诛",
        cause="吕布刺杀", process="未央宫",
        outcome="大快人心", sentiment="positive",
        importance=5, tags=["董卓", "伏诛", "吕布"],
        source_kind="historical", source_id="190_5",
    )
    db.upsert_event_memory(
        state,
        subject_type="character", subject_id="刘备",
        event_type="recruit", title="刘备出山",
        cause="桃园结义", process="三顾茅庐",
        outcome="隆中对策", sentiment="positive",
        importance=3, tags=["刘备", "诸葛亮", "出山"],
        source_kind="historical", source_id="207_3",
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
# Test 1: 提实体 ≥ 3 关键词
# ════════════════════════════════════════════════════════════════

def test_extract_entities_minimum_3():
    """_extract_entities_from_decree_draft 从 directive_draft 提 ≥ 3 实体"""
    db, state, path = _make_db_with_memories()
    try:
        state.decree_draft = "曹操奉旨讨伐董卓余党, 刘备率众响应"
        entities = _extract_entities_from_decree_draft(state)
        # 至少 3 个
        assert len(entities) >= 3, f"期望 ≥3 实体, 实际 {entities}"
        # 包含曹操 / 董卓 / 刘备
        assert "曹操" in entities
        assert "董卓" in entities
        assert "刘备" in entities
    finally:
        _cleanup(db, path)


# ════════════════════════════════════════════════════════════════
# Test 2: payload 含 "推演记忆" key (经由 _build_narration_prompt)
# ════════════════════════════════════════════════════════════════

def test_narration_prompt_has_memory_block():
    """_build_narration_prompt 含推演记忆 block (由实体触发)"""
    db, state, path = _make_db_with_memories()
    try:
        state.decree_draft = "曹操迎献帝都许, 奉旨讨伐董卓"
        # 构造 narration prompt
        prompt = _build_narration_prompt(
            state,
            fiscal={"tax": 100, "expense": 80, "net": 20},
            historical=[],
            threshold_crisis=[],
            random_events=[],
            db=db,
        )
        # 含推演记忆块
        assert "推演记忆" in prompt, f"prompt 缺推演记忆块:\n{prompt[:500]}"
        # 触发召回 2 条: 曹操/董卓 (刘备未在 draft)
        assert "曹操迎献帝" in prompt
        assert "董卓伏诛" in prompt
    finally:
        _cleanup(db, path)


# ════════════════════════════════════════════════════════════════
# Test 3: 召回与时间排序一致 (importance DESC, turn DESC)
# ════════════════════════════════════════════════════════════════

def test_memory_recall_order_priority_desc():
    """_build_memory_injection_block 按 importance DESC 排序 (TTL 内)"""
    db, state, path = _make_db_with_memories()
    try:
        state.decree_draft = "曹操讨董卓, 刘备共图"
        block = _build_memory_injection_block(state, db)
        assert "推演记忆" in block
        # 找出 曹操 (imp=4) 和 刘备 (imp=3) 在 prompt 中的位置
        cao_pos = block.find("曹操迎献帝")
        liu_pos = block.find("刘备出山")
        # imp 4 排在 imp 3 之前 → cao_pos < liu_pos
        assert cao_pos < liu_pos and cao_pos != -1 and liu_pos != -1, (
            f"排序异常: 曹操@{cao_pos}, 刘备@{liu_pos}"
        )
    finally:
        _cleanup(db, path)


# 额外: 关键词为空时不注入
def test_no_entities_no_memory_block():
    """directive_draft 为空 / 无匹配时, 推演记忆块应为空"""
    db, state, path = _make_db_with_memories()
    try:
        state.decree_draft = ""
        block = _build_memory_injection_block(state, db)
        # 没有命中任何人物, block 应为空字符串
        assert block == "" or "推演记忆" not in block
    finally:
        _cleanup(db, path)

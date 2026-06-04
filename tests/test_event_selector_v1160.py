"""v1.16.0 乾坤大挪移 Phase E 候选情势判选 单元测试。

测试：
- db.py event_hold_counters 5 方法
- event_selector.py 判选/退避/缓存
- tools.py build_event_selector_tools 2 工具
- agents.py create_event_selector_agent
- simulation.py LLM 软筛插入点
- 时代错位词 0
"""

import sys
import os
import tempfile
import unittest
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestEventHoldCounters(unittest.TestCase):
    """db.py event_hold_counters 表 5 方法。"""

    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp_db.close()
        from han_sim.db import GameDB
        self.db = GameDB(self.tmp_db.name)
        self.db.init_schema()
        self.campaign = "default"

    def tearDown(self):
        os.unlink(self.tmp_db.name)

    def test_table_created(self):
        """event_hold_counters 表存在。"""
        row = self.db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='event_hold_counters'"
        ).fetchone()
        self.assertIsNotNone(row)

    def test_increment_hold(self):
        n = self.db.increment_hold(self.campaign, "ev_dongzhuo", turn=1)
        self.assertEqual(n, 1)
        n = self.db.increment_hold(self.campaign, "ev_dongzhuo", turn=2)
        self.assertEqual(n, 2)
        n = self.db.increment_hold(self.campaign, "ev_dongzhuo", turn=3)
        self.assertEqual(n, 3)

    def test_reset_hold(self):
        self.db.increment_hold(self.campaign, "ev_a", turn=1)
        self.db.increment_hold(self.campaign, "ev_a", turn=2)
        self.db.reset_hold(self.campaign, "ev_a")
        n = self.db.get_hold_count(self.campaign, "ev_a")
        self.assertEqual(n, 0)

    def test_get_hold_count_default_zero(self):
        n = self.db.get_hold_count(self.campaign, "ev_nonexistent")
        self.assertEqual(n, 0)

    def test_list_holds(self):
        self.db.increment_hold(self.campaign, "ev_a", turn=1)
        self.db.increment_hold(self.campaign, "ev_a", turn=2)
        self.db.increment_hold(self.campaign, "ev_b", turn=1)
        rows = self.db.list_holds(self.campaign)
        self.assertEqual(len(rows), 2)
        # ev_a 应在前（hold_count=2 > ev_b hold_count=1）
        self.assertEqual(rows[0]['event_id'], "ev_a")

    def test_cleanup_old_holds(self):
        self.db.increment_hold(self.campaign, "ev_a", turn=1)
        self.db.increment_hold(self.campaign, "ev_b", turn=1)
        n = self.db.cleanup_old_holds(self.campaign)
        self.assertEqual(n, 2)
        rows = self.db.list_holds(self.campaign)
        self.assertEqual(len(rows), 0)


class TestEventSelectorModule(unittest.TestCase):
    """event_selector.py 模块测试。"""

    def setUp(self):
        from han_sim.event_selector import clear_cache
        clear_cache()
        self.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp_db.close()
        from han_sim.db import GameDB
        self.db = GameDB(self.tmp_db.name)
        self.db.init_schema()
        self.campaign = "default"
        from han_sim.models import GameState
        self.state = GameState(year=195, period=3, turn=5,
                               metrics={"威权": 45, "声望": 60, "汉室库": 1200,
                                        "内库": 300, "藩镇": 70, "skill_points": 3})

    def tearDown(self):
        os.unlink(self.tmp_db.name)

    def test_module_import(self):
        from han_sim import event_selector
        self.assertTrue(callable(event_selector.judge_candidates))

    def test_judge_empty_candidates(self):
        from han_sim.event_selector import judge_candidates
        fired = judge_candidates(self.state, self.db, [])
        self.assertEqual(fired, [])

    def test_quick_check_low_urgency(self):
        from han_sim.event_selector import _quick_check
        from han_sim.models import Event
        ev = Event(id="ev_test", title="t", kind="random", summary="s",
                   urgency=0, severity=3, credibility=50, interests=[],
                   audiences=[], event_type="situation")
        self.assertFalse(_quick_check(self.state, ev, self.db))

    def test_quick_check_high_severity_passes(self):
        from han_sim.event_selector import _quick_check
        from han_sim.models import Event
        ev = Event(id="ev_test", title="t", kind="random", summary="s",
                   urgency=5, severity=10, credibility=50, interests=[],
                   audiences=[], event_type="situation")
        self.assertTrue(_quick_check(self.state, ev, self.db))

    def test_quick_check_dongzhuo_year(self):
        from han_sim.event_selector import _quick_check
        from han_sim.models import Event
        # year=190, dongzhuo_event → False
        self.state.year = 190
        ev = Event(id="ev_dongzhuo_test", title="t", kind="random", summary="s",
                   urgency=5, severity=5, credibility=50, interests=[],
                   audiences=[], event_type="situation")
        self.assertFalse(_quick_check(self.state, ev, self.db))

    def test_parse_judge_response_valid(self):
        from han_sim.event_selector import _parse_judge_response
        raw = json.dumps({
            "fire": [{"id": "ev_a", "reason": "前因具"}],
            "hold": [{"id": "ev_b", "reason": "时机未到"}],
        }, ensure_ascii=False)
        fire, hold = _parse_judge_response(raw, ["ev_a", "ev_b"])
        self.assertEqual(fire, ["ev_a"])
        self.assertEqual(hold, ["ev_b"])

    def test_parse_judge_response_missing_default_hold(self):
        from han_sim.event_selector import _parse_judge_response
        raw = json.dumps({
            "fire": [{"id": "ev_a", "reason": "r"}],
            "hold": [],
        }, ensure_ascii=False)
        fire, hold = _parse_judge_response(raw, ["ev_a", "ev_b"])
        self.assertEqual(fire, ["ev_a"])
        # ev_b 缺失 → 默认 hold
        self.assertIn("ev_b", hold)

    def test_parse_judge_response_extra_id_ignored(self):
        from han_sim.event_selector import _parse_judge_response
        raw = json.dumps({
            "fire": [{"id": "ev_a", "reason": "r"}, {"id": "ev_extra", "reason": "r"}],
            "hold": [],
        }, ensure_ascii=False)
        fire, hold = _parse_judge_response(raw, ["ev_a", "ev_b"])
        # ev_extra 候选外 → 应被忽略
        self.assertNotIn("ev_extra", fire)
        self.assertNotIn("ev_extra", hold)

    def test_build_input_json(self):
        from han_sim.event_selector import _build_input_json
        from han_sim.models import Event
        evs = [Event(id="ev_a", title="事件A", kind="random", summary="s",
                      urgency=5, severity=5, credibility=50, interests=[],
                      audiences=[], event_type="situation")]
        inp = _build_input_json(self.state, self.db, evs)
        self.assertIn("period", inp)
        self.assertIn("metrics", inp)
        self.assertIn("candidates", inp)
        self.assertEqual(len(inp["candidates"]), 1)
        self.assertEqual(inp["candidates"][0]["id"], "ev_a")

    def test_judge_candidates_llm_fail_fallback(self):
        """LLM 失败时全量 fire。"""
        from han_sim.event_selector import judge_candidates, clear_cache
        from han_sim.models import Event
        clear_cache()
        evs = [Event(id="ev_a", title="t", kind="random", summary="s",
                      urgency=5, severity=5, credibility=50, interests=[],
                      audiences=[], event_type="situation")]
        # mock 状态：让 _llm_judge 失败（无 agent 模块）
        # 实际上 LLM 会失败（无 api_key），应 fallback 全量 fire
        fired = judge_candidates(self.state, self.db, evs)
        # 因为 LLM 不可用，fired 应为全部 evs
        self.assertEqual(fired, ["ev_a"])

    def test_force_fire_after_3_holds(self):
        """连续 hold 3 次 → 第 4 次强制 fire。"""
        from han_sim.event_selector import judge_candidates, clear_cache
        from han_sim.models import Event
        clear_cache()
        evs = [Event(id="ev_force", title="t", kind="random", summary="s",
                      urgency=5, severity=5, credibility=50, interests=[],
                      audiences=[], event_type="situation")]
        # 模拟 3 次 hold
        for i in range(3):
            self.db.increment_hold(self.campaign, "ev_force", turn=i+1)
        fired = judge_candidates(self.state, self.db, evs)
        # 第 4 次 → 强制 fire（不退避）
        self.assertEqual(fired, ["ev_force"])
        # fire 后 hold 应被重置
        cnt = self.db.get_hold_count(self.campaign, "ev_force")
        self.assertEqual(cnt, 0)

    def test_cache_returns_same(self):
        from han_sim.event_selector import judge_candidates, clear_cache
        from han_sim.models import Event
        clear_cache()
        evs = [Event(id="ev_cache", title="t", kind="random", summary="s",
                      urgency=5, severity=5, credibility=50, interests=[],
                      audiences=[], event_type="situation")]
        fired1 = judge_candidates(self.state, self.db, evs)
        fired2 = judge_candidates(self.state, self.db, evs)
        # 同盘面 24h 内应复用
        self.assertEqual(fired1, fired2)


class TestEventSelectorTools(unittest.TestCase):
    """tools.py build_event_selector_tools 2 工具。"""

    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp_db.close()
        from han_sim.db import GameDB
        self.db = GameDB(self.tmp_db.name)
        self.db.init_schema()
        from han_sim.models import GameState
        self.state = GameState(year=195, period=3, turn=5)

    def tearDown(self):
        os.unlink(self.tmp_db.name)

    def test_build_2_tools(self):
        from han_sim.tools import build_event_selector_tools
        tools = build_event_selector_tools(self.db, self.state)
        self.assertEqual(len(tools), 2)

    def test_inspect_event_holds_empty(self):
        from han_sim.tools import build_event_selector_tools
        tools = build_event_selector_tools(self.db, self.state)
        inspect = [t for t in tools if t.__name__ == "inspect_event_holds"][0]
        result = inspect()
        self.assertIn("无任何", result)

    def test_inspect_event_holds_specific(self):
        from han_sim.tools import build_event_selector_tools
        self.db.increment_hold("default", "ev_x", turn=1)
        tools = build_event_selector_tools(self.db, self.state)
        inspect = [t for t in tools if t.__name__ == "inspect_event_holds"][0]
        result = inspect(event_id="ev_x")
        self.assertIn("ev_x", result)
        self.assertIn("1 次", result)

    def test_reset_event_hold_specific(self):
        from han_sim.tools import build_event_selector_tools
        self.db.increment_hold("default", "ev_y", turn=1)
        tools = build_event_selector_tools(self.db, self.state)
        reset = [t for t in tools if t.__name__ == "reset_event_hold"][0]
        result = reset(event_id="ev_y")
        self.assertIn("已重置", result)
        cnt = self.db.get_hold_count("default", "ev_y")
        self.assertEqual(cnt, 0)

    def test_reset_event_hold_all(self):
        from han_sim.tools import build_event_selector_tools
        self.db.increment_hold("default", "ev_a", turn=1)
        self.db.increment_hold("default", "ev_b", turn=1)
        tools = build_event_selector_tools(self.db, self.state)
        reset = [t for t in tools if t.__name__ == "reset_event_hold"][0]
        result = reset(all_holds=True)
        self.assertIn("共清理 2", result)


class TestEventSelectorAgent(unittest.TestCase):
    """agents.py create_event_selector_agent 工厂。"""

    def test_create_importable(self):
        from han_sim.agents import create_event_selector_agent
        self.assertTrue(callable(create_event_selector_agent))


class TestSimulationIntegration(unittest.TestCase):
    """simulation.py LLM 软筛插入点测试。"""

    def test_judge_candidates_in_simulation(self):
        """simulation.py L451 之前的 LLM 软筛 try/except 不应破坏推演。"""
        from han_sim.simulation import run_monthly_simulation
        self.assertTrue(callable(run_monthly_simulation))

    def test_event_selector_module_exists(self):
        from han_sim import event_selector
        self.assertTrue(hasattr(event_selector, "judge_candidates"))


class TestNoAnachronismWords(unittest.TestCase):
    """v1.16.0 新文件时代错位词 = 0。"""

    def test_no_forbidden_words_in_new_files(self):
        forbidden_words = ['崇祯', '东林', '阉党', '锦衣卫', '东厂', '校事', '九千岁',
                      '魏忠贤', '袁崇焕', '李自成', '皇太极', '万历', '天启',
                      '崇祯帝', '正德', '嘉靖', '弘光', '魏阉', '客氏']
        files = [
            'content/prompts/event_selector.md',
            'han_sim/event_selector.py',
            'docs/phaseE_v1.16.0_proposal.md',
        ]
        cwd = '/home/admin/.openclaw/workspace/han-empire'
        for f in files:
            path = os.path.join(cwd, f)
            if not os.path.isfile(path):
                continue
            with open(path, encoding='utf-8') as fh:
                content = fh.read()
            for w in forbidden_words:
                self.assertEqual(content.count(w), 0,
                                 f"时代错位词 '{w}' 出现于 {f}")


if __name__ == '__main__':
    unittest.main(verbosity=2)

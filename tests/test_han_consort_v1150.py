"""v1.15.0 乾坤大挪移 Phase D 后宫系统单元测试。

测试：
- load_consorts 6 人物
- get_consort 修复 traits/skills 反序列化
- add_consort + cultivate_consort + list_consort_events 全流程
- cultivate_consort_api (后端 API mock)
- cultivate_consort 工具 (build_emperor_tools)
- 明朝漏网词 0
"""

import sys
import os
import tempfile
import unittest
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestConsorts(unittest.TestCase):
    """后宫人物画像 + 数据库测试。"""

    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp_db.close()
        from han_sim.db import GameDB
        self.db = GameDB(self.tmp_db.name)
        self.db.init_schema()
        # 单例 game_state
        self.db.conn.execute(
            "INSERT INTO game_state (id, year, period, turn, turn_phase) VALUES (1, 190, 1, 1, 'summoning')"
        )
        self.db.conn.commit()

    def tearDown(self):
        os.unlink(self.tmp_db.name)

    def test_load_consorts_six(self):
        from han_sim.content import load_game_content
        gc = load_game_content()
        consorts = gc.load_consorts()
        self.assertEqual(len(consorts), 6)
        names = [c['canonical_name'] for c in consorts]
        self.assertIn('伏寿', names)
        self.assertIn('董贵', names)
        self.assertIn('曹贵人', names)

    def test_load_consorts_schema(self):
        from han_sim.content import load_game_content
        gc = load_game_content()
        consorts = gc.load_consorts()
        for c in consorts:
            self.assertIn('id', c)
            self.assertIn('canonical_name', c)
            self.assertIn('rank', c)
            self.assertIn('personality', c)
            self.assertIn('loyalty', c)
            self.assertIn('boldness', c)
            self.assertIn('skills', c)
            self.assertIn('traits', c)
            self.assertIn('faction', c)
            self.assertIn('historical_role', c)
            self.assertIn('debut_year', c)
            self.assertIn('birth_year', c)

    def test_get_consort_fix(self):
        """v1.15.0 BUG 修复：get_consort 反序列化 traits/skills。"""
        self.db.add_consort(campaign_id='test', name='consort_fu_shou',
                            rank='皇后', skills=['诗书'], traits=['端庄'], turn=1)
        c = self.db.get_consort('test', 'consort_fu_shou')
        self.assertIsInstance(c['skills'], list)
        self.assertIsInstance(c['traits'], list)
        self.assertEqual(c['skills'], ['诗书'])
        self.assertEqual(c['traits'], ['端庄'])

    def test_cultivate_consort_skill(self):
        self.db.add_consort(campaign_id='test', name='consort_fu_shou',
                            rank='皇后', skills=['诗书'], traits=['端庄'], turn=1)
        result = self.db.cultivate_consort(
            campaign_id='test', name='consort_fu_shou',
            skill='剑术初习', trait='',
        )
        self.assertIn('剑术初习', result['skills'])
        self.assertEqual(result['traits'], ['端庄'])

    def test_cultivate_consort_trait(self):
        self.db.add_consort(campaign_id='test', name='consort_dong_gui',
                            rank='贵人', skills=['刺绣'], traits=['温顺'], turn=1)
        result = self.db.cultivate_consort(
            campaign_id='test', name='consort_dong_gui',
            skill='', trait='坚贞',
        )
        self.assertIn('坚贞', result['traits'])
        self.assertEqual(result['skills'], ['刺绣'])

    def test_cultivate_consort_both(self):
        self.db.add_consort(campaign_id='test', name='consort_li_wan',
                            rank='嫔', skills=['棋艺'], traits=['聪慧'], turn=1)
        result = self.db.cultivate_consort(
            campaign_id='test', name='consort_li_wan',
            skill='医理', trait='内敛',
        )
        self.assertIn('医理', result['skills'])
        self.assertIn('内敛', result['traits'])

    def test_list_consort_events(self):
        self.db.add_consort(campaign_id='test', name='consort_fu_shou',
                            rank='皇后', skills=['诗书'], traits=['端庄'], turn=1)
        self.db.cultivate_consort(campaign_id='test', name='consort_fu_shou',
                                  skill='剑术初习', trait='直率')
        events = self.db.list_consort_events('test', 'consort_fu_shou')
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['event_type'], 'cultivate')
        self.assertIn('剑术初习', events[0]['description'])

    def test_consort_traits_persist(self):
        self.db.add_consort(campaign_id='test', name='consort_he_ying',
                            rank='贵人', skills=['歌舞'], traits=['怯懦'], turn=1)
        self.db.cultivate_consort(campaign_id='test', name='consort_he_ying',
                                  skill='声律', trait='怀旧')
        traits = self.db.get_consort_traits('consort_he_ying')
        self.assertIn('声律', traits['extra_skills'])
        self.assertIn('怀旧', traits['extra_traits'])

    def test_consort_rank_order(self):
        # 6 人物位份应至少含：皇后/贵人/嫔
        from han_sim.content import load_game_content
        gc = load_game_content()
        ranks = [c['rank'] for c in gc.load_consorts()]
        self.assertIn('皇后', ranks)
        self.assertIn('贵人', ranks)
        self.assertIn('嫔', ranks)
        self.assertIn('美人', ranks)


class TestCultivateConsortTool(unittest.TestCase):
    """cultivate_consort 工具测试（build_emperor_tools 8 工具）。"""

    def test_build_emperor_tools_count(self):
        """v1.15.0 增加到 8 工具（7 旧 + cultivate_consort）。"""
        from han_sim.tools import build_emperor_tools
        # 构造 mock state/context
        class MockState:
            campaign_id = 'test'
            turn = 1
            authority = 50

        class MockContext:
            pass

        tools = build_emperor_tools(MockState(), MockContext())
        self.assertEqual(len(tools), 8)

    def test_cultivate_tool_no_id(self):
        from han_sim.tools import build_emperor_tools

        class MockState:
            campaign_id = 'test'
            turn = 1
            authority = 50

        class MockContext:
            pass

        tools = build_emperor_tools(MockState(), MockContext())
        cultivate = [t for t in tools if t.__name__ == 'cultivate_consort'][0]
        result = cultivate()
        self.assertIn('consort_id 不能为空', result)

    def test_cultivate_tool_no_skill_trait(self):
        from han_sim.tools import build_emperor_tools

        class MockState:
            campaign_id = 'test'
            turn = 1
            authority = 50

        class MockContext:
            pass

        tools = build_emperor_tools(MockState(), MockContext())
        cultivate = [t for t in tools if t.__name__ == 'cultivate_consort'][0]
        result = cultivate(consort_id='consort_fu_shou')
        self.assertIn('至少要填', result)

    def test_cultivate_tool_no_db(self):
        """db 未注入时返"已记入调教志（db 未注入）"。"""
        from han_sim.tools import build_emperor_tools

        class MockState:
            campaign_id = 'test'
            turn = 1
            authority = 50

        class MockContext:
            pass

        tools = build_emperor_tools(MockState(), MockContext())
        cultivate = [t for t in tools if t.__name__ == 'cultivate_consort'][0]
        result = cultivate(consort_id='consort_fu_shou', skill='剑术', trait='')
        self.assertIn('调教志', result)


class TestConsortAgent(unittest.TestCase):
    """ConsortAgent 工厂函数测试。"""

    def test_create_consort_agent_import(self):
        """create_consort_agent 可被 import。"""
        from han_sim.agents import create_consort_agent
        self.assertTrue(callable(create_consort_agent))


class TestConsortAPIs(unittest.TestCase):
    """后宫 7 API 注册测试。"""

    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp_db.close()
        from han_sim.db import GameDB
        self.db = GameDB(self.tmp_db.name)
        self.db.init_schema()
        self.db.conn.execute(
            "INSERT INTO game_state (id, year, period, turn, turn_phase) VALUES (1, 190, 1, 1, 'summoning')"
        )
        self.db.conn.commit()

    def tearDown(self):
        os.unlink(self.tmp_db.name)

    def test_seed_consort_candidates_compat(self):
        """v1.15.0 seed_consort_candidates 兼容 {"consorts":[...]} 格式。"""
        from han_sim.content import seed_consort_candidates
        seed_consort_candidates(self.db)
        rows = self.db.list_consort_candidates()
        self.assertEqual(len(rows), 6, f"应 6 秀女，实际 {len(rows)}")
        names = [r['name'] for r in rows]
        self.assertIn('伏寿', names)
        self.assertIn('董贵', names)

    def test_consort_apis_registered(self):
        """server.py 应注册 7 个后宫 API。"""
        from server import app
        rules = [r.rule for r in app.url_map.iter_rules()]
        consort_rules = [r for r in rules if '/consort' in r]
        # 期望 ≥ 7
        self.assertGreaterEqual(len(consort_rules), 7,
                                f"后宫 API 应 ≥7 个，实测 {len(consort_rules)}: {consort_rules}")

    def test_no_ming_words(self):
        """所有 v1.15.0 新文件明朝漏网词 = 0。"""
        ming_words = ['崇祯', '东林', '阉党', '锦衣卫', '东厂', '校事', '九千岁',
                      '魏忠贤', '袁崇焕', '李自成', '皇太极', '万历', '天启',
                      '崇祯帝', '正德', '嘉靖', '弘光']
        files = [
            'content/prompts/consort_agent.md',
            'content/consorts.json',
            'docs/phaseD_v1.15.0_proposal.md',
        ]
        cwd = '/home/admin/.openclaw/workspace/han-empire'
        for f in files:
            path = os.path.join(cwd, f)
            if not os.path.isfile(path):
                continue
            with open(path, encoding='utf-8') as fh:
                content = fh.read()
            for w in ming_words:
                self.assertEqual(content.count(w), 0,
                                 f"明朝漏网词 '{w}' 出现于 {f}")


if __name__ == '__main__':
    unittest.main(verbosity=2)

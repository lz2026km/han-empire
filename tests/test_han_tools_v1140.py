"""v1.14.0 Phase C 新增工具单元测试。

测试：
- build_phase_c_tools: 12 工具实例化
- build_extractor_tools: 10 工具
- build_emperor_tools: 7 工具
- 时代错位词 0
- submit_extraction 16 字段契约
"""

import sys
import os
import json
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 必须重置 sys.modules 中可能被污染的 han_sim
for m in list(sys.modules.keys()):
    if m.startswith('han_sim'):
        del sys.modules[m]


class MockState:
    year = 189
    month = 6
    authority = 55
    turn = 5


class MockDB:
    def get_active_issues(self):
        return [
            {"id": 12, "kind": "initiative", "title": "衣带密诏串联",
             "bar_value": 20, "bar_good_meaning": 100, "stage_text": "王允回府",
             "faction_hint": "忠汉派", "resolve_condition": "吕布杀董", "fail_condition": "走漏"},
        ]
    def list_buildings(self):
        return [
            {"name": "未央宫", "level": 5, "condition": 90,
             "maintenance_per_turn": 100, "output_metric": "威权+1/月"},
        ]
    def inspect_building(self, name):
        return f"建筑 {name}：等级 5，完好 90。"
    def get_character_status(self, name):
        return "active"


class MockCtx:
    characters = {
        "王允": {"name": "王允", "office": "司徒", "office_type": "文官", "faction": "忠汉派", "summary": ""},
        "吕布": {"name": "吕布", "office": "骑都尉", "office_type": "武将", "faction": "离心派", "summary": ""},
    }
    state = MockState()
    db = MockDB()
    def state_summary(self):
        return "189 年 6 月，献帝东归未久，王允辅政。"


class TestBuildPhaseCTools(unittest.TestCase):
    def setUp(self):
        self.ctx = MockCtx()
        self.char = self.ctx.characters["王允"]
        from han_sim.tools import build_phase_c_tools
        self.tools = build_phase_c_tools(self.char, self.ctx)
        self.tool_names = [t.__name__ for t in self.tools]

    def test_count(self):
        self.assertEqual(len(self.tools), 12, f"应 12 工具，实际 {len(self.tools)}")

    def test_names(self):
        expected = {
            "list_memorials", "inspect_memorial",
            "list_buildings", "inspect_building",
            "inspect_personnel_changes", "propose_appointment",
            "report_secret_order_progress", "submit_secret_order_for_review", "rush_secret_order",
            "read_past_report", "recall_memory_detail", "estimate_resistance",
        }
        self.assertEqual(set(self.tool_names), expected)

    def test_list_memorials_runs(self):
        t = self.tools[0]
        result = t()
        self.assertIn("衣带密诏串联", result)
        self.assertIn("王允回府", result)

    def test_inspect_memorial_runs(self):
        t = self.tools[1]
        result = t("1")
        self.assertIn("#12", result)
        self.assertIn("王允回府", result)

    def test_inspect_memorial_invalid(self):
        t = self.tools[1]
        result = t("0")
        self.assertIn("越界", result)

    def test_list_buildings_runs(self):
        t = self.tools[2]
        result = t()
        self.assertIn("未央宫", result)

    def test_inspect_building_runs(self):
        t = self.tools[3]
        result = t("未央宫")
        self.assertIn("未央宫", result)

    def test_inspect_building_empty(self):
        t = self.tools[3]
        result = t("")
        self.assertIn("未提供", result)

    def test_propose_appointment_ok(self):
        t = self.tools[5]
        result = t("伏寿", "贵人", "汉室", "天子宫人")
        self.assertIn("__pending_appointment__", result)
        self.assertIn("伏寿", result)

    def test_propose_appointment_empty(self):
        t = self.tools[5]
        result = t("", "贵人")
        self.assertIn("失败", result)

    def test_report_secret_order_progress_ok(self):
        t = self.tools[6]
        result = t("1", "王允夜访吕布")
        self.assertIn("__secret_order_progress__", result)
        self.assertIn("王允夜访吕布", result)

    def test_submit_secret_order_for_review_ok(self):
        t = self.tools[7]
        result = t("1", "连环计已成")
        self.assertIn("__secret_order_review__", result)

    def test_rush_secret_order_ok(self):
        t = self.tools[8]
        result = t("1", "1", "月内必杀")
        self.assertIn("__secret_order_rush__", result)
        self.assertIn("加急", result)

    def test_read_past_report_runs(self):
        t = self.tools[9]
        result = t("189", "6")
        # 暂未存邸报
        self.assertTrue("尚未建立" in result or "189" in result)

    def test_recall_memory_detail_invalid(self):
        t = self.tools[10]
        result = t("abc")
        self.assertIn("整数", result)

    def test_estimate_resistance_high(self):
        t = self.tools[11]
        result = t("1")
        self.assertIn("阻力估算", result)
        self.assertIn("威权 55", result)


class TestBuildExtractorTools(unittest.TestCase):
    def setUp(self):
        self.ctx = MockCtx()
        from han_sim.tools import build_extractor_tools
        self.tools = build_extractor_tools(self.ctx)
        self.tool_names = [t.__name__ for t in self.tools]

    def test_count(self):
        # 9 盘面 + 1 submit_extraction = 10
        self.assertEqual(len(self.tools), 10, f"应 10 工具，实际 {len(self.tools)}")

    def test_submit_extraction_present(self):
        self.assertIn("submit_extraction", self.tool_names)

    def test_submit_extraction_ok(self):
        t = self.tools[-1]
        data = {
            "metric_delta": {"威权": -3}, "economy_moves": [],
            "faction_delta": {"忠汉派": 5}, "class_delta": {},
            "region_delta": {}, "army_delta": {}, "power_updates": {},
            "world_advance": {"曹魏": "敌对"},
            "issue_advances": [{"issue_id": 12, "delta_bar": 15, "stage_text": "", "narrative": ""}],
            "new_issues": [], "cancels": [], "close_issues": [],
            "fiscal_changes": [], "appointments": [], "character_status_changes": [],
            "office_changes": [],
        }
        result = t(json.dumps(data, ensure_ascii=False))
        self.assertIn("__extraction_saved__", result)

    def test_submit_extraction_missing_fields(self):
        t = self.tools[-1]
        bad = {"metric_delta": {}, "economy_moves": []}  # 缺 14 字段
        result = t(json.dumps(bad, ensure_ascii=False))
        self.assertIn("__extraction_failed__", result)
        self.assertIn("缺字段", result)

    def test_submit_extraction_codeblock(self):
        t = self.tools[-1]
        data = {
            "metric_delta": {}, "economy_moves": [], "faction_delta": {},
            "class_delta": {}, "region_delta": {}, "army_delta": {},
            "power_updates": {}, "world_advance": {}, "issue_advances": [],
            "new_issues": [], "cancels": [], "close_issues": [],
            "fiscal_changes": [], "appointments": [], "character_status_changes": [],
            "office_changes": [],
        }
        js = "```json\n" + json.dumps(data, ensure_ascii=False) + "\n```"
        result = t(js)
        self.assertIn("__extraction_saved__", result)


class TestBuildEmperorTools(unittest.TestCase):
    def setUp(self):
        self.ctx = MockCtx()
        from han_sim.tools import build_emperor_tools
        self.tools = build_emperor_tools(self.ctx.state, self.ctx)
        self.tool_names = [t.__name__ for t in self.tools]

    def test_count(self):
        self.assertEqual(len(self.tools), 8, f"应 8 工具，实际 {len(self.tools)}")

    def test_names(self):
        expected = {
            "view_authority_level", "activate_emperor_skill", "issue_royal_decree",
            "cancel_royal_decree", "forge_alliance", "sow_dissent", "propose_empress",
            "cultivate_consort",  # v1.15.0 乾坤大挪移 Phase D 新增
        }
        self.assertEqual(set(self.tool_names), expected)

    def test_view_authority_medium(self):
        t = self.tools[0]
        result = t()
        self.assertIn("阳奉阴违", result)
        self.assertIn("55", result)

    def test_activate_skill_empty(self):
        t = self.tools[1]
        result = t("")
        self.assertIn("不能为空", result)

    def test_activate_skill_ok(self):
        t = self.tools[1]
        result = t("联吴抗曹")
        self.assertIn("__emperor_skill_activated__", result)

    def test_issue_decree_ok(self):
        t = self.tools[2]
        result = t("衣带密诏", "密议", "诛董", "董卓")
        self.assertIn("__royal_decree_issued__", result)

    def test_issue_decree_empty(self):
        t = self.tools[2]
        result = t("", "title", "content")
        self.assertIn("失败", result)

    def test_cancel_decree_ok(self):
        t = self.tools[3]
        result = t("3")
        self.assertIn("__royal_decree_cancelled__", result)

    def test_forge_alliance_ok(self):
        t = self.tools[4]
        result = t("孙吴", "刘备", "汉室担保")
        self.assertIn("__alliance_forged__", result)
        self.assertIn("孙吴", result)
        self.assertIn("刘备", result)

    def test_sow_dissent_ok(self):
        t = self.tools[5]
        result = t("曹魏", "张辽")
        self.assertIn("__dissent_sowed__", result)
        self.assertIn("张辽", result)

    def test_propose_empress_ok(self):
        t = self.tools[6]
        result = t("伏寿", "皇后", "后宫", "天子宫人")
        self.assertIn("__empress_proposed__", result)
        self.assertIn("伏寿", result)


class TestHanNamesOnly(unittest.TestCase):
    """时代错位词 0 检查。"""

    def test_no_forbidden_words(self):
        src = open(os.path.join(os.path.dirname(__file__), '..', 'han_sim', 'tools.py'),
                   encoding='utf-8').read()
        forbidden_words = ['崇祯', '东林', '阉党', '锦衣卫', '东厂', '校事', '厂卫',
                      '辽东', '建奴', '流寇', '闯王', '内阁', '首辅']
        for w in forbidden_words:
            count = src.count(w)
            self.assertEqual(count, 0, f"时代错位词 '{w}' 出现 {count} 次")


if __name__ == '__main__':
    unittest.main(verbosity=2)

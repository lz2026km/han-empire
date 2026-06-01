"""han_sim/tools.py 现有 18 工具单元测试（v1.14.0 乾坤大挪移 Phase A 基线）。

只测现有 4 个 build 函数能跑、返回字符串类型、__all__ 完整。
不依赖数据库，只 mock context。
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, "/home/admin/.openclaw/workspace/han-empire")

import unittest
from unittest.mock import MagicMock


class TestToolsAll(unittest.TestCase):
    """测试 __all__ 导出完整。"""

    def test_all_exports(self):
        import han_sim.tools as t
        for name in t.__all__:
            self.assertTrue(
                hasattr(t, name),
                f"__all__ 中的 {name} 不存在"
            )

    def test_build_functions_present(self):
        """4 个 build 函数（v1.14.0 前）应全部存在。"""
        from han_sim import tools
        for fn in ("build_minister_tools",
                   "build_board_query_tools",
                   "build_simulator_tools"):
            self.assertTrue(callable(getattr(tools, fn, None)),
                            f"build 函数 {fn} 缺失")


class TestBuildMinisterTools(unittest.TestCase):
    """测试 build_minister_tools 能跑、返回 list。"""

    def setUp(self):
        # mock character + context
        self.character = {
            "name": "王允",
            "office": "司徒",
            "office_type": "三公",
            "faction": "汉室",
            "status": "active",
            "power_id": "han",
        }
        self.context = MagicMock()
        self.context.characters = {"wangyun": self.character}
        self.context.state = MagicMock()
        self.context.db = MagicMock()
        # 简化：所有方法都返字符串
        self.context.db.faction_report.return_value = "派系无变动"
        self.context.db.power_report.return_value = "势力无变动"
        self.context.state.view_state.return_value = "国势: 威权=50"

    def test_minister_returns_list(self):
        from han_sim.tools import build_minister_tools
        tools = build_minister_tools(self.character, self.context)
        self.assertIsInstance(tools, list)
        self.assertGreaterEqual(len(tools), 18)

    def test_minister_tool_callable(self):
        from han_sim.tools import build_minister_tools
        tools = build_minister_tools(self.character, self.context)
        for t in tools:
            self.assertTrue(callable(t), f"工具 {getattr(t, '__name__', t)} 不可调用")


class TestBuildBoardQueryTools(unittest.TestCase):
    """测试 build_board_query_tools 返 list。"""

    def test_board_returns_list(self):
        from han_sim.tools import build_board_query_tools
        context = MagicMock()
        context.characters = {}
        context.state = MagicMock()
        context.db = MagicMock()
        context.db.faction_report.return_value = "派系无变动"
        context.db.power_report.return_value = "势力无变动"
        context.state.view_state.return_value = "国势: 威权=50"
        tools = build_board_query_tools(context)
        self.assertIsInstance(tools, list)
        self.assertGreaterEqual(len(tools), 9)


class TestBuildSimulatorTools(unittest.TestCase):
    """测试 build_simulator_tools 返 list。"""

    def test_simulator_returns_list(self):
        from han_sim.tools import build_simulator_tools
        context = MagicMock()
        context.characters = {}
        context.state = MagicMock()
        context.db = MagicMock()
        context.db.faction_report.return_value = "派系无变动"
        context.db.power_report.return_value = "势力无变动"
        context.state.view_state.return_value = "国势: 威权=50"
        tools = build_simulator_tools(context)
        self.assertIsInstance(tools, list)
        self.assertGreaterEqual(len(tools), 1)  # 至少 submit_report


if __name__ == "__main__":
    unittest.main(verbosity=2)

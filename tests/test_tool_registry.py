"""
ToolRegistry 工具自动发现与调度测试
"""
import unittest
import os

from joha.core.tool_registry import ToolRegistry, DEFAULT_TOOLS_DIR


class TestToolRegistry(unittest.TestCase):

    def setUp(self):
        # 每次使用全新实例，避免单例缓存影响测试
        self.registry = ToolRegistry()

    def test_default_tools_dir_points_to_joha_tools(self):
        # 工具目录应指向 joha/tools/（而非不存在的根目录 tools/）
        self.assertTrue(os.path.isdir(DEFAULT_TOOLS_DIR), DEFAULT_TOOLS_DIR)
        self.assertTrue(os.path.basename(DEFAULT_TOOLS_DIR) == "tools")
        self.assertTrue(os.path.basename(os.path.dirname(DEFAULT_TOOLS_DIR)) == "joha")

    def test_auto_discover_finds_search_and_webpage(self):
        count = self.registry.auto_discover()
        names = set(self.registry.get_tool_names())
        self.assertGreaterEqual(count, 2)
        self.assertIn("search", names)
        self.assertIn("webpage", names)

    def test_has_tool_and_alias(self):
        self.registry.auto_discover()
        self.assertTrue(self.registry.has_tool("search"))
        self.assertTrue(self.registry.has_tool("/search"))

    def test_dispatch_unknown_tool_returns_none(self):
        self.registry.auto_discover()
        self.assertIsNone(self.registry.dispatch("/不存在的工具", ""))

    def test_get_tool_descriptions_contains_tools(self):
        self.registry.auto_discover()
        desc = self.registry.get_tool_descriptions()
        self.assertIn("search", desc)
        self.assertIn("webpage", desc)


if __name__ == "__main__":
    unittest.main()

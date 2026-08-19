"""
ToolRegistry — 自动发现（JSON/Python）、call_tool、list_tools 测试
"""
import unittest
import os
import json

from joha.core.tool_registry import ToolRegistry, DEFAULT_TOOLS_DIR


class TestToolRegistry(unittest.TestCase):

    def setUp(self):
        self.registry = ToolRegistry()

    # ── 目录定位 ──

    def test_default_tools_dir_points_to_joha_tools(self):
        self.assertTrue(os.path.isdir(DEFAULT_TOOLS_DIR), DEFAULT_TOOLS_DIR)
        self.assertTrue(os.path.basename(DEFAULT_TOOLS_DIR) == "tools")
        self.assertTrue(os.path.basename(os.path.dirname(DEFAULT_TOOLS_DIR)) == "joha")

    # ── JSON 描述符文件 ──

    def test_json_descriptor_files_exist(self):
        """每种子目录应有 tool.json"""
        for subdir in os.listdir(DEFAULT_TOOLS_DIR):
            subpath = os.path.join(DEFAULT_TOOLS_DIR, subdir)
            if not os.path.isdir(subpath) or subdir.startswith("_"):
                continue
            json_path = os.path.join(subpath, "tool.json")
            self.assertTrue(
                os.path.isfile(json_path),
                f"缺少 tool.json: {json_path}",
            )
            # 验证是合法 JSON 且包含必要的字段
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            self.assertIn("name", data)
            self.assertIn("description", data)
            self.assertIn("arguments", data)

    def test_json_descriptor_aliases_loaded(self):
        """JSON 中的 aliases 应被正确注册"""
        self.registry.auto_discover()
        self.assertTrue(self.registry.has_tool("s"))       # search 的别名
        self.assertTrue(self.registry.has_tool("wp"))      # webpage 的别名

    # ── 自动发现 ──

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

    def test_has_tool_returns_false_for_unknown(self):
        self.registry.auto_discover()
        self.assertFalse(self.registry.has_tool("nonexistent"))

    # ── dispatch（字符串参数，传统风格）──

    def test_dispatch_unknown_tool_returns_none(self):
        self.registry.auto_discover()
        self.assertIsNone(self.registry.dispatch("/不存在的工具", ""))

    # ── call_tool（MCP 风格）──

    def test_call_tool_search_with_kwargs(self):
        self.registry.auto_discover()
        result = self.registry.call_tool("search", {"query": "Python", "num_results": 2})
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_call_tool_raises_key_error_for_unknown(self):
        self.registry.auto_discover()
        with self.assertRaises(KeyError):
            self.registry.call_tool("nonexistent", {})

    def test_call_tool_raises_type_error_for_missing_required(self):
        """webpage 要求 url 参数，不传应抛 TypeError"""
        self.registry.auto_discover()
        with self.assertRaises(TypeError):
            self.registry.call_tool("webpage", {})

    # ── list_tools（MCP 兼容输出）──

    def test_list_tools_returns_valid_mcp_schema(self):
        self.registry.auto_discover()
        tools = self.registry.list_tools()
        self.assertGreaterEqual(len(tools), 2)
        for t in tools:
            self.assertIn("name", t)
            self.assertIn("description", t)
            self.assertIn("arguments", t)
            self.assertEqual(t["arguments"]["type"], "object")
            self.assertIn("properties", t["arguments"])
            self.assertIn("required", t["arguments"])

    # ── get_tool_descriptions ──

    def test_get_tool_descriptions_contains_tools(self):
        self.registry.auto_discover()
        desc = self.registry.get_tool_descriptions()
        self.assertIn("search", desc)
        self.assertIn("webpage", desc)


if __name__ == "__main__":
    unittest.main()
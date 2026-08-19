"""
Tool Registry 中台
统一工具管理中台，实现工具的自动发现、注册和调用
参考 MCP (Model Context Protocol) 设计，支持 JSON descriptor + Python 实现分离

架构：
  - JSON 描述符文件（tool.json）定义工具的接口（name, description, arguments schema）
  - Python 实现文件（tool.py）提供 execute() 函数
  - ToolRegistry 自动发现并绑定两者
"""
import os
import json
import importlib.util
import traceback
from typing import Dict, List, Optional, Callable, Any

from joha.config.logger import tprint


# 默认工具扫描路径（工具位于 joha/tools/ 下）
DEFAULT_TOOLS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools")


def _load_json_descriptor(json_path: str) -> Optional[dict]:
    """加载 JSON 工具描述符文件"""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        tprint("warning", f"[ToolRegistry] 加载 JSON 描述符失败 {json_path}: {e}")
        return None


def _normalize_meta_from_json(json_data: dict) -> dict:
    """将 MCP 风格的 JSON 描述符转换为内部统一的 TOOL_META 格式

    JSON 输入格式（arguments 为 JSON Schema）：
      {
        "name": "search",
        "description": "...",
        "aliases": ["s"],
        "arguments": {
          "type": "object",
          "properties": {
            "query": {"type": "string", "description": "...", "default": 5},
            "num_results": {"type": "integer", "description": "..."}
          },
          "required": ["query"]
        }
      }

    内部格式（parameters 为 dict）：
      {
        "name": "search",
        "description": "...",
        "aliases": ["s"],
        "parameters": {
          "query": {"type": "str", "required": True, "description": "..."},
          "num_results": {"type": "int", "required": False, "description": "..."}
        }
      }
    """
    meta = {
        "name": json_data.get("name", ""),
        "description": json_data.get("description", ""),
        "aliases": json_data.get("aliases", []),
        "parameters": {},
    }

    arguments = json_data.get("arguments", {})
    properties = arguments.get("properties", {})
    required = set(arguments.get("required", []))

    for pname, pinfo in properties.items():
        js_type = pinfo.get("type", "string")
        # 将 JSON Schema type 映射到内部 type
        type_map = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "array": "list",
            "object": "dict",
        }
        meta["parameters"][pname] = {
            "type": type_map.get(js_type, js_type),
            "description": pinfo.get("description", ""),
            "required": pname in required,
        }
        # 携带默认值
        if "default" in pinfo:
            meta["parameters"][pname]["default"] = pinfo["default"]

    return meta


class ToolRegistry:
    """工具注册表中台
    自动发现 tools/ 目录下的工具（支持 JSON + Python 双模式），统一注册、调度和描述生成
    """

    def __init__(self, tools_dir: str = ""):
        self.tools_dir = tools_dir or DEFAULT_TOOLS_DIR
        self._tools: Dict[str, dict] = {}   # name -> {meta, execute, file}
        self._aliases: Dict[str, str] = {}  # alias -> name
        self._initialized = False

    # ----------------------------------------------------------------
    # 自动发现
    # ----------------------------------------------------------------

    def auto_discover(self) -> int:
        """自动扫描 tools/ 目录，加载符合规范的工具

        发现策略：
          1. 扫描 tools/<name>/tool.json — 加载接口描述
          2. 扫描 tools/<name>/tool.py   — 加载 execute() 实现
         两者可以独立存在，同时存在时 JSON 定义接口、Python 提供实现
        """
        if self._initialized:
            return len(self._tools)

        self._initialized = True
        tools_dir = self.tools_dir
        if not os.path.isdir(tools_dir):
            tprint("warning", f"[ToolRegistry] 工具目录不存在: {tools_dir}")
            return 0

        count = 0

        for subdir in sorted(os.listdir(tools_dir)):
            subdir_path = os.path.join(tools_dir, subdir)
            if not os.path.isdir(subdir_path) or subdir.startswith("_"):
                continue

            json_file = os.path.join(subdir_path, "tool.json")
            py_file = os.path.join(subdir_path, "tool.py")

            # 1. 加载 JSON 描述符（MCP 风格）
            meta = None
            if os.path.isfile(json_file):
                json_data = _load_json_descriptor(json_file)
                if json_data:
                    meta = _normalize_meta_from_json(json_data)
                    tprint("info", f"[ToolRegistry] 发现 JSON 描述符: {json_file}")

            # 2. 加载 Python 实现
            execute_fn = None
            py_path = None
            if os.path.isfile(py_file):
                try:
                    spec = importlib.util.spec_from_file_location(
                        f"joha.tools.{subdir}.tool", py_file
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        execute_fn = getattr(module, "execute", None)

                        # 如果没有 JSON，从 Python 的 TOOL_META 读取
                        if meta is None:
                            py_meta = getattr(module, "TOOL_META", None)
                            if py_meta:
                                meta = py_meta

                        py_path = py_file
                except Exception as e:
                    tprint("warning", f"[ToolRegistry] 加载 Python 实现失败 {py_file}: {e}")
                    traceback.print_exc()

            # 3. 注册（只要有 meta 或 execute_fn 之一即可）
            if meta and execute_fn and callable(execute_fn):
                self._register(meta, execute_fn, py_path or json_file)
                count += 1
                tprint("info", f"[ToolRegistry] ✅ 工具注册: {meta['name']}")
            elif meta and not execute_fn:
                tprint("warning", f"[ToolRegistry] ⚠️ 工具 '{meta.get('name')}' 缺少 execute() 实现")
            elif execute_fn and not meta:
                tprint("warning", f"[ToolRegistry] ⚠️ 工具 '{subdir}' 缺少接口描述 (tool.json 或 TOOL_META)")

        tprint("info", f"[ToolRegistry] 自动发现完成，共 {count} 个工具")
        return count

    def _register(self, meta: dict, execute_fn: Callable, filepath: str):
        """注册工具到内部字典"""
        name = meta.get("name", "")
        if not name:
            return

        self._tools[name] = {
            "meta": meta,
            "execute": execute_fn,
            "file": filepath,
        }

        for alias in meta.get("aliases", []):
            self._aliases[alias] = name

    def register_tool(
        self,
        name: str,
        meta: dict,
        execute_fn: Callable,
        filepath: str = "",
    ) -> None:
        """手动注册工具"""
        self._register(meta, execute_fn, filepath)

    # ----------------------------------------------------------------
    # 工具调用 - MCP 风格
    # ----------------------------------------------------------------

    def call_tool(self, name: str, arguments: dict = None) -> Any:
        """MCP 风格的工具调用

        Args:
            name: 工具名（或别名）
            arguments: 参数字典，如 {"query": "天气", "num_results": 3}

        Returns:
            工具执行结果

        Raises:
            KeyError: 工具未找到
            TypeError: 参数不匹配
            RuntimeError: 执行失败
        """
        raw = name.lstrip("/").strip().lower()
        tool_name = self._aliases.get(raw) or raw
        tool = self._tools.get(tool_name)

        if not tool:
            raise KeyError(f"工具 '{name}' 未找到")

        meta = tool["meta"]
        execute_fn = tool["execute"]
        params = meta.get("parameters", {})
        args = arguments or {}

        try:
            # 构造 kwargs：按参数名匹配
            kwargs = {}
            for pname, pinfo in params.items():
                if pname in args:
                    val = args[pname]
                    # 类型转换
                    expected_type = pinfo.get("type", "str")
                    if expected_type == "int":
                        val = int(val) if val is not None else 0
                    elif expected_type == "float":
                        val = float(val) if val is not None else 0.0
                    kwargs[pname] = val
                elif pinfo.get("required", False):
                    raise TypeError(f"缺少必需参数: {pname}")
                elif "default" in pinfo:
                    kwargs[pname] = pinfo["default"]

            result = execute_fn(**kwargs)
            return result

        except (KeyError, TypeError, RuntimeError):
            raise
        except Exception as e:
            raise RuntimeError(f"工具 '{tool_name}' 执行失败: {e}")

    # ----------------------------------------------------------------
    # 工具调用 - 传统风格（字符串参数）
    # ----------------------------------------------------------------

    def dispatch(self, cmd: str, args: str = "") -> Optional[str]:
        """传统风格的工具调度（字符串参数解析）

        Args:
            cmd: 命令名（如 'search'）或别名（如 's'）
            args: 参数字符串

        Returns:
            工具执行结果，或 None 表示未找到工具
        """
        raw_cmd = cmd.lstrip("/").strip().lower()
        tool_name = self._aliases.get(raw_cmd) or raw_cmd
        tool = self._tools.get(tool_name)

        if not tool:
            return None

        meta = tool["meta"]
        execute_fn = tool["execute"]
        params = meta.get("parameters", {})

        try:
            if not params:
                result = execute_fn()
            elif len(params) == 1:
                result = execute_fn(args.strip())
            else:
                arg_parts = args.strip().split(None, len(params) - 1)
                kwargs = {}
                for i, (pname, pinfo) in enumerate(params.items()):
                    if i < len(arg_parts):
                        val = arg_parts[i]
                        if pinfo.get("type") == "int":
                            try:
                                val = int(val)
                            except ValueError:
                                pass
                        kwargs[pname] = val
                    elif pinfo.get("required", False):
                        kwargs[pname] = ""
                    elif "default" in pinfo:
                        kwargs[pname] = pinfo["default"]
                result = execute_fn(**kwargs)

            return str(result) if result is not None else ""

        except Exception as e:
            tprint("error", f"[ToolRegistry] 工具 '{tool_name}' 执行失败: {e}")
            return f"工具执行失败: {str(e)}"

    # ----------------------------------------------------------------
    # 查询
    # ----------------------------------------------------------------

    def get_tool(self, name: str) -> Optional[dict]:
        """获取工具信息"""
        return self._tools.get(name)

    def has_tool(self, name_or_alias: str) -> bool:
        """检查工具是否存在"""
        raw = name_or_alias.lstrip("/").strip().lower()
        return raw in self._tools or raw in self._aliases

    def get_tool_names(self) -> List[str]:
        """获取所有已注册工具名"""
        return list(self._tools.keys())

    def get_tool_descriptions(self) -> str:
        """生成工具描述文本（用于注入 system prompt）"""
        if not self._tools:
            return ""

        lines = ["\n【可用工具】你可以通过以下命令调用工具："]
        for name, tool in sorted(self._tools.items()):
            meta = tool["meta"]
            desc = meta.get("description", "")
            aliases = meta.get("aliases", [])
            params = meta.get("parameters", {})
            examples = meta.get("examples", [])

            param_desc = " ".join(
                f"[{pname}]" if params[pname].get("required") else f"({pname})"
                for pname in params
            )

            alias_str = f" (别名: {'/'.join(aliases)})" if aliases else ""
            lines.append(f"  /{name} {param_desc}{alias_str}")
            lines.append(f"    用途: {desc}")

            if examples:
                ex = examples[0]
                lines.append(f"    示例: {ex}")

        lines.append("使用方式: 输入 /工具名 参数")
        return "\n".join(lines)

    def get_help_text(self) -> str:
        """生成帮助文本"""
        if not self._tools:
            return "暂无可用工具"

        lines = ["可用工具："]
        for name, tool in sorted(self._tools.items()):
            meta = tool["meta"]
            desc = meta.get("description", "")
            aliases = meta.get("aliases", [])
            params = meta.get("parameters", {})

            param_str = " ".join(
                f"<{pname}>" if params[pname].get("required") else f"[{pname}]"
                for pname in params
            )

            alias_str = f" (别名: {'/'.join(aliases)})" if aliases else ""
            lines.append(f"  /{name} {param_str}{alias_str}")
            lines.append(f"    {desc}")

        return "\n".join(lines)

    # ----------------------------------------------------------------
    # MCP 兼容：输出所有工具的 JSON Schema 列表
    # ----------------------------------------------------------------

    def list_tools(self) -> List[dict]:
        """以 MCP tools 列表格式输出所有注册的工具

        返回格式：
          [
            {
              "name": "search",
              "description": "...",
              "arguments": {
                "type": "object",
                "properties": {...},
                "required": [...]
              }
            },
            ...
          ]
        """
        tools = []
        for name, tool in sorted(self._tools.items()):
            meta = tool["meta"]
            params = meta.get("parameters", {})

            properties = {}
            required = []
            for pname, pinfo in params.items():
                # 内部 type -> JSON Schema type
                type_map = {
                    "str": "string",
                    "int": "integer",
                    "float": "number",
                    "bool": "boolean",
                    "list": "array",
                    "dict": "object",
                }
                prop = {
                    "type": type_map.get(pinfo.get("type", "str"), "string"),
                    "description": pinfo.get("description", ""),
                }
                if "default" in pinfo:
                    prop["default"] = pinfo["default"]
                properties[pname] = prop
                if pinfo.get("required", False):
                    required.append(pname)

            tools.append({
                "name": name,
                "description": meta.get("description", ""),
                "arguments": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            })

        return tools


# 全局单例
_registry_instance = None


def get_tool_registry(tools_dir: str = "") -> ToolRegistry:
    """获取 ToolRegistry 全局实例（单例）"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ToolRegistry(tools_dir)
    return _registry_instance


# 全局工具注册表中台实例
tool_registry = get_tool_registry()
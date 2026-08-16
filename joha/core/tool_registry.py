"""
Tool Registry 中台
统一工具管理中台，实现工具的自动发现、注册和调用
参考 SKILL 系统设计，支持插件化架构
"""
import os
import importlib
import inspect
import traceback
from typing import Dict, List, Optional, Callable, Any

from joha.config.logger import tprint


# 默认工具扫描路径（工具位于 joha/tools/ 下）
DEFAULT_TOOLS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools")


class ToolRegistry:
    """工具注册表中台
    自动发现 tools/ 目录下的工具，统一注册、调度和描述生成
    """

    def __init__(self, tools_dir: str = ""):
        self.tools_dir = tools_dir or DEFAULT_TOOLS_DIR
        self._tools: Dict[str, dict] = {}  # name -> {meta, execute, file}
        self._aliases: Dict[str, str] = {}  # alias -> name
        self._initialized = False

    def auto_discover(self) -> int:
        """自动扫描 tools/ 目录，加载符合规范的工具
        返回发现的工具数量
        """
        if self._initialized:
            return len(self._tools)

        self._initialized = True
        tools_dir = self.tools_dir
        if not os.path.isdir(tools_dir):
            tprint("warning", f"[ToolRegistry] 工具目录不存在: {tools_dir}")
            return 0

        count = 0
        # 1. 新格式：扫描子目录 tools/<name>/tool.py
        for subdir in sorted(os.listdir(tools_dir)):
            subdir_path = os.path.join(tools_dir, subdir)
            if not os.path.isdir(subdir_path) or subdir.startswith("_"):
                continue

            tool_file = os.path.join(subdir_path, "tool.py")
            if not os.path.isfile(tool_file):
                continue

            try:
                spec = importlib.util.spec_from_file_location(
                    f"joha.tools.{subdir}.tool", tool_file
                )
                if spec is None or spec.loader is None:
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                meta = getattr(module, "TOOL_META", None)
                execute_fn = getattr(module, "execute", None)

                if meta and execute_fn and callable(execute_fn):
                    self._register_from_meta(meta, execute_fn, tool_file)
                    count += 1
                    tprint("info", f"[ToolRegistry] 发现工具: {meta['name']} ({tool_file})")
            except Exception as e:
                tprint("warning", f"[ToolRegistry] 加载工具失败 {subdir}: {e}")
                traceback.print_exc()

        # 2. 旧格式兼容：扫描顶层 *_tool.py 或 *.py（过渡期）
        for filename in sorted(os.listdir(tools_dir)):
            if not filename.endswith(".py") or filename.startswith("_"):
                continue

            filepath = os.path.join(tools_dir, filename)
            if os.path.isdir(filepath):
                continue

            module_name = filename[:-3]
            if filename.endswith("_tool.py"):
                # 旧格式 *_tool.py 文件
                try:
                    spec = importlib.util.spec_from_file_location(
                        f"joha.tools.{module_name}", filepath
                    )
                    if spec is None or spec.loader is None:
                        continue

                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    meta = getattr(module, "TOOL_META", None)
                    execute_fn = getattr(module, "execute", None)

                    if meta and execute_fn and callable(execute_fn):
                        self._register_from_meta(meta, execute_fn, filepath)
                        count += 1
                        tprint("info", f"[ToolRegistry] 发现工具(旧格式): {meta['name']} ({filepath})")
                except Exception as e:
                    tprint("warning", f"[ToolRegistry] 加载工具失败 {filename}: {e}")
                    traceback.print_exc()

        tprint("info", f"[ToolRegistry] 自动发现完成，共 {count} 个工具")
        return count

    def _register_from_meta(self, meta: dict, execute_fn: Callable, filepath: str):
        """从 TOOL_META 注册工具"""
        name = meta.get("name", "")
        if not name:
            return

        self._tools[name] = {
            "meta": meta,
            "execute": execute_fn,
            "file": filepath,
        }

        # 注册别名
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
        self._tools[name] = {
            "meta": meta,
            "execute": execute_fn,
            "file": filepath,
        }
        for alias in meta.get("aliases", []):
            self._aliases[alias] = name

    def dispatch(self, cmd: str, args: str = "") -> Optional[str]:
        """调度工具调用

        Args:
            cmd: 命令名（如 'search'）或别名（如 's'）
            args: 参数字符串

        Returns:
            工具执行结果，或 None 表示未找到工具
        """
        # 去掉 '/' 前缀
        raw_cmd = cmd.lstrip("/").strip().lower()

        # 查找工具名
        tool_name = self._aliases.get(raw_cmd) or raw_cmd
        tool = self._tools.get(tool_name)

        if not tool:
            return None

        meta = tool["meta"]
        execute_fn = tool["execute"]
        params = meta.get("parameters", {})

        try:
            # 解析参数
            if not params:
                # 无参数工具
                result = execute_fn()
            elif len(params) == 1:
                # 单参数工具：直接传 args
                first_param_name = list(params.keys())[0]
                result = execute_fn(args.strip())
            else:
                # 多参数工具：尝试按空格分割
                arg_parts = args.strip().split(None, len(params) - 1)
                kwargs = {}
                for i, (pname, pinfo) in enumerate(params.items()):
                    if pinfo.get("required", False):
                        if i < len(arg_parts):
                            val = arg_parts[i]
                            # 类型转换
                            if pinfo.get("type") == "int":
                                try:
                                    val = int(val)
                                except ValueError:
                                    pass
                            kwargs[pname] = val
                        else:
                            kwargs[pname] = ""
                    else:
                        if i < len(arg_parts):
                            val = arg_parts[i]
                            if pinfo.get("type") == "int":
                                try:
                                    val = int(val)
                                except ValueError:
                                    pass
                            kwargs[pname] = val
                result = execute_fn(**kwargs)

            return str(result) if result is not None else ""

        except Exception as e:
            tprint("error", f"[ToolRegistry] 工具 '{tool_name}' 执行失败: {e}")
            return f"工具执行失败: {str(e)}"

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

            # 构建参数说明
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

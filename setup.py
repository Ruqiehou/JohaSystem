from __future__ import annotations

import argparse
import importlib.util
import json
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    import yaml
except ImportError:
    yaml = None


ROOT_DIR = Path(__file__).resolve().parent
REQUIREMENTS_FILE = ROOT_DIR / "requirements.txt"
ROOT_CONFIG_FILE = ROOT_DIR / "config.yaml"
CONNECTION_CONFIG_FILE = ROOT_DIR / "joha" / "adapter" / "connection.yaml"
APP_CONFIG_FILE = ROOT_DIR / "joha" / "config" / "config.json"
RUN_FILE = ROOT_DIR / "run.py"

REQUIRED_DIRS = [
    ROOT_DIR / "storage",
    ROOT_DIR / "storage" / "history",
    ROOT_DIR / "storage" / "styles",
    ROOT_DIR / "storage" / "johalog",
]

REQUIRED_IMPORTS = {
    "openai": "openai",
    "yaml": "pyyaml",
    "websockets": "websockets",
    "aiohttp": "aiohttp",
    "aiofiles": "aiofiles",
    "dotenv": "python-dotenv",
    "watchdog": "watchdog",
}

OPTIONAL_IMPORTS = {
    "playwright": "playwright（网页截图功能需要）",
}


class SetupReport:
    def __init__(self) -> None:
        self.ok: list[str] = []
        self.warn: list[str] = []
        self.err: list[str] = []

    def add_ok(self, msg: str) -> None:
        self.ok.append(msg)

    def add_warn(self, msg: str) -> None:
        self.warn.append(msg)

    def add_err(self, msg: str) -> None:
        self.err.append(msg)

    @property
    def success(self) -> bool:
        return not self.err


def mask_secret(value: object) -> str:
    text = "" if value is None else str(value)
    if not text:
        return "未配置"
    if len(text) <= 8:
        return "*" * len(text)
    return f"{text[:4]}...{text[-4:]}"


def load_yaml(path: Path, report: SetupReport) -> dict:
    if not path.exists():
        report.add_err(f"缺少 YAML 配置文件：{path.relative_to(ROOT_DIR)}")
        return {}
    if yaml is None:
        report.add_err("未安装 pyyaml，无法读取 YAML 配置")
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        report.add_err(f"YAML 配置读取失败：{path.relative_to(ROOT_DIR)}，原因：{exc}")
        return {}
    if not isinstance(data, dict):
        report.add_err(f"YAML 配置内容必须是对象：{path.relative_to(ROOT_DIR)}")
        return {}
    return data


def load_json(path: Path, report: SetupReport) -> dict:
    if not path.exists():
        report.add_err(f"缺少 JSON 配置文件：{path.relative_to(ROOT_DIR)}")
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        report.add_err(f"JSON 配置读取失败：{path.relative_to(ROOT_DIR)}，原因：{exc}")
        return {}
    if not isinstance(data, dict):
        report.add_err(f"JSON 配置内容必须是对象：{path.relative_to(ROOT_DIR)}")
        return {}
    return data


def check_python(report: SetupReport) -> None:
    version = sys.version_info
    if version >= (3, 10):
        report.add_ok(f"Python 版本：{version.major}.{version.minor}.{version.micro}")
    else:
        report.add_err(f"Python 版本过低：{version.major}.{version.minor}.{version.micro}，需要 Python 3.10+")


def check_files(report: SetupReport) -> None:
    required_files = [REQUIREMENTS_FILE, CONNECTION_CONFIG_FILE, APP_CONFIG_FILE, RUN_FILE]
    for path in required_files:
        rel = path.relative_to(ROOT_DIR)
        if path.exists():
            report.add_ok(f"文件存在：{rel}")
        else:
            report.add_err(f"文件缺失：{rel}")

    if ROOT_CONFIG_FILE.exists():
        report.add_ok("根目录 config.yaml 存在")
    else:
        report.add_warn("根目录 config.yaml 不存在；当前启动主要使用 joha/adapter/connection.yaml")


def check_dirs(report: SetupReport, fix: bool) -> None:
    for path in REQUIRED_DIRS:
        rel = path.relative_to(ROOT_DIR)
        if path.exists():
            report.add_ok(f"目录存在：{rel}")
            continue
        if fix:
            path.mkdir(parents=True, exist_ok=True)
            report.add_ok(f"已创建目录：{rel}")
        else:
            report.add_warn(f"目录不存在：{rel}，可运行 python setup.py --fix 创建")


def check_imports(report: SetupReport) -> None:
    for module, package in REQUIRED_IMPORTS.items():
        if importlib.util.find_spec(module):
            report.add_ok(f"依赖可用：{package}")
        else:
            report.add_err(f"依赖缺失：{package}，请运行 pip install -r requirements.txt")

    for module, package in OPTIONAL_IMPORTS.items():
        if importlib.util.find_spec(module):
            report.add_ok(f"可选依赖可用：{package}")
        else:
            report.add_warn(f"可选依赖缺失：{package}；需要截图功能时安装并执行 playwright install chromium")


def check_napcat_config(report: SetupReport) -> None:
    cfg = load_yaml(CONNECTION_CONFIG_FILE, report)
    if not cfg:
        return

    bot_uin = cfg.get("bt_uin") or cfg.get("bot_uin")
    napcat = cfg.get("napcat", {})
    if not isinstance(napcat, dict):
        report.add_err("napcat 配置必须是对象")
        return

    ws_url = napcat.get("ws_url")
    access_token = napcat.get("access_token")
    webui_uri = napcat.get("webui_uri")

    if bot_uin:
        report.add_ok(f"机器人 QQ：{bot_uin}")
    else:
        report.add_err("未配置 bot_uin（机器人 QQ 号）")

    if ws_url:
        parsed = urlparse(str(ws_url))
        if parsed.scheme in {"ws", "wss"} and parsed.hostname and parsed.port:
            report.add_ok(f"NapCat WebSocket：{ws_url}")
            check_ws_port(report, parsed.hostname, parsed.port)
        else:
            report.add_err("napcat.ws_url 格式不正确，示例：ws://127.0.0.1:3002")
    else:
        report.add_err("未配置 napcat.ws_url")

    if access_token:
        report.add_ok(f"NapCat WebSocket Token：{mask_secret(access_token)}")
    else:
        report.add_warn("napcat.access_token 为空；如果 NapCat 配置了 token，机器人会连接失败")

    if webui_uri:
        report.add_ok(f"NapCat WebUI：{webui_uri}")
    else:
        report.add_warn("未配置 napcat.webui_uri")

    report.add_warn("NapCat 自动拉起已移除，请先手动启动 NapCat")


def check_ws_port(report: SetupReport, host: str, port: int) -> None:
    try:
        with socket.create_connection((host, port), timeout=1.5):
            report.add_ok(f"NapCat 端口可连接：{host}:{port}")
    except OSError:
        report.add_warn(f"NapCat 端口暂不可连接：{host}:{port}；启动 NapCat 后再运行机器人")


def check_llm_config(report: SetupReport) -> None:
    cfg = load_json(APP_CONFIG_FILE, report)
    if not cfg:
        return

    chat_llm = cfg.get("chat-llm", {})
    if not isinstance(chat_llm, dict):
        report.add_err("chat-llm 配置必须是对象")
        return

    providers = chat_llm.get("providers", [])
    active_name = chat_llm.get("active_provider", "")
    if not isinstance(providers, list) or not providers:
        report.add_err("chat-llm.providers 未配置")
        return

    enabled = [p for p in providers if isinstance(p, dict) and not p.get("disabled", False)]
    if not enabled:
        report.add_err("没有可用的 LLM provider")
        return

    names = [p.get("name") for p in enabled]
    active = next((p for p in enabled if p.get("name") == active_name), None)
    if active is None:
        active = next((p for p in enabled if p.get("default")), enabled[0])
        report.add_warn(f"active_provider={active_name or '未配置'} 未命中，运行时会回退到：{active.get('name')}")
    else:
        report.add_ok(f"当前 LLM Provider：{active_name}")

    for key in ("api_key", "base_url", "model"):
        value = active.get(key)
        if value:
            shown = mask_secret(value) if key == "api_key" else value
            report.add_ok(f"LLM {key}：{shown}")
        else:
            report.add_err(f"当前 LLM provider 缺少 {key}")

    report.add_ok(f"可用 LLM Provider：{', '.join(str(name) for name in names if name)}")

    vl_llm = cfg.get("vl-llm", {})
    if isinstance(vl_llm, dict) and vl_llm.get("api_key") and vl_llm.get("base_url") and vl_llm.get("model"):
        report.add_ok(f"视觉模型：{vl_llm.get('model')}")
    else:
        report.add_warn("视觉模型 vl-llm 未完整配置；图片理解能力可能不可用")


def print_report(report: SetupReport) -> None:
    print("\n=== Joha 配置检查 ===")
    for msg in report.ok:
        print(f"[OK] {msg}")
    for msg in report.warn:
        print(f"[WARN] {msg}")
    for msg in report.err:
        print(f"[ERR] {msg}")

    print("\n=== 检查结果 ===")
    if report.success:
        print("基础配置未发现致命问题。")
    else:
        print("存在必须修复的问题，请先处理 [ERR] 项。")


def print_steps() -> None:
    print("\n=== Step by Step 操作 ===")
    steps = [
        "1. 安装 Python 3.10 或更高版本，并确认命令行可执行 python。",
        "2. 在项目根目录执行：python -m pip install -r requirements.txt",
        "3. 如需网页截图功能，执行：python -m playwright install chromium",
        "4. 编辑 joha/adapter/connection.yaml：填写 bot_uin、napcat.ws_url、napcat.access_token，并确认端口与 NapCat 一致。",
        "5. 编辑 joha/config/config.json：设置 chat-llm.active_provider，并确保对应 provider 的 api_key、base_url、model 完整。",
        "6. 启动 NapCat，并确保 WebSocket 服务已开启。",
        "7. 回到项目根目录执行：python setup.py --check，确认没有 [ERR]。",
        "8. 启动机器人：python run.py",
    ]
    for step in steps:
        print(step)


def run_check(fix: bool) -> SetupReport:
    report = SetupReport()
    check_python(report)
    check_files(report)
    check_dirs(report, fix)
    check_imports(report)
    check_napcat_config(report)
    check_llm_config(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Joha 项目配置检查与启动步骤助手")
    parser.add_argument("--check", action="store_true", help="检查当前配置")
    parser.add_argument("--steps", action="store_true", help="显示 step by step 操作步骤")
    parser.add_argument("--fix", action="store_true", help="创建缺失的基础 storage 目录")
    args = parser.parse_args()

    do_check = args.check or not args.steps
    if do_check:
        report = run_check(fix=args.fix)
        print_report(report)
    if args.steps or not args.check:
        print_steps()

    if do_check and not report.success:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Joha 二次开发指南

## 1. 开发环境搭建

### 1.1 前置要求

- Python >= 3.10
- 运行中的 NapCatQQ（WebSocket 端口开放）
- Git

### 1.2 安装步骤

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd JohaChat

# 2. 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 3. 安装依赖
pip install -r requirements.txt

# 4. 复制配置文件
cp joha/config/config.example.json joha/config/config.json

# 5. 编辑配置文件
#    joha/config/config.json      — 填入 API Key
#    joha/adapter/connection.yaml — 填入 WebSocket 地址和 QQ 号

# 6. 确保 NapCatQQ 已启动，然后运行
python run.py
```

---

## 2. 项目结构速查

```
JohaChat/
├── run.py                          # 统一启动入口
├── requirements.txt                # Python 依赖
├── CHANGELOG.md                    # 更新日志
│
├── storage/                        # 运行时数据（自动创建）
│   ├── history/                    # 聊天历史
│   ├── conversations/              # 群对话记忆
│   ├── memory/                     # 群长期记忆
│   ├── styles/                     # 风格学习
│   ├── personas/                   # 人设数据
│   └── johalog/                    # 运行日志
│
├── joha/                           # 核心代码包
│   ├── adapter/                    # NapCat 适配层（transport/protocol/core）
│   ├── core/                       # 编排入口层（扁平）
│   ├── ai/                         # AI 驱动层
│   ├── decision/                   # 决策大脑层
│   ├── managers/                   # 数据管理层
│   ├── tools/                      # 工具层
│   └── config/                     # 配置与基础设施（扁平）
│
├── tests/                          # 单元测试
├── docs/                           # 文档目录
└── README.md                       # 项目说明
```

---

## 3. 添加新命令

以添加 `/天气 <城市>` 命令为例：

编辑 `joha/core/commands.py`：

```python
async def handle_weather(cmd_args: str, event, api) -> str:
    """处理 /天气 命令"""
    city = cmd_args.strip()
    if not city:
        return "请指定城市，例如：/天气 北京"
    
    weather_info = await fetch_weather(city)
    return weather_info
```

在 `CommandHandler.handle_command()` 中注册分支：

```python
elif cmd == "/天气" and len(parts) >= 2:
    response = await handle_weather(parts[1], msg_group_id, bot_api)
```

添加自然语言别名（可选），编辑 `joha/core/commands.py` 的 `FALLBACK_COMMAND_ALIASES`：

```python
FALLBACK_COMMAND_ALIASES = {
    # ... 已有别名
    "天气": "/天气",
    "查天气": "/天气",
}
```

---

## 4. 添加新工具

工具系统支持自动发现，两种风格任选。

### 4.1 函数 + 元信息风格（推荐，供 ToolRegistry 自动发现）

创建 `joha/tools/weather/tool.py`：

```python
"""天气查询工具"""

TOOL_META = {
    "name": "weather",
    "description": "查询指定城市的天气信息",
    "parameters": {
        "city": {"type": "str", "required": True, "description": "城市名"},
    },
    "aliases": ["天气"],
}

async def execute(city: str) -> str:
    """执行天气查询"""
    return f"{city}今天晴，25°C"
```

### 4.2 类风格

创建 `joha/tools/weather/core.py`：

```python
"""天气查询工具（类风格）"""

class WeatherTool:
    def query(self, city: str) -> str:
        return f"{city}今天晴，25°C"
```

---

## 5. 配置系统

### 5.1 连接配置

`joha/adapter/connection.yaml`：

```yaml
napcat:
  ws_url: ws://127.0.0.1:3002
  access_token: ""
  bot_uin: "你的机器人QQ号"
```

可在 `run.py` 的 `RUN_CONNECT_CONFIG` 中覆盖：

```python
RUN_CONNECT_CONFIG = {
    "ws_url": "ws://127.0.0.1:3002",  # 覆盖 YAML 配置
    "access_token": "",
    "bot_uin": "1234567890",
    "debug": True,
}
```

### 5.2 机器人配置

`joha/config/config.json`：

```json
{
  "llm": {
    "active_provider": "deepseek",
    "providers": [
      {
        "name": "deepseek",
        "role": "chat",
        "api_key": "sk-xxx",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-v4-flash",
        "default": true
      }
    ]
  },
  "admin": {
    "admins": ["你的QQ号"]
  }
}
```

### 5.3 决策参数

`joha/config/reply_decision.json`：回复概率计算参数，支持热重载。

---

## 6. 日志系统

```python
from joha.config.logger import tprint, johalog_logger, ai_logger

tprint("info", "消息内容")           # 终端 + 文件
johalog_logger.info("详细日志")       # 仅文件
ai_logger.info("AI 相关日志")         # AI 专用
```

日志文件位于 `storage/johalog/`，按日期分文件。

---

## 7. 测试

### 7.1 运行测试

```bash
python -m pytest tests -q       # 全部测试
python tests/run.py             # unittest 运行器
```

### 7.2 测试 WebSocket 连接

```python
from joha.adapter import MessageClient

client = MessageClient(
    ws_url="ws://127.0.0.1:3002",
    access_token="",
)

@client.on_group_message()
async def handle(event):
    print(f"收到消息: {event.message.plain_text}")

client.start(debug=True)
```

### 7.3 测试 LLM 调用

```python
from joha.ai.generator import generator
import asyncio

async def test():
    response = await generator.chat(
        messages=[{"role": "user", "content": "你好，请介绍一下自己"}],
    )
    print(response)

asyncio.run(test())
```

---

## 8. 热重载

开发时可启用模块热重载，监控 `joha/` 目录文件变化：

```python
from joha.core.hot_reload import hot_reloader

hot_reloader.start()
# 修改 joha/ 下的 .py 文件会自动重载
hot_reloader.stop()
```

也可以在 `joha/adapter/connection.yaml` 中开启：

```yaml
settings:
  hot_reload: true
```

# Joha 核心 API 参考

## 1. MessageClient

路径: `adapter.message_client.MessageClient`

WebSocket 消息客户端入口类。

```python
from adapter import MessageClient

client = MessageClient(
    ws_url="ws://127.0.0.1:3002",
    access_token="",
)
```

### 方法

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `on_group_message()` | `func` (装饰器) | 装饰器 | 注册群消息事件处理函数 |
| `start()` | `debug=True` | None | 启动连接循环 |
| `stop()` | — | None | 停止连接 |

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `api` | `BotAPI` | 消息发送 API 实例 |

---

## 2. BotAPI

路径: `adapter.kernel.api.BotAPI`

OneBot 协议 API 封装。

```python
api = bot.api
```

### 方法

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `send_group_message()` | `group_id`, `message`, `auto_escape=False` | dict | 发送群消息 |
| `send_private_message()` | `user_id`, `message` | dict | 发送私聊消息 |
| `get_group_info()` | `group_id` | dict | 获取群信息 |
| `get_group_member_info()` | `group_id`, `user_id` | dict | 获取群成员信息 |

---

## 3. GroupMessageEvent

路径: `adapter.protocol.events.GroupMessageEvent`

群消息事件模型。

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `group_id` | int | 群号 |
| `user_id` | int | 发送者 QQ 号 |
| `message` | str | 消息纯文本内容 |
| `raw_message` | str | 原始消息内容 |
| `message_id` | int | 消息 ID |
| `sender` | dict | 发送者信息（昵称、角色等） |

### 方法

| 方法 | 返回 | 说明 |
|------|------|------|
| `is_at(bot_uin)` | bool | 消息是否@了指定机器人 |
| `get_images()` | list | 获取消息中的图片 URL 列表 |

---

## 4. MessageHandler

路径: `joha.core.message_handler`

消息处理入口。

```python
from joha.core import message_handler

await message_handler.process_group_message(event, api)
```

### 主要函数

| 函数 | 参数 | 说明 |
|------|------|------|
| `process_group_message(event, api)` | `GroupMessageEvent`, `BotAPI` | 处理群消息的完整流程 |

---

## 5. MessageService

路径: `joha.core.service`

核心业务编排。

```python
from joha.core import MessageService

service = MessageService()
await service.process_message(event, api, context)
```

### 方法

| 方法 | 说明 |
|------|------|
| `process_message(event, api, context)` | 完整的学习→决策→生成流水线 |
| `learn_from_message(event)` | 仅执行学习阶段 |
| `should_reply(context)` | 仅执行决策阶段 |
| `generate_reply(context)` | 仅执行生成阶段 |

---

## 6. DecisionEngine

路径: `joha.decision.decision_engine.DecisionEngine`

回复决策总控。

```python
from joha.decision.decision_engine import DecisionEngine

engine = DecisionEngine()
should_reply = await engine.should_reply(context)
prob = engine.compute_reply_prob(context)
```

### 方法

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `should_reply(context)` | dict | bool | 综合判断是否回复 |
| `compute_reply_prob(context)` | dict | float | 计算回复概率 [0, 1] |
| `build_context(event)` | `GroupMessageEvent` | dict | 构建决策上下文 |

---

## 7. ReplyConfig

路径: `joha.decision.reply_config.reply_cfg`

决策配置单例。

```python
from joha.decision.reply_config import reply_cfg

# 访问配置项
threshold = reply_cfg.thresholds.group
weights = reply_cfg.feedback_weights

# 热重载
reply_cfg.reload()
```

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `thresholds` | dict | 阈值配置 |
| `feedback_weights` | dict | 反馈权重 |
| `group_dynamic` | dict | 群动态调节参数 |
| `content_quality` | dict | 内容质量参数 |
| `cooldown` | dict | 冷却参数 |

---

## 8. ChatEngine

路径: `joha.ai.bot.ChatEngine`

通用 AI 聊天引擎。

```python
from joha.ai.bot import ChatEngine

engine = ChatEngine()
response = engine.chat("你好")
```

### 方法

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `chat(message, context=None)` | str, dict | str | 发送单条消息并获取回复 |
| `chat_with_history(messages)` | list | str | 发送多轮对话并获取回复 |
| `switch_provider(name)` | str | bool | 切换到指定 Provider |
| `get_current_provider()` | — | dict | 获取当前 Provider 信息 |

---

## 9. ProviderManager

路径: `joha.ai.providers.ProviderManager`

多 Provider 管理。

```python
from joha.ai.providers import ProviderManager

pm = ProviderManager()
client = pm.get_client("deepseek")
pm.switch("alibaba")
```

### 方法

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `get_client(name)` | str | `AIClient` | 获取指定 Provider 的客户端 |
| `switch(name)` | str | bool | 切换当前激活的 Provider |
| `list_providers()` | — | list | 列出所有可用 Provider |
| `get_active()` | — | dict | 获取当前激活的 Provider 配置 |

---

## 10. AdminManager

路径: `joha.managers.admin.AdminManager`

管理员权限管理。

```python
from joha.managers.admin import AdminManager

admin_mgr = AdminManager()
is_admin = admin_mgr.is_admin(user_id)
```

### 方法

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `is_admin(user_id)` | int | bool | 检查用户是否为管理员 |
| `add_admin(user_id)` | int | bool | 添加管理员 |
| `remove_admin(user_id)` | int | bool | 移除管理员 |
| `list_admins()` | — | list[int] | 列出所有管理员 |

---

## 11. ConfigManager

路径: `joha.config.config_manager.ConfigManager`

配置管理器单例。

```python
from joha.config.config_manager import config_manager

# 获取配置项
debug = config_manager.get("settings.debug", False)
providers = config_manager.get("llm.providers", [])

# 获取嵌套配置
napcat = config_manager.get("napcat", {})
```

### 方法

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `get(key, default=None)` | str, any | any | 获取配置项，支持点号路径 |
| `reload()` | — | None | 重新加载配置文件 |

---

## 12. Logger

路径: `joha.config.logger`

日志工具。

```python
from joha.config.logger import tprint

tprint("info", "这是一条信息日志")
tprint("error", "这是一条错误日志")
tprint("debug", "调试信息: %s", some_value)
```

### 函数

| 函数 | 参数 | 说明 |
|------|------|------|
| `tprint(level, message, *args)` | str, str, ... | 打印日志，`level` 可选: debug/info/warning/error |

---

## 13. CooldownManager

路径: `joha.decision.cooldown.CooldownManager`

冷却管理。

```python
from joha.decision.cooldown import CooldownManager

cd = CooldownManager()
can_reply = cd.check(group_id)
cd.record(group_id)
```

### 方法

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `check(group_id)` | int | bool | 检查该群是否可以回复 |
| `record(group_id)` | int | None | 记录一次回复时间 |
| `get_remaining(group_id)` | int | float | 获取该群剩余冷却时间（秒） |

---

## 14. GroupModeConfig

路径: `joha.config.group_mode_config.GroupModeConfig`

群组模式配置。

```python
from joha.config.group_mode_config import GroupModeConfig

mode_cfg = GroupModeConfig()
mode = mode_cfg.get_mode(group_id)  # "active" 或 "passive"
mode_cfg.set_mode(group_id, "passive")
```

### 方法

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `get_mode(group_id)` | int | str | 获取指定群的模式 |
| `set_mode(group_id, mode)` | int, str | None | 设置群模式 |
| `get_global_mode()` | — | str | 获取全局模式 |
| `set_global_mode(mode)` | str | None | 设置全局模式 |

---

## 15. RuntimeContext

路径: `joha.core.runtime_context`

运行时全局上下文。

```python
from joha.core import runtime_context

# 设置机器人 QQ 号
runtime_context.bot_uin = 123456789

# 访问
print(runtime_context.bot_uin)
```

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `bot_uin` | int | 机器人 QQ 号 |

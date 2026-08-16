# Joha 核心 API 参考

## 1. MessageClient

路径: `joha.adapter.message_client.MessageClient`（也通过 `joha.adapter.MessageClient` 导出）

WebSocket 消息客户端入口类（封装层），负责事件注册与路由。

```python
from joha.adapter import MessageClient

client = MessageClient(
    ws_url="ws://127.0.0.1:3002",
    access_token="",
)
```

### 装饰器（事件注册）

| 方法 | 参数 | 说明 |
|------|------|------|
| `on_group_message()` | func (装饰器) | 注册群消息事件处理函数 |
| `on_private_message()` | func (装饰器) | 注册私聊消息事件处理函数 |
| `on_notice()` | func (装饰器) | 注册通知事件处理函数 |
| `on_request()` | func (装饰器) | 注册请求事件处理函数 |

### 生命周期

| 方法 | 参数 | 说明 |
|------|------|------|
| `start(debug=False)` | bool | 启动消息客户端（便捷方法，兼容已有事件循环） |
| `run_frontend(debug=False)` | bool | 运行事件循环入口（async） |
| `run()` | — | 一键启动：从 connection.yaml 读取配置并运行（classmethod） |
| `set_tick_handler(handler)` | async 无参回调 | 设置主循环 tick 回调（后台周期任务，如清理过期队列） |

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `api` | `BotAPI` | 消息发送 API 实例 |

---

## 2. BotAPI

路径: `joha.adapter.protocol.api.BotAPI`

OneBot 协议 API 封装（协议层），对 `NapCatClient.call_api()` 做语义化封装。

```python
api = bot.api
# 或
from joha.adapter.protocol import BotAPI
```

### 消息发送

| 方法 | 说明 |
|------|------|
| `call(action, params=None)` | 调用任意 OneBot API |
| `send_group_message(group_id, message="", image_path=None, at_user_id=None, reply_message_id=None)` | 发送群消息 |
| `send_private_message(user_id, message="", image_path=None, reply_message_id=None)` | 发送私聊消息 |
| `send_group_message_segments(group_id, segments, reply_message_id=None)` | 发送图文混排群消息（消息段数组） |
| `send_private_message_segments(user_id, segments, reply_message_id=None)` | 发送图文混排私聊消息 |

### 消息管理

| 方法 | 说明 |
|------|------|
| `delete_message(message_id)` | 撤回 / 删除消息 |
| `get_message(message_id)` | 获取指定消息 |

### 互动娱乐

| 方法 | 说明 |
|------|------|
| `group_poke(group_id, user_id)` / `friend_poke(user_id)` | 戳一戳 |
| `send_group_dice(group_id)` / `send_private_dice(user_id)` | 发送骰子 |
| `send_group_rps(group_id)` / `send_private_rps(user_id)` | 发送猜拳 |

### 历史记录

| 方法 | 说明 |
|------|------|
| `get_group_message_history(group_id, message_seq=None, count=20, reverse_order=False)` | 获取群消息历史 |
| `get_private_message_history(user_id, message_seq, count=20, reverse_order=False)` | 获取私聊消息历史 |

### 群组 / 好友管理

| 方法 | 说明 |
|------|------|
| `get_group_list()` / `get_group_member_list(group_id)` / `get_group_member_info(group_id, user_id)` | 群信息 |
| `set_group_ban(group_id, user_id, duration=1800)` | 禁言 |
| `set_group_kick(group_id, user_id, reject_add_request=False)` | 踢出 |
| `set_group_card(group_id, user_id, card="")` | 设置群名片 |
| `get_friend_list()` / `get_login_info()` / `get_stranger_info(user_id)` | 好友信息 |
| `set_friend_add_request(flag, approve=True, remark="")` | 处理好友请求 |
| `set_group_add_request(flag, sub_type, approve=True, reason="")` | 处理群请求 |
| `send_like(user_id, times=1)` | 发送赞 |
| `get_version_info()` | 获取版本信息 |

---

## 3. GroupMessageEvent

路径: `joha.adapter.protocol.events.GroupMessageEvent`

群消息事件模型。

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `group_id` | int | 群号 |
| `user_id` | int | 发送者 QQ 号 |
| `user_name` | str | 发送者昵称 |
| `message` | `Message` | 消息对象（`message.plain_text` 获取纯文本） |
| `raw_message` | str | 原始消息内容 |
| `message_id` | int | 消息 ID |
| `sender` | dict | 发送者信息（昵称、角色等） |
| `at_user_ids` | list[int] | 消息中 @ 的用户 ID 列表 |
| `reply_message_id` | int/None | 回复的消息 ID（无则 None） |

### 相关类

| 类 | 说明 |
|------|------|
| `Message` | 消息内容模型，属性：`plain_text`、`raw_message`、`has_dice`、`has_rps`、`has_poke`；方法：`get_plain_text()` |
| `PrivateMessageEvent` | 私聊消息事件 |
| `NoticeEvent` | 通知事件（群成员增减、禁言、撤回、戳一戳等子类） |
| `RequestEvent` | 请求事件（好友/群请求） |

---

## 4. MessageHandler

路径: `joha.core.message_handler`

消息处理入口。

```python
from joha.core.message_handler import message_handler, process_merged_message

await message_handler.process_group_message(event, api)
```

### 主要函数

| 函数 | 参数 | 说明 |
|------|------|------|
| `MessageHandler.process_group_message(event, api)` | `GroupMessageEvent`, `BotAPI` | 处理群消息的完整流程（提取 → 命令 → 队列合并） |
| `process_merged_message(merged_msg, api)` | `MergedMessage`, `BotAPI` | 处理合并后的消息（生成回复 + 发送） |

---

## 5. MessageService

路径: `joha.core.service.MessageService`

核心业务编排（学习 → 决策 → 生成）。

```python
from joha.core.service import message_service

response = await message_service.process_message(
    userid="123456",
    message="你好",
    group_id="7890",
    is_at_bot=False,
)
```

### 方法

| 方法 | 说明 |
|------|------|
| `process_message(userid, message, group_id=None, force_reply=False, is_at_bot=False, reply_to_bot=False, is_pure_sticker_or_image=False, images=None, merged_text="", merged_messages=None, is_merged=False)` | 完整流水线，返回回复文本或 None |
| `get_global_mode()` / `set_global_mode(mode)` | 全局 active/passive 模式 |
| `get_group_mode(group_id)` / `set_group_mode(group_id, mode)` | 逐群模式 |
| `get_stats()` | 运行统计（dict） |
| `get_stats_str()` | 统计文本 |

### 数据类

| 数据类 | 说明 |
|------|------|
| `MessageContext` | 消息处理上下文（user_id、group_id、message、images、决策结果等） |

---

## 6. DecisionEngine

路径: `joha.decision.decision_engine.DecisionEngine`

回复决策总控（总分架构的"总"）。

```python
from joha.decision import get_decision_engine

engine = get_decision_engine()
result = engine.process(
    text="你好",
    user_id="123456",
    group_id="7890",
    is_at_bot=False,
    group_mode="active",
)
```

### 方法

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `process(text, user_id, group_id="", is_at_bot=False, reply_to_bot=False, is_pure_media=False, is_private=False, group_mode="passive", force_reply=False, **kwargs)` | 消息与上下文 | `EngineResult` | 完整决策流水线 |
| `get_stats()` | — | dict | 引擎统计（调用/回复/跳过次数） |
| `refresh()` | — | None | 刷新子模块状态 |

### EngineResult 主要字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `should_reply` | bool | 是否回复 |
| `probability` | float | 回复概率 [0, 1] |
| `threshold` | float | 使用的阈值 |
| `intent` | str | 识别到的意图 |
| `intent_confidence` | float | 意图置信度 |
| `action_level` | str | 动作分级 |
| `reply_text` | str | 直接回复文本（如有） |
| `tool_action` | dict/None | 工具调用动作 |
| `tool_response` | str/None | 工具调用结果 |

---

## 7. ReplyConfig

路径: `joha.decision.reply_decision.reply_cfg`

决策配置单例（内联在 `reply_decision.py`，懒加载自 `joha/config/reply_decision.json`）。

```python
from joha.decision.reply_decision import reply_cfg

# 访问配置项
threshold = reply_cfg.thresholds["group"]
weights = reply_cfg.feedback_weights

# 热重载
reply_cfg.reload()
```

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `bot_nicknames` | set | 机器人昵称集合 |
| `thresholds` | dict | 阈值配置 |
| `feedback_weights` | dict | 反馈权重 |
| `group_dynamic` | dict | 群动态调节参数 |
| `length_bonuses` | dict | 内容长度奖励/惩罚 |
| `spam_detection` | dict | 垃圾信息检测参数 |
| `intent_feedback_mapping` | dict | 意图→反馈权重映射 |
| `threshold_adjustments` | dict | 阈值动态调整参数 |

### 核心函数

| 函数 | 说明 |
|------|------|
| `compute_reply_prob(ctx, cooldown=None)` | 计算回复概率（Logit + Sigmoid） |
| `should_reply(ctx, cooldown=None)` | 概率 ≥ 阈值判断是否回复 |
| `build_context(text, user_id, group_id="", ...)` | 构建决策上下文（含群组状态注入） |
| `apply_feedback(intent, positive, magnitude=0.1)` | 应用好评/差评反馈 |

---

## 8. ChatEngine

路径: `joha.ai.bot.ChatEngine`

通用 AI 聊天引擎（支持工具调用 search_web / fetch_webpage）。

```python
from joha.ai.bot import ChatEngine

engine = ChatEngine()
response = engine.chat("你好")
```

### 方法

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `chat(user_input, stream=False, temperature=0.7)` | str, bool, float | str | 发送消息并获取回复（失败自动切换其他 Provider 重试） |
| `set_system_prompt(prompt)` | str | None | 设置系统提示词 |
| `clear_history()` | — | None | 清除对话历史（保留系统提示词） |

### 获取实例

| 函数 | 说明 |
|------|------|
| `get_chat_engine()` | 获取全局聊天引擎实例（延迟初始化） |

---

## 9. ProviderManager

路径: `joha.ai.providers.ProviderManager`（单例 `provider_manager`）

多 Provider 管理（按 role 区分 chat / classifier / tool_calling）。

```python
from joha.ai.providers import provider_manager

provider = provider_manager.get("deepseek")
default = provider_manager.get_default("chat")
```

### 方法

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `get(name)` | str | `Provider`/None | 按名称获取 Provider |
| `get_default(role)` | str | `Provider`/None | 获取指定 role 的默认 Provider |
| `list_by_role(role)` | str | list | 列出指定 role 的所有 Provider |
| `list_all()` | — | list | 列出所有 Provider |
| `reload()` | — | None | 从 config.json 重新加载 |
| `add_or_update(name, role, api_key, base_url, model, default=False)` | ... | None | 添加/更新 Provider 并持久化 |
| `remove(name)` | str | None | 移除 Provider 并持久化 |

### 数据类

| 数据类 | 字段 | 说明 |
|------|------|------|
| `Provider` | name, role, api_key, base_url, model | 单个 Provider |

---

## 10. AdminManager

路径: `joha.managers.admin.AdminManager`（单例 `admin_manager`）

管理员权限管理。

```python
from joha.managers.admin import admin_manager

is_admin = admin_manager.is_admin(user_id)
```

### 方法

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `is_admin(user_id)` | int | bool | 检查用户是否为管理员 |
| `get_admins()` | — | list[str] | 获取所有管理员 |
| `add_admin(user_id)` | int | bool | 添加管理员 |
| `remove_admin(user_id)` | int | bool | 移除管理员（target_users 不可删除） |
| `get_admin_count()` | — | int | 管理员数量 |
| `is_target_user(user_id)` | int | bool | 是否为不可删除的目标用户 |

---

## 11. ConfigManager

路径: `joha.config.config_manager.ConfigManager`（全局实例 `config`）

主配置管理器（JSON 配置，LLM Provider / admin 等）。

```python
from joha.config.config_manager import config

# 获取配置项
debug = config.get("settings.debug", False)
providers = config.get("llm.providers", [])
admins = config.admins
```

### 方法

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `get(key, default=None)` | str, any | any | 获取配置项，支持点号路径 |
| `set(key, value)` | str, any | None | 设置配置项 |
| `save()` | — | None | 保存到 config.json |
| `load()` | — | None | 重新加载配置 |
| `switch_provider(name)` | str | bool | 切换当前激活 Provider |
| `get_llm_providers()` | — | list | 获取所有 Provider 配置 |
| `get_active_provider()` | — | dict/None | 获取当前激活 Provider |
| `get_active_provider_name()` | — | str | 当前激活 Provider 名称 |

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `llm_api_key` | str | 当前激活 Provider 的 API Key |
| `llm_base_url` | str | 当前激活 Provider 的 Base URL |
| `llm_model` | str | 当前激活 Provider 的模型名 |
| `admins` | list | 管理员列表 |

---

## 12. Logger

路径: `joha.config.logger`

日志工具。

```python
from joha.config.logger import tprint, johalog_logger, ai_logger

tprint("info", "这是一条信息日志")
tprint("error", "这是一条错误日志")
johalog_logger.info("详细日志")       # 仅写入文件
ai_logger.info("AI 相关日志")         # AI 专用日志
```

### 函数

| 函数 | 参数 | 说明 |
|------|------|------|
| `tprint(level, message, *args)` | str, str, ... | 打印日志，`level` 可选: debug/info/warning/error |

---

## 13. CooldownManager

路径: `joha.decision.cooldown.CooldownManager`（单例 `cooldown_manager`）

冷却管理（JSON 持久化，群级 + 用户级）。

```python
from joha.decision.cooldown import cooldown_manager

penalty = cooldown_manager.get_cooldown_penalty(group_id, user_id)
cooldown_manager.record_reply(group_id, user_id)
```

### 方法

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `get_cooldown_penalty(group_id, user_id="")` | str, str | float | 计算冷却惩罚分（负值抑制回复） |
| `record_reply(group_id, user_id="")` | str, str | None | 记录一次回复时间 |
| `can_reply(group_id, user_id="", min_interval=2.0)` | str, str, float | bool | 是否可回复 |
| `get_group_stats(group_id)` | str | dict | 群冷却统计（距上次回复秒数等） |

---

## 14. GroupModeConfig

路径: `joha.config.group_mode_config.GroupModeConfig`（单例 `group_mode_config`）

群组模式配置（JSON 持久化）。

```python
from joha.config.group_mode_config import group_mode_config

mode = group_mode_config.get_mode(group_id)  # "active" 或 "passive"
group_mode_config.set_mode(group_id, "passive")
```

### 方法

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `get_mode(group_id, default="passive")` | str, str | str | 获取指定群的模式 |
| `set_mode(group_id, mode)` | str, str | None | 设置群模式（立即保存） |
| `remove_mode(group_id)` | str | bool | 删除群模式设置 |
| `has_mode(group_id)` | str | bool | 是否存在群模式设置 |
| `get_all_modes()` | — | dict | 获取全部群模式 |
| `clear_all()` | — | None | 清空所有群模式 |

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

---

## 16. 其他常用模块

| 模块 | 路径 | 说明 |
|------|------|------|
| MessageQueueManager | `joha.core.message_queue` | 消息队列合并（`message_queue_manager`） |
| MessageBuilder | `joha.core.message_builder` | LLM 上下文组装（`message_builder`） |
| HistoryManager | `joha.managers.history_manager` | 聊天历史管理（`history_manager`） |
| StyleLearner | `joha.managers.style_learner` | 风格学习（`style_learner`） |
| GroupConversation | `joha.managers.group_conversation` | 群对话记忆（`group_conversation`） |
| GroupMemory | `joha.managers.group_memory` | 群长期记忆（`group_memory_manager`） |
| GroupState | `joha.decision.group_state` | 群组状态追踪（`group_state_manager`） |
| ToolRegistry | `joha.core.tool_registry` | 工具注册表（`tool_registry` / `get_tool_registry()`） |
| SearchTool / WebpageTool | `joha.tools` | 搜索与网页抓取工具 |

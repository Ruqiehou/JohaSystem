# Joha 模块说明文档

## 目录

- [adapter 适配层](#adapter-适配层)
- [core 编排层](#core-编排层)
- [ai AI驱动层](#ai-ai驱动层)
- [decision 决策层](#decision-决策层)
- [managers 管理层](#managers-管理层)
- [tools 工具层](#tools-工具层)
- [config 基础设施](#config-基础设施)

---

## adapter 适配层

路径: `joha/adapter/`

负责与 NapCatQQ 消息平台对接，提供 WebSocket 连接和事件抽象。分为传输层（transport）、协议层（protocol）和兼容导出层（core）三层。

### message_client.py
- **类**: `MessageClient`
- **职责**: 封装层，专注于事件路由和装饰器注册
- **关键方法**:
  - `on_group_message()`: 装饰器，注册群消息事件回调
  - `on_private_message()`: 装饰器，注册私聊消息事件回调
  - `on_notice()`: 装饰器，注册通知事件回调
  - `on_request()`: 装饰器，注册请求事件回调
  - `set_tick_handler()`: 设置主循环 tick 回调（后台周期任务）
  - `start()`: 启动连接循环
  - `api`: 属性，暴露消息发送 API

### transport/ 传输层

| 文件 | 类/函数 | 职责 |
|------|---------|------|
| `client.py` | `NapCatClient` | 连接层：WebSocket 连接管理、消息收发、通用 `call_api()` |
| `interfaces.py` | `IClient` 等 | 传输层接口定义 |

### protocol/ 协议层

| 文件 | 类/函数 | 职责 |
|------|---------|------|
| `api.py` | `BotAPI` | OneBot 协议 API 封装（发送消息等） |
| `events.py` | `GroupMessageEvent` 等 | 事件数据模型 |
| `event_bus.py` | `EventBus` | 内部事件总线 |
| `event_dispatcher.py` | `EventDispatcher` | 事件分发器 |
| `emoji_map.py` | — | QQ 表情 ID 与文字映射 |
| `message_segment.py` | `MessageSegment` | 消息段构建器 |
| `interfaces.py` | 接口定义 | 抽象接口 |

### core/ 兼容导出层

| 文件 | 职责 |
|------|------|
| `__init__.py` | 统一 re-export transport + protocol 的所有公开类 |
| `client.py` | client 兼容重导出 |
| `events.py` | events 兼容重导出 |
| `interfaces.py` | interfaces 兼容重导出 |

### config.py
- **职责**: 连接配置读取（YAML）、.env 加载、日志系统初始化
- **关键类**: `ConfigManager`（YAML 配置）、`Config`（环境变量配置）
- **函数**: `setup_logging()`、`get_logger()`

### connection.yaml
- **职责**: NapCat 连接配置（WebSocket 地址、QQ 号等）

---

## core 编排层

路径: `joha/core/`

扁平结构，负责消息流入后的完整处理流水线。

### message_handler.py
- **类**: `MessageHandler`
- **职责**: 
  - 接收原始群消息事件
  - 提取文本、图片、@信息等
  - 检测斜杠命令并直通返回
  - 检测@/回复关系
  - 将消息送入队列合并系统
- **函数**: `process_merged_message()` 处理合并后的消息（生成回复 + 发送）

### commands.py
- **类**: `CommandHandler`
- **职责**: 所有斜杠命令的解析与路由
- **支持命令**:
  - 全员: `/好评`, `/差评`, `/群状态`
  - 管理员: `/帮助`, `/全局启动`, `/全局关闭`, `/本群启动`, `/本群关闭`, `/模式`, `/管理员列表`, `/添加管理员`, `/删除管理员`, `/模型`, `/当前模型`, `/模型状态`, `/切换模型`, `/风格`, `/清除风格`, `/统计`, `/人设列表`, `/人设信息`, `/切换人设`, `/绑定人设`, `/创建人设`, `/删除人设`, `/人设`
- **别名**: `FALLBACK_COMMAND_ALIASES` + `normalize_fallback_command()` 支持自然语言触发

### service.py
- **类**: `MessageService`
- **职责**: 核心业务编排
  - 判断群组模式（active/passive）
  - 调用学习模块记录历史、学习风格
  - 调用决策引擎判断是否回复
  - 调用生成器构建回复
- **数据类**: `MessageContext`

### message_builder.py
- **职责**: 为 LLM 构建完整的对话上下文
  - 组装系统提示词（含人设）
  - 注入群长期记忆 / 群对话记忆 / 用户历史
  - 注入工具描述

### message_queue.py
- **类**: `MessageQueueManager`
- **职责**: 
  - 维护各群的消息队列
  - 在 `merge_window` 时间内合并多条消息
  - 队列满或超时时触发批量处理
  - 过期消息定期清理

### 其他模块

| 文件 | 职责 |
|------|------|
| `runtime_context.py` | 运行时全局上下文（bot_uin 等） |
| `persona_monitor.py` | 人设参数监控与稳定性报告 |
| `tool_registry.py` | 工具自动发现与注册 |
| `response_postprocessor.py` | 回复后处理（过滤、格式化） |
| `image_utils.py` | 图片格式转换与处理 |
| `clean_history.py` | 历史记录清洗与压缩 |
| `hot_reload.py` | 开发时模块热重载 |

---

## ai AI驱动层

路径: `joha/ai/`

负责 LLM 调用，封装多 Provider 差异。

### clients.py
- **类**: `BaseAIClient`, `OpenAICompatibleClient`, `SimpleClassifierClient`
- **函数**: `create_client_from_provider()`
- **职责**: OpenAI 协议兼容的底层 API 调用

### providers.py
- **类**: `ProviderManager`（单例）、`Provider`
- **职责**: 管理多个 LLM Provider（按 role 区分），运行时切换
- **方法**: `get()`, `get_default(role)`, `list_by_role()`, `list_all()`, `reload()`, `add_or_update()`, `remove()`

### bot.py
- **类**: `ChatEngine`
- **职责**: 通用 AI 聊天引擎，支持工具调用（search_web / fetch_webpage）和 Provider 自动切换
- **方法**: `chat()`, `set_system_prompt()`, `clear_history()`

### generator.py
- **类**: `Generator`
- **职责**: 基于 MessageBuilder 构建的上下文，调用 LLM 生成回复
- **方法**: `chat()`（异步）、`chat_sync()`（同步）、`switch_provider()`

### classifier.py
- **类**: `QuestionClassifier`
- **职责**: 文本分类任务（意图识别等）

---

## decision 决策层

路径: `joha/decision/`

Joha 的核心大脑，决定是否回复消息。

### decision_engine.py
- **类**: `DecisionEngine`
- **职责**: 总分架构的"总控"，按顺序调用各子模块
- **入口**: `process()`，返回 `EngineResult`
- **子模块**: `CommandAnalyzer`（自然语言命令分析，AI 驱动）

### reply_decision.py
- **职责**: 核心概率计算（Logit 累加 + Sigmoid 归一化）+ 配置懒加载与热重载
- **函数**: `compute_reply_prob()`, `should_reply()`, `build_context()`, `apply_feedback()`
- **数据类**: `MessageContext`, `ReplyConfig`（单例 `reply_cfg`）

### intent_classifier.py
- **职责**: 纯规则意图识别

### group_state.py
- **职责**: 群活跃度追踪、消息频率统计、认可率
- **持久化**: `johadata/group_states.json`

### cooldown.py
- **类**: `CooldownManager`
- **职责**: 防刷屏，限制短时间连续回复（群级 + 用户级）
- **持久化**: `johadata/cooldown.json`

---

## managers 管理层

路径: `joha/managers/`

### personas.py
- **职责**: 多维度人设参数管理、多人设增删改查、群绑定
- **存储**: `johadata/personas/`

### style_learner.py
- **职责**: 自动学习群成员说话风格
- **存储**: `johadata/styles/`

### history_manager.py
- **职责**: 聊天记录的增删查（只存用户消息，不含回复）
- **存储**: `johadata/history/`

### group_conversation.py
- **职责**: 群对话记忆（短时上下文，按群分文件）
- **存储**: `johadata/conversations/group_{group_id}.json`

### group_memory.py
- **职责**: 群长期记忆（跨会话总结）
- **存储**: `johadata/memory/group_{group_id}.json`

### user_profile.py
- **职责**: 用户画像持久化
- **存储**: `johadata/user_profiles.json`

### admin.py
- **类**: `AdminManager`（单例）
- **职责**: 管理员列表维护、权限检查
- **存储**: `joha/config/config.json` 的 `admin.admins` 段

---

## tools 工具层

路径: `joha/tools/`

每个工具独立目录，采用 **MCP 风格 JSON 描述符 + Python 实现** 分离架构：

```
joha/tools/<tool_name>/
├── tool.json    ← MCP 风格接口描述（name, description, arguments JSON Schema）
├── tool.py      ← execute() 函数 + TOOL_META（向后兼容）
└── core.py      ← 核心实现逻辑
```

| 组件 | 路径 | 职责 |
|------|------|------|
| `ToolRegistry` | `joha.core.tool_registry` | 中台：自动发现、注册、call_tool/list_tools/dispatch |
| `tool.json` | `joha/tools/<name>/tool.json` | MCP 风格 JSON 描述符（参数校验用） |
| `tool.py` | `joha/tools/<name>/tool.py` | `execute()` 函数，被 ToolRegistry 调度 |
| `core.py` | `joha/tools/<name>/core.py` | 真实实现（搜索、抓取等） |

### 工具调度流程

```
用户发 /search Python
  → commands.py 识别 /search
  → tool_registry.call_tool("search", {"query": "Python"})
  → 加载 joha/tools/search/tool.json 校验参数
  → 调用 search/tool.py 的 execute(query="Python")
  → search/core.py 的 SearchTool.do_search()
  → 返回结果文本
```

### search/
- **tool.json**: 参数 query (str, required), num_results (int, default=5)
- **exec**: `SearchTool.do_search()` — DuckDuckGo / Google / Bing + AI 总结
- **命令**: `/search <query>`, `/s <query>`, `/web_search <query>`

### webpage/
- **tool.json**: 参数 url (str, required)
- **exec**: `WebpageTool.fetch()` — URL 验证 + 内容提取
- **命令**: `/webpage <url>`, `/wp <url>`, `/fetch <url>`

---

## config 基础设施

路径: `joha/config/`

扁平结构，所有模块直接在 `config/` 下。

### config_manager.py
- **类**: `ConfigManager`
- **职责**: JSON 配置文件读取（LLM Provider、admin 等）
- **全局实例**: `config`

### group_mode_config.py
- **类**: `GroupModeConfig`
- **职责**: 逐群的 active/passive 模式管理
- **持久化**: `johadata/group_modes.json`

### logger.py
- **职责**: 多级别日志、文件轮转、预定义记录器
- **导出**: `tprint`, `johalog_logger`, `ai_logger`

### cache.py
- **类**: `LRUCache`
- **职责**: LRU 缓存、TTL 过期、函数结果缓存装饰器

### paths.py
- **职责**: 存储路径集中定义（`STORAGE_ROOT`、`HISTORY_DIR` 等）
- **运行时**: 自动创建 `johadata/` 及其子目录（路径集中定义于 `joha.config.paths.STORAGE_ROOT`）

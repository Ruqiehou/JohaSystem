# 更新日志

所有重要版本变更记录。

## v3.7.0 (2026-08-16)

### 结构修正（以代码为准）

- **adapter 迁回 `joha/` 下**: `adapter/` 由项目根目录迁回 `joha/adapter/`（传输层 transport / 协议层 protocol / 兼容导出层 core 的三层结构不变），所有导入路径统一为 `from joha.adapter import ...`
- **连接配置**: `connection.yaml` 路径为 `joha/adapter/connection.yaml`
- **新增测试**: 完整单元测试套件（group_conversation / history_manager / message_builder / message_queue / service），运行方式 `python -m pytest tests -q`

### 功能更新（2026-06 之后累积）

- **群聊双层记忆**: 新增 `managers/group_conversation.py`（短时群对话记忆，`storage/conversations/`）与 `managers/group_memory.py`（长期记忆，`storage/memory/`）
- **消息队列增强**: 过期消息定期清理（`message_queue_manager.process_expired()`）
- **多模态与存储**: 优化图片处理，存储操作增加线程安全保护
- **决策层重构**: 合并 `reply_config` 职责到 `reply_decision`；意图识别改为纯规则分类；决策引擎 `process()` 统一入口（`EngineResult` 输出）
- **人设系统**: 支持多人设管理（`/人设列表`、`/切换人设`、`/创建人设`、`/绑定人设`、`/删除人设`）

### 文档同步

- README / docs 全部按当前代码结构更新（adapter 路径、存储目录、命令表、API 参考等）

---

## v3.6.0 (2026-06-19)

### Adapter 传输层 / 协议层拆分

本次版本对 `adapter/` 进行职责拆分，将原 `adapter/kernel/` 拆分为传输层（transport）和协议层（protocol），新增兼容导出层（core）。

#### 新增：传输层 `adapter/transport/`
- **`NapCatClient`** 精简为纯传输层客户端，只负责 WebSocket 连接管理、消息收发循环和通用 `call_api()` 调用
- 剥离所有 OneBot 业务方法（`send_group_message`、`get_group_list` 等），传输层不感知协议语义
- 导出接口：`IClient`、`IConnectionEventListener`、`MessageSegmentType`

#### 新增：协议层 `adapter/protocol/`
- **`BotAPI`** 重构为直接调用 `client.call_api(action, params)`，不再依赖 NapCatClient 的便捷方法
- **`MessageSegment`** 从 NapCatClient 中独立为 `message_segment.py`，专注消息段构建
- 事件模型（`events.py`）、表情映射（`emoji_map.py`）、事件总线（`event_bus.py`）、事件分发器（`event_dispatcher.py`）全部迁入
- 导出接口：`IBotAPI`、`IEventDispatcher`

#### 新增：兼容导出层 `adapter/core/`
- `adapter/core/__init__.py` 统一 re-export transport + protocol 的所有公开类
- `adapter/core/client.py`、`adapter/core/events.py`、`adapter/core/interfaces.py` 提供子模块级兼容路径
- 旧的 `from adapter.core.xxx import Yyy` 导入路径全部可用，无需修改业务代码

#### 删除：`adapter/kernel/`
- 原 `adapter/kernel/` 目录已完全移除，代码分别迁入 `transport/` 和 `protocol/`

#### 版本号更新
- `adapter/__version__` 从 `3.5.0` 升至 `3.6.0`

### 文件变更清单

**新增**
- `adapter/transport/__init__.py` — 传输层入口
- `adapter/transport/client.py` — NapCatClient（纯传输层）
- `adapter/transport/interfaces.py` — 传输层接口定义
- `adapter/protocol/__init__.py` — 协议层入口
- `adapter/protocol/api.py` — BotAPI（协议层封装）
- `adapter/protocol/events.py` — 事件数据模型
- `adapter/protocol/event_bus.py` — 事件总线
- `adapter/protocol/event_dispatcher.py` — 事件分发器
- `adapter/protocol/interfaces.py` — 协议层接口定义
- `adapter/protocol/message_segment.py` — 消息段构建器
- `adapter/protocol/emoji_map.py` — QQ 表情映射
- `adapter/core/__init__.py` — 兼容导出层
- `adapter/core/client.py` — client 兼容重导出
- `adapter/core/events.py` — events 兼容重导出
- `adapter/core/interfaces.py` — interfaces 兼容重导出

**删除**
- `adapter/kernel/` — 旧内核目录（已拆分至 transport + protocol）

---

## v3.5.0 (2026-05-30)

### 架构重构

本次版本对项目进行了大规模的架构简化和命名规范化，提升了代码可读性和维护性。

#### 适配层（adapter）提级
- **`adapter/` 从 `joha/` 提升到项目根目录**，作为独立包，与 `joha/` 核心包平级
- 内部导入使用 `adapter.config`、`adapter.core` 等，外部导入从 `joha.adapter` 改为 `adapter`
- **移除 `adapter/config/` 子目录**，配置文件直接放在 `adapter/` 下，结构更扁平
- **移除 `napcat_launcher.py`**（自动拉起 NapCat），改为纯连接检测，用户需手动启动 NapCat
- **移除 `config.example.yaml`**，只保留 `connection.yaml` 作为唯一配置文件
- **`bot_client.py` 重命名为 `message_client.py`**，职责更清晰

#### 连接器职责分离
- **`NapCatClient`**（连接层）：专注于 WebSocket 连接管理、消息收发、API 调用
- **`MessageClient`**（封装层）：专注于事件路由、装饰器注册、生命周期管理
- 消息回调通过 `set_message_callback()` 注入，消除两层之间的重复定义

#### 核心层（core）扁平化
- 移除 `core/handlers/`、`core/builders/`、`core/utils/` 三个子目录
- 所有模块直接放在 `core/` 下，import 路径从 `joha.core.handlers.xxx` 简化为 `joha.core.xxx`

#### 命名规范化
| 旧名称 | 新名称 | 说明 |
|--------|--------|------|
| `AIBot` | `ChatEngine` | AI 对话引擎，更符合现代命名 |
| `ai_bot` / `get_ai_bot()` | `chat_engine` / `get_chat_engine()` | 全局实例和获取函数 |
| `BotClient` | `MessageClient` | 消息客户端，突出消息处理职责 |

#### 配置层（config）扁平化
- 移除 `config/managers/` 和 `config/infrastructure/` 子目录
- 所有模块直接放在 `config/` 下：`config_manager.py`、`group_mode_config.py`、`logger.py`、`cache.py`
- 导入路径从 `joha.config.managers.xxx` 简化为 `joha.config.xxx`

#### 历史记录简化
- 移除 `response` 字段，历史记录只保留用户消息
- 删除 `find_similar_response()` 方法
- `add_message()` 不再需要传入回复内容

#### 数据目录外提
- `joha/storage/` 提升到项目根目录 `storage/`
- 新增 `joha/config/paths.py` 集中定义所有存储路径
- 运行时通过 `ensure_storage_dirs()` 自动创建目录，无需手动初始化

#### IPv4/IPv6 兼容
- WebSocket 连接自动将 `localhost` 替换为 `127.0.0.1`，避免 IPv6 解析问题
- 配置示例和默认值统一使用 `127.0.0.1`

### 热重载
- 新增 `core/hot_reload.py`，基于 watchdog 监控 `joha/` 目录文件变化，支持开发时模块热重载

### 配置优先级
`run.py` 支持在代码中自定义连接配置，优先级：
1. 代码中设置的 `WS_URL` / `ACCESS_TOKEN` / `BOT_UIN`
2. `adapter/connection.yaml` 中的配置
3. 内置默认值

### 文件变更清单

**新增**
- `joha/config/paths.py` — 集中路径定义
- `joha/core/hot_reload.py` — 热重载模块
- `joha/adapter/config.py` — 配置管理（从子目录提升）
- `joha/adapter/connection.yaml` — 连接配置（从子目录提升）
- `joha/adapter/message_client.py` — 消息客户端（从 bot_client.py 重命名）
- `joha/core/service.py` — 消息处理服务（从 handlers/ 提升）
- `joha/core/message_handler.py` — 消息处理器（从 handlers/ 提升）
- `joha/core/commands.py` — 命令处理器（从 handlers/ 提升）
- `joha/core/message_builder.py` — 消息构建器（从 builders/ 提升）
- `joha/core/message_queue.py` — 消息队列（从 builders/ 提升）
- `CHANGELOG.md` — 更新日志

**删除**
- `joha/adapter/config/` — 配置子目录
- `joha/adapter/config.example.yaml` — 示例配置
- `joha/adapter/napcat_launcher.py` — NapCat 自动拉起
- `joha/adapter/bot_client.py` — 旧客户端文件
- `joha/core/handlers/` — 处理器子目录
- `joha/core/builders/` — 构建器子目录
- `joha/core/utils/` — 工具子目录
- `joha/config/managers/` — 配置管理器子目录
- `joha/config/infrastructure/` — 基础设施子目录
- `joha/storage/` — 旧存储目录（已迁移至根目录）
- `hot_reload.py` — 根目录旧热重载文件

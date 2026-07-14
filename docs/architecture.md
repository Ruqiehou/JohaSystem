# Joha 系统架构设计文档

## 1. 架构总览

Joha 采用**分层 + 事件驱动**的架构设计，从上到下分为：

```
┌─────────────────────────────────────────────┐
│           消息平台层 (NapCatQQ)              │  ← OneBot 协议 / WebSocket
├─────────────────────────────────────────────┤
│           适配层 (adapter)                   │  ← MessageClient、事件分发
├─────────────────────────────────────────────┤
│           编排层 (joha.core)                 │  ← 消息处理、命令路由、队列合并
├─────────────────────────────────────────────┤
│           决策层 (joha.decision)             │  ← 回复概率计算、意图分类
├─────────────────────────────────────────────┤
│           AI 驱动层 (joha.ai)                │  ← LLM 调用、多 Provider 管理
├─────────────────────────────────────────────┤
│           管理层 (joha.managers)             │  ← 人设、风格、历史、画像
├─────────────────────────────────────────────┤
│           工具层 (joha.tools)                │  ← 搜索、网页抓取
├─────────────────────────────────────────────┤
│           基础设施 (joha.config)             │  ← 配置、日志、缓存、路径
└─────────────────────────────────────────────┘
```

---

## 2. 各层职责

### 2.1 适配层 (adapter)

独立包，负责与外部消息平台（NapCatQQ）建立和维护连接。

| 模块 | 文件 | 职责 |
|------|------|------|
| 消息客户端 | `message_client.py` | 封装层：事件注册、路由、生命周期管理 |
| 连接客户端 | `kernel/client.py` | 连接层：WebSocket 连接、消息收发、API 调用 |
| 事件模型 | `kernel/events.py` | 群消息、私聊、通知等事件数据模型 |
| API 封装 | `kernel/api.py` | OneBot 协议 API（发送消息等） |
| 配置管理 | `config.py` | 连接配置读取、日志系统 |
| 连接配置 | `connection.yaml` | WebSocket 地址、QQ 号等 |

**关键类：**
- `MessageClient`: 入口类，负责事件注册（装饰器模式）和生命周期管理
- `NapCatClient`: 底层 WebSocket 连接管理
- `GroupMessageEvent`: 群消息事件模型
- `BotAPI`: OneBot 协议 API 封装

### 2.2 编排层 (joha.core)

扁平结构，负责消息流入后的预处理、命令识别、业务编排。

| 模块 | 文件 | 职责 |
|------|------|------|
| 消息处理器 | `message_handler.py` | 消息接收、@/回复检测、队列合并调度 |
| 命令处理器 | `commands.py` | 斜杠命令解析与路由 |
| 业务服务 | `service.py` | 核心编排：学习 → 决策 → 生成的完整流水线 |
| 消息构建器 | `message_builder.py` | LLM 上下文组装 |
| 消息队列 | `message_queue.py` | 短时间多条消息合并，减少冗余回复 |
| 运行时上下文 | `runtime_context.py` | 全局运行时状态（bot_uin 等） |
| 人设监控 | `persona_monitor.py` | 人设参数监控与稳定性报告 |
| 工具注册 | `tool_registry.py` | 工具自动发现与注册 |
| 回复后处理 | `response_postprocessor.py` | 回复过滤、格式化 |
| 图片工具 | `image_utils.py` | 图片格式转换与处理 |
| 历史清洗 | `clean_history.py` | 历史记录清洗与压缩 |
| 热重载 | `hot_reload.py` | 开发时模块热重载 |

### 2.3 决策层 (joha.decision)

Joha 的核心亮点，负责判断机器人在什么场景下应该回复。

| 模块 | 文件 | 职责 |
|------|------|------|
| 决策引擎 | `decision_engine.py` | 总分架构的"总"，编排各子模块 |
| 回复决策 | `reply_decision.py` | Logit 累加 + Sigmoid 归一化计算回复概率（含配置懒加载） |
| 意图分类 | `intent_classifier.py` | 纯规则意图识别 |
| 命令分析 | `command_analyzer.py` | 自然语言命令解析（如"帮助"→`/帮助`） |
| 群组状态 | `group_state.py` | 群活跃度追踪、消息频率统计 |
| 冷却管理 | `cooldown.py` | 防刷屏，限制短时间连续回复 |

### 2.4 AI 驱动层 (joha.ai)

负责与各种 LLM API 交互，支持多 Provider 动态切换。

| 模块 | 文件 | 职责 |
|------|------|------|
| AI 客户端 | `clients.py` | OpenAI 协议兼容的 API 调用封装 |
| Provider 管理 | `providers.py` | 多 Provider 注册、切换、负载均衡 |
| 聊天引擎 | `bot.py` | ChatEngine，支持工具调用和 Provider 自动切换 |
| 回复生成器 | `generator.py` | 基于上下文的回复生成逻辑 |
| 分类器 | `classifier.py` | 文本分类（意图、情感等） |

### 2.5 管理层 (joha.managers)

负责各类数据的持久化与管理。

| 模块 | 文件 | 职责 |
|------|------|------|
| 人设管理 | `personas.py` | 多维度人设参数管理 |
| 风格学习 | `style_learner.py` | 自动学习群成员说话风格 |
| 历史记录 | `history_manager.py` | 聊天记录的增删查（只存用户消息） |
| 用户画像 | `user_profile.py` | 用户偏好和聊天习惯持久化 |
| 管理员系统 | `admin.py` | 权限分级、管理员增删查 |

### 2.6 工具层 (joha.tools)

模块化工具，每个工具独立封装。

| 模块 | 文件 | 职责 |
|------|------|------|
| 网络搜索 | `search/` | 可配置搜索 API |
| 网页抓取 | `webpage/` | 网页内容抓取与解析 |

### 2.7 基础设施 (joha.config)

扁平结构，所有模块直接在 `config/` 下。

| 模块 | 文件 | 职责 |
|------|------|------|
| 配置管理器 | `config_manager.py` | JSON 配置 + 环境变量覆盖 |
| 群组模式 | `group_mode_config.py` | 逐群的 active/passive 模式持久化 |
| 日志系统 | `logger.py` | 多级别日志、文件轮转、预定义记录器 |
| 缓存系统 | `cache.py` | LRU 缓存、TTL 过期、函数结果缓存装饰器 |
| 路径定义 | `paths.py` | 存储路径集中定义、运行时自动创建目录 |

---

## 3. 数据流向

```
NapCatQQ ──WebSocket──→ NapCatClient (连接层)
                        ↓ 消息回调
                        MessageClient (封装层)
                        ↓ 事件路由
                        MessageHandler
                        ↓
            MessageService.process_message()
                    │
        ┌───────────┼───────────┐
        ↓           ↓           ↓
   HistoryManager StyleLearner  DecisionEngine
        │           │           │
        └───────────┴───────────┘
                    ↓
            MessageBuilder
                    ↓
            ChatEngine / Generator
                    ↓
            BotAPI.send_group_message()
                    ↓
            NapCatQQ ──→ 群聊
```

---

## 4. 存储结构

数据存储在项目根目录 `storage/`，运行时自动创建：

```
storage/
├── group_states.json       # 群组状态持久化
├── group_modes.json        # 群组模式配置
├── user_profiles.json      # 用户画像数据
├── cooldown.json           # 冷却状态
├── history/                # 聊天历史记录（按用户分文件）
├── styles/                 # 风格学习数据
├── personas/               # 人设数据
└── johalog/                # 运行日志文件
```
